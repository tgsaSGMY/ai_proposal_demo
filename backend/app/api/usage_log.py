# 用途：提供使用量分析的 API 端點，包含趨勢分析、分組統計與篩選器選項。
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
    """解析查詢日期區間，若未提供則回退到最近 N 天。"""
    today = datetime.utcnow().date()
    default_start = today - timedelta(days=DEFAULT_LOOKBACK_DAYS - 1)
    resolved_start = start_date or default_start
    resolved_end = end_date or today

    if resolved_start > resolved_end:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    return resolved_start, resolved_end


def _normalize_value(value: Any) -> Any:
    """將日期時間物件正規化為 ISO 字串，便於 API 回傳。"""
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            return value.isoformat()
        return value.isoformat()
    return value


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """逐欄位正規化資料列中的值。"""
    return {key: _normalize_value(val) for key, val in row.items()}


async def _fetch_all(
    client: Any,
    table_name: str,
    filters: Optional[Dict[str, Any]] = None,
    group_by: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """從 Supabase 表取得資料（自動分頁，避免預設 1000 筆上限）。"""
    try:
        page_size = 1000
        offset = 0
        all_rows: List[Dict[str, Any]] = []

        while True:
            # 使用 range 分頁查詢，避免一次撈取過大量資料。
            query = client.from_(table_name).select("*").range(offset, offset + page_size - 1)

            if filters:
                for key, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        query = query.in_(key, value)
                    elif isinstance(value, dict):
                        if "gte" in value:
                            query = query.gte(key, value["gte"])
                        if "lt" in value:
                            query = query.lt(key, value["lt"])
                    else:
                        query = query.eq(key, value)

            response = await asyncio.to_thread(query.execute)
            batch = response.data or []
            if not batch:
                break

            all_rows.extend(batch)
            if len(batch) < page_size:
                break

            offset += page_size

        return [_normalize_row(row) for row in all_rows]
    except Exception as e:
        logger.error(f"Failed to fetch from {table_name}: {e}", exc_info=True)
        return []


async def _get_user_emails(user_ids: List[str], supabase_service: SupabaseService) -> Dict[str, str]:
    """批次查詢 user_id 對應 email，查不到時提供可讀 fallback。"""
    if not user_ids:
        return {}
    
    user_emails = {}
    try:
        response = await asyncio.to_thread(
            supabase_service.client.from_("users").select("id,email").in_("id", user_ids).execute
        )

        for user in (response.data or []):
            uid = user.get("id")
            email = user.get("email")
            if uid and email:
                user_emails[uid] = email
                
    except Exception as e:
        logger.warning(f"Failed to fetch emails from users table: {e}", exc_info=True)
    
    # 補齊無法查到的帳號，避免前端顯示空白。
    for uid in user_ids:
        if uid not in user_emails:
            user_emails[uid] = f"User {uid[:8]}..."
            
    return user_emails


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
    """取得使用量分析資料，回傳趨勢、分組統計與可用篩選條件。"""
    try:
        # 先解析查詢區間，後續統計都會以此範圍為準。
        range_start_date, range_end_date = _resolve_date_range(start_date, end_date)
        range_start_dt = datetime.combine(range_start_date, time.min)
        range_end_dt = datetime.combine(range_end_date + timedelta(days=1), time.min)

        # 建立基本篩選條件（含 created_at 區間）。
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

        # 讀取指定區間內的 usage logs。
        all_logs = await _fetch_all(supabase_service.client, "usage_logs", filters)
        
        # 全域摘要統計（區間成本、Token、呼叫次數、活躍專案數）。
        range_metrics = {
            "total_cost": sum(row.get("cost", 0) or 0 for row in all_logs),
            "total_input_tokens": sum(row.get("input_token", 0) or 0 for row in all_logs),
            "total_output_tokens": sum(row.get("output_token", 0) or 0 for row in all_logs),
            "active_projects": len(set(row.get("project_id") for row in all_logs if row.get("project_id"))),
            "total_calls": len(all_logs),
        }

        # 預留本月統計資料（目前僅保留查詢流程，回傳尚未單獨使用）。
        now = datetime.utcnow()
        mtd_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        mtd_filters = {"created_at": {"gte": mtd_start.isoformat(), "lt": now.isoformat()}}
        if user_id:
            mtd_filters["user_id"] = user_id

        # 依日期彙總趨勢資料。
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

        # 依使用者彙總，並將 user_id 轉成 email 顯示。
        user_dict = {}
        user_projects_dict = {}
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
            # 用 set 追蹤每位使用者觸及的唯一專案數。
            pid = row.get("project_id")
            if pid:
                user_projects_dict[uid].add(pid)
        
        # 補上每位使用者的專案數欄位。
        for uid in user_dict:
            user_dict[uid]["projectCount"] = len(user_projects_dict.get(uid, set()))
        
        # 批次查詢 email，避免逐筆查詢造成額外負擔。
        user_ids_list = [uid for uid in user_dict.keys() if uid != "UNASSIGNED"]
        user_emails = await _get_user_emails(user_ids_list, supabase_service)
        
        # 將 userId 對應成可讀 email。
        user_rows_with_email = []
        for uid, user_data in user_dict.items():
            email_display = user_emails.get(uid, uid) if uid != "UNASSIGNED" else "UNASSIGNED"
            user_data["email"] = email_display
            user_rows_with_email.append(user_data)
        
        user_rows = sorted(user_rows_with_email, key=lambda x: x["totalCost"], reverse=True)[:10]

        # 依專案彙總，並保留建立者 user_id 供 email 對應。
        project_dict = {}
        project_user_dict = {}
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
        
        # 查詢專案所屬使用者 email。
        project_user_ids = list(set(project_user_dict.values()))
        project_emails = await _get_user_emails(project_user_ids, supabase_service)
        
        # 將 email 回填到專案彙總資料。
        for pid, user_data in project_dict.items():
            uid = user_data["userId"]
            email_display = project_emails.get(uid, uid) if uid != "UNASSIGNED" else "UNASSIGNED"
            user_data["email"] = email_display
        
        project_rows_all = sorted(project_dict.values(), key=lambda x: x["totalCost"], reverse=True)
        project_rows = project_rows_all[:10]

        # 依 action 彙總成本與呼叫數。
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

        # 依模型彙總成本、Token 與平均成本。
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

        # 取得前端篩選器所需候選值（user/project/model/action）。
        all_logs_no_filter = await _fetch_all(supabase_service.client, "usage_logs", {})
        
        option_users_ids = list(set(row.get("user_id") for row in all_logs_no_filter if row.get("user_id")))[:120]
        option_projects = list(set(row.get("project_id") for row in all_logs_no_filter if row.get("project_id")))[:120]
        option_models = list(set(row.get("model_id") for row in all_logs_no_filter if row.get("model_id")))[:120]
        option_actions = list(set(row.get("action") for row in all_logs_no_filter if row.get("action")))[:120]

        # 篩選器中的使用者同樣轉換成 email 顯示。
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
                "users": option_users,
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

