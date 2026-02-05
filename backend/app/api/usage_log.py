from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.api.dependencies import get_supabase_service, verify_internal_user
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usage-log", tags=["Usage Analytics"])

DEFAULT_LOOKBACK_DAYS = 30


def _resolve_date_range(
    start_date: Optional[date],
    end_date: Optional[date],
) -> tuple[date, date]:
    today = datetime.utcnow().date()
    default_start = today - timedelta(days=DEFAULT_LOOKBACK_DAYS - 1)
    resolved_start = start_date or default_start
    resolved_end = end_date or today

    if resolved_start > resolved_end:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    return resolved_start, resolved_end


def _normalize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            return value.isoformat()
        return value.isoformat()
    return value


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _normalize_value(val) for key, val in row.items()}


def _parse_iso_datetime(iso_string: str) -> Optional[datetime]:
    """Parse ISO datetime string and strip timezone info to make it naive UTC"""
    if not iso_string:
        return None
    try:
        dt = datetime.fromisoformat(iso_string)
        # Strip timezone info to make it naive (UTC)
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None


async def _fetch_all(
    client: Any,
    table_name: str,
    filters: Optional[Dict[str, Any]] = None,
    group_by: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """从 Supabase 表中获取数据"""
    try:
        query = client.from_(table_name).select("*")
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    query = query.in_(key, value)
                elif isinstance(value, dict):
                    # 处理范围查询
                    if "gte" in value:
                        query = query.gte(key, value["gte"])
                    if "lt" in value:
                        query = query.lt(key, value["lt"])
                else:
                    query = query.eq(key, value)
        
        response = await asyncio.to_thread(query.execute)
        return [_normalize_row(row) for row in (response.data or [])]
    except Exception as e:
        logger.error(f"Failed to fetch from {table_name}: {e}", exc_info=True)
        return []


async def _get_user_emails(user_ids: List[str], supabase_service: SupabaseService) -> Dict[str, str]:
    if not user_ids:
        return {}
    
    user_emails = {}
    try:
        # 使用 rpc 呼叫剛才建立的 SQL 函數
        response = await asyncio.to_thread(
            supabase_service.client.rpc("get_user_emails", {"user_ids": user_ids}).execute
        )
        
        # response.data 會長這樣: [{'id': '...', 'email': '...'}, ...]
        for user in (response.data or []):
            uid = user.get("id")
            email = user.get("email")
            if uid and email:
                user_emails[uid] = email
                
    except Exception as e:
        logger.warning(f"Failed to fetch emails via RPC: {e}", exc_info=True)
    
    # Fallback (保持你原本的邏輯)
    for uid in user_ids:
        if uid not in user_emails:
            user_emails[uid] = f"User {uid[:8]}..." # 可以美化一下 fallback
            
    return user_emails

def _aggregate_by_field(
    rows: List[Dict[str, Any]],
    group_field: str,
    agg_fields: Dict[str, str],
    order_by: tuple[str, bool] = ("total_cost", False),
) -> List[Dict[str, Any]]:
    """按字段分组并聚合数据"""
    groups = {}
    
    for row in rows:
        key = row.get(group_field, "UNASSIGNED")
        if key not in groups:
            groups[key] = {group_field: key}
            for agg_field, agg_type in agg_fields.items():
                if agg_type == "sum":
                    groups[key][agg_field] = 0
                elif agg_type == "count":
                    groups[key][agg_field] = 0
        
        for agg_field, agg_type in agg_fields.items():
            if agg_type == "sum":
                groups[key][agg_field] += row.get(agg_field, 0) or 0
            elif agg_type == "count":
                groups[key][agg_field] += 1
    
    result = list(groups.values())
    if order_by:
        result.sort(key=lambda x: x.get(order_by[0], 0), reverse=order_by[1])
    
    return result


@router.get("/analytics")
async def get_usage_analytics(
    start_date: Optional[date] = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Inclusive end date (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    project_id: Optional[str] = Query(None, description="Filter by project_id"),
    model_id: Optional[str] = Query(None, description="Filter by model_id"),
    action: Optional[str] = Query(None, description="Filter by action"),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    """获取使用量分析数据"""
    try:
        range_start_date, range_end_date = _resolve_date_range(start_date, end_date)
        range_start_dt = datetime.combine(range_start_date, time.min)
        range_end_dt = datetime.combine(range_end_date + timedelta(days=1), time.min)

        # 构建过滤条件
        filters = {
            "created_at": {
                "gte": range_start_dt.isoformat(),
                "lt": range_end_dt.isoformat()
            }
        }
        
        if user_id:
            filters["user_id"] = user_id
        if project_id:
            filters["project_id"] = project_id
        if model_id:
            filters["model_id"] = model_id
        if action:
            filters["action"] = action

        # 获取日期范围内的所有数据
        all_logs = await _fetch_all(supabase_service.client, "usage_logs", filters)
        
        # 聚合范围数据
        range_metrics = {
            "total_cost": sum(row.get("cost", 0) or 0 for row in all_logs),
            "total_input_tokens": sum(row.get("input_token", 0) or 0 for row in all_logs),
            "total_output_tokens": sum(row.get("output_token", 0) or 0 for row in all_logs),
            "active_projects": len(set(row.get("project_id") for row in all_logs if row.get("project_id"))),
            "total_calls": len(all_logs),
        }

        # 获取今月数据
        now = datetime.utcnow()
        mtd_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        mtd_filters = {"created_at": {"gte": mtd_start.isoformat(), "lt": now.isoformat()}}
        if user_id:
            mtd_filters["user_id"] = user_id
        mtd_logs = await _fetch_all(supabase_service.client, "usage_logs", mtd_filters)
        global_metrics = {}

        # 按日期聚合趋势
        trend_dict = {}
        for row in all_logs:
            date_str = row.get("created_at", "")[:10] if row.get("created_at") else ""
            if not date_str:
                continue
            if date_str not in trend_dict:
                trend_dict[date_str] = {
                    "date": date_str,
                    "cost": 0.0,
                    "inputTokens": 0,
                    "outputTokens": 0,
                }
            trend_dict[date_str]["cost"] += row.get("cost", 0) or 0
            trend_dict[date_str]["inputTokens"] += row.get("input_token", 0) or 0
            trend_dict[date_str]["outputTokens"] += row.get("output_token", 0) or 0
        trend_rows = sorted(trend_dict.values(), key=lambda x: x["date"])

        # 按用户聚合，并用邮箱替换显示
        user_dict = {}
        user_projects_dict = {}  # Track unique projects per user
        for row in all_logs:
            uid = row.get("user_id") or "UNASSIGNED"
            if uid not in user_dict:
                user_dict[uid] = {
                    "userId": uid,
                    "totalCost": 0.0,
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "callCount": 0,
                }
                user_projects_dict[uid] = set()
            user_dict[uid]["totalCost"] += row.get("cost", 0) or 0
            user_dict[uid]["inputTokens"] += row.get("input_token", 0) or 0
            user_dict[uid]["outputTokens"] += row.get("output_token", 0) or 0
            user_dict[uid]["callCount"] += 1
            # Track unique projects
            pid = row.get("project_id")
            if pid:
                user_projects_dict[uid].add(pid)
        
        # 添加项目计数
        for uid in user_dict:
            user_dict[uid]["projectCount"] = len(user_projects_dict.get(uid, set()))
        
        # 批量获取用户邮箱
        user_ids_list = [uid for uid in user_dict.keys() if uid != "UNASSIGNED"]
        user_emails = await _get_user_emails(user_ids_list, supabase_service)
        
        # 用邮箱替换用户ID显示
        user_rows_with_email = []
        for uid, user_data in user_dict.items():
            email_display = user_emails.get(uid, uid) if uid != "UNASSIGNED" else "UNASSIGNED"
            user_data["email"] = email_display
            user_rows_with_email.append(user_data)
        
        user_rows = sorted(user_rows_with_email, key=lambda x: x["totalCost"], reverse=True)[:10]

        # 按项目聚合，并追踪用户
        project_dict = {}
        project_user_dict = {}  # Track user for each project
        for row in all_logs:
            pid = row.get("project_id") or "UNLINKED"
            uid = row.get("user_id") or "UNASSIGNED"
            if pid not in project_dict:
                project_dict[pid] = {
                    "projectId": pid,
                    "userId": uid,
                    "totalCost": 0.0,
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "callCount": 0,
                }
                project_user_dict[pid] = uid
            project_dict[pid]["totalCost"] += row.get("cost", 0) or 0
            project_dict[pid]["inputTokens"] += row.get("input_token", 0) or 0
            project_dict[pid]["outputTokens"] += row.get("output_token", 0) or 0
            project_dict[pid]["callCount"] += 1
        
        # 获取项目对应用户的邮箱
        project_user_ids = list(set(project_user_dict.values()))
        project_emails = await _get_user_emails(project_user_ids, supabase_service)
        
        # 添加用户邮箱到项目数据
        for pid, user_data in project_dict.items():
            uid = user_data["userId"]
            email_display = project_emails.get(uid, uid) if uid != "UNASSIGNED" else "UNASSIGNED"
            user_data["email"] = email_display
        
        project_rows_all = sorted(project_dict.values(), key=lambda x: x["totalCost"], reverse=True)
        project_rows = project_rows_all[:10]

        # 按行为聚合
        action_dict = {}
        for row in all_logs:
            act = row.get("action") or "未標註"
            if act not in action_dict:
                action_dict[act] = {
                    "action": act,
                    "totalCost": 0.0,
                    "callCount": 0,
                }
            action_dict[act]["totalCost"] += row.get("cost", 0) or 0
            action_dict[act]["callCount"] += 1
        action_rows = sorted(action_dict.values(), key=lambda x: x["totalCost"], reverse=True)

        # 按模型聚合
        model_dict = {}
        for row in all_logs:
            mid = row.get("model_id") or "未知模型"
            if mid not in model_dict:
                model_dict[mid] = {
                    "modelId": mid,
                    "totalCost": 0.0,
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "callCount": 0,
                    "avgCost": 0.0,
                }
            model_dict[mid]["totalCost"] += row.get("cost", 0) or 0
            model_dict[mid]["inputTokens"] += row.get("input_token", 0) or 0
            model_dict[mid]["outputTokens"] += row.get("output_token", 0) or 0
            model_dict[mid]["callCount"] += 1
        
        for mid in model_dict:
            if model_dict[mid]["callCount"] > 0:
                model_dict[mid]["avgCost"] = model_dict[mid]["totalCost"] / model_dict[mid]["callCount"]
        model_rows = sorted(model_dict.values(), key=lambda x: x["totalCost"], reverse=True)

        # 获取过滤选项
        all_logs_no_filter = await _fetch_all(supabase_service.client, "usage_logs", {})
        
        option_users_ids = list(set(row.get("user_id") for row in all_logs_no_filter if row.get("user_id")))[:120]
        option_projects = list(set(row.get("project_id") for row in all_logs_no_filter if row.get("project_id")))[:120]
        option_models = list(set(row.get("model_id") for row in all_logs_no_filter if row.get("model_id")))[:120]
        option_actions = list(set(row.get("action") for row in all_logs_no_filter if row.get("action")))[:120]

        # 为过滤选项中的用户获取邮箱
        option_users_emails = await _get_user_emails(option_users_ids, supabase_service)
        option_users = [
            {"id": uid, "email": option_users_emails.get(uid, uid), "lastUsed": None}
            for uid in option_users_ids
        ]

        response = {
            "filters": {
                "userId": user_id,
                "projectId": project_id,
                "modelId": model_id,
                "action": action,
                "rangeStart": range_start_date.isoformat(),
                "rangeEnd": range_end_date.isoformat(),
            },
            "globalOverview": {
                "totalCostMTD": float(range_metrics.get("total_cost", 0.0)),
                "rangeCost": float(range_metrics.get("total_cost", 0.0)),
                "totalInputTokens": int(range_metrics.get("total_input_tokens", 0)),
                "totalOutputTokens": int(range_metrics.get("total_output_tokens", 0)),
                "activeProjects": int(range_metrics.get("active_projects", 0)),
                "totalCalls": int(range_metrics.get("total_calls", 0)),
            },
            "trend": trend_rows,
            "byUser": {"rows": user_rows},
            "byProject": {"rows": project_rows_all},
            "byAction": action_rows,
            "byModel": model_rows,
            "availableFilters": {
                "users": [{"id": uid, "lastUsed": None} for uid in option_users],
                "projects": [{"id": pid, "lastUsed": None} for pid in option_projects],
                "models": [{"id": mid, "lastUsed": None} for mid in option_models],
                "actions": [{"id": act, "lastUsed": None} for act in option_actions],
            },
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
        }

        return response

    except Exception as e:
        logger.error(f"Failed to fetch usage analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

