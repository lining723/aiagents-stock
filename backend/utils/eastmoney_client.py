import json
import os
import shutil
import subprocess
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlencode

import requests

from utils.logger import get_logger


logger = get_logger(__name__)

try:
    from curl_cffi import requests as curl_cffi_requests
except Exception:  # pragma: no cover - optional transport fallback
    curl_cffi_requests = None


class EastmoneyClient:
    """使用更接近浏览器的请求方式访问东方财富接口。"""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Origin": "https://quote.eastmoney.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def __init__(self):
        self._curl_path = shutil.which("curl")
        self._proxy_base_url = os.getenv("EASTMONEY_PROXY_BASE_URL", "").rstrip("/")
        self._impersonate = os.getenv("EASTMONEY_IMPERSONATE", "chrome124")

    def get_json(
        self,
        urls: Iterable[str],
        params: Dict[str, Any],
        referer: str,
        timeout: int = 15,
    ) -> Optional[Dict[str, Any]]:
        """按候选 URL 顺序请求 JSON，优先使用 curl。"""
        headers = dict(self.DEFAULT_HEADERS)
        headers["Referer"] = referer

        for url in urls:
            if self._proxy_base_url:
                try:
                    data = self._get_json_via_proxy(url, params, headers, timeout)
                    if data is not None:
                        return data
                except Exception as exc:
                    logger.warning(f"Eastmoney 宿主机代理请求失败: url={url} error={type(exc).__name__}: {exc}")

            try:
                data = self._get_json_with_curl_cffi(url, params, headers, timeout)
                if data is not None:
                    return data
            except Exception as exc:
                logger.warning(f"Eastmoney curl_cffi 请求失败: url={url} error={type(exc).__name__}: {exc}")

            try:
                data = self._get_json_with_curl(url, params, headers, timeout)
                if data is not None:
                    return data
            except Exception as exc:
                logger.warning(f"Eastmoney curl 请求失败: url={url} error={type(exc).__name__}: {exc}")

            try:
                data = self._get_json_with_requests(url, params, headers, timeout)
                if data is not None:
                    return data
            except Exception as exc:
                logger.warning(f"Eastmoney requests 请求失败: url={url} error={type(exc).__name__}: {exc}")

        return None

    def _get_json_via_proxy(
        self,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
    ) -> Optional[Dict[str, Any]]:
        proxy_url = f"{self._proxy_base_url}/fetch"
        response = requests.post(
            proxy_url,
            json={
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            },
            timeout=timeout + 5,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(payload.get("error", "proxy request failed"))
        return payload.get("data")

    def _get_json_with_curl(
        self,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
    ) -> Optional[Dict[str, Any]]:
        if not self._curl_path:
            return None

        query = urlencode(params)
        full_url = f"{url}?{query}"

        cmd = [
            self._curl_path,
            "--silent",
            "--show-error",
            "--location",
            "--compressed",
            "--max-time",
            str(timeout),
        ]
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
        cmd.append(full_url)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"curl exit code {result.returncode}")

        payload = result.stdout.strip()
        if not payload:
            return None
        return json.loads(payload)

    def _get_json_with_curl_cffi(
        self,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
    ) -> Optional[Dict[str, Any]]:
        if curl_cffi_requests is None:
            return None

        response = curl_cffi_requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            impersonate=self._impersonate,
        )
        response.raise_for_status()
        payload = response.text.strip()
        if not payload:
            return None
        return json.loads(payload)

    def _get_json_with_requests(
        self,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        timeout: int,
    ) -> Optional[Dict[str, Any]]:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
