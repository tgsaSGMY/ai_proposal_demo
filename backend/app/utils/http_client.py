# 用途：共用 HTTP 客戶端，負責對母平台 (TGSA Portal) 發送請求。
# 統一處理 JSON 解析、逾時 (timeout) 與 HTTP 錯誤擷取。

import json
from typing import Any, Dict, Tuple, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def post_form(url: str, payload: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
    """以 x-www-form-urlencoded 格式送出 POST 請求，回傳解析後的 JSON。"""
    body = urlencode(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)

def post_json(
    url: str,
    body: Dict[str, Any],
    bearer_token: str,
    timeout: int = 15,
) -> Tuple[int, Dict[str, Any]]:
    """以 application/json 格式送出 POST 請求 (需 Bearer Token)，回傳 (HTTP_STATUS, JSON)。"""
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    req = Request(url, data=data, headers=headers, method="POST")
    return _execute_json_request(req, timeout)

def get_json_with_bearer(
    url: str, 
    bearer_token: str, 
    timeout: int = 15
) -> Tuple[int, Dict[str, Any]]:
    """以 GET 請求取得 JSON (需 Bearer Token)，回傳 (HTTP_STATUS, JSON)。"""
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
    }
    req = Request(url, headers=headers, method="GET")
    return _execute_json_request(req, timeout)

def _execute_json_request(req: Request, timeout: int) -> Tuple[int, Dict[str, Any]]:
    """內部共用函數：執行 Request 並解析錯誤與 JSON。"""
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(raw)
    except HTTPError as exc:
        raw = ""
        try:
            raw = exc.read().decode("utf-8")
        except Exception:
            pass
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {"error": raw}
        return exc.code, payload
    except URLError as exc:
        return -1, {"error": f"url_error: {exc.reason}"}
    except Exception as exc:
        return -1, {"error": f"unexpected: {exc}"}
