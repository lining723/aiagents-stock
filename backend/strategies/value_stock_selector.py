#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低估值选股模块
使用akshare/pywencai获取低估值优质股票
"""

import pandas as pd
import akshare as ak
import pywencai
from datetime import datetime, timedelta
import os
from typing import Tuple, Optional
import time
import requests
from utils.logger import get_logger
from utils.eastmoney_client import EastmoneyClient


logger = get_logger(__name__)


class ValueStockSelector:
    """低估值选股类"""

    def __init__(self):
        self.raw_data = None
        self.selected_stocks = None
        self.eastmoney_client = EastmoneyClient()

    def get_value_stocks(self, pe_max: float = 20, pb_max: float = 1.5, top_n: int = 10) -> Tuple[bool, Optional[pd.DataFrame], str]:
        """
        获取低估值优质股票

        选股策略：
        - 市盈率 ≤ pe_max
        - 市净率 ≤ pb_max
        - 股息率 ≥ 1%
        - 资产负债率 ≤ 30%
        - 非ST
        - 非科创板
        - 非创业板
        - 按流通市值由小到大排名

        Args:
            pe_max: 市盈率最大值
            pb_max: 市净率最大值
            top_n: 返回前N只股票

        Returns:
            (success, dataframe, message)
        """
        try:
            print(f"\n{'='*60}")
            print(f"💎 低估值选股 - 数据获取中")
            print(f"{'='*60}")
            print(f"策略: PE≤{pe_max} + PB≤{pb_max} + 股息率≥1% + 资产负债率≤30%")
            print(f"排除: ST、科创板、创业板")
            print(f"排序: 按流通市值由小到大")
            print(f"目标: 筛选前{top_n}只股票")

            # 优先使用 akshare 获取数据（更稳定）
            df_result = self._get_value_stocks_akshare(pe_max, pb_max, top_n)

            if df_result is None or df_result.empty:
                print(f"\n东方财富/akshare获取失败，尝试Tushare...")
                df_result = self._get_value_stocks_tencent(pe_max, pb_max)

            if df_result is None or df_result.empty:
                print(f"\n腾讯行情兜底失败，尝试Tushare...")
                df_result = self._get_value_stocks_tushare(pe_max, pb_max)

            if df_result is None or df_result.empty:
                # 尝试使用 pywencai 作为备用
                print(f"\nTushare获取失败，尝试pywencai...")
                df_result = self._get_value_stocks_wencai(pe_max, pb_max, top_n)

            if df_result is None or df_result.empty:
                return False, None, "未获取到符合条件的股票数据"

            print(f"✅ 成功获取 {len(df_result)} 只股票")

            # 保存原始数据
            self.raw_data = df_result

            # 取前N只
            if len(df_result) > top_n:
                selected = df_result.head(top_n)
                print(f"\n从 {len(df_result)} 只股票中选出前 {top_n} 只")
            else:
                selected = df_result
                print(f"\n共 {len(df_result)} 只符合条件的股票")

            self.selected_stocks = selected

            print(f"{'='*60}\n")

            return True, selected, f"成功筛选出{len(selected)}只低估值优质股票"

        except Exception as e:
            error_msg = f"获取数据失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, None, error_msg

    def _get_value_stocks_akshare(self, pe_max: float, pb_max: float, top_n: int) -> Optional[pd.DataFrame]:
        """使用 akshare 获取低估值股票"""
        try:
            print(f"\n正在使用东方财富接口获取A股行情数据...")

            df = self._get_value_stocks_eastmoney(pe_max, pb_max)
            if df is not None and not df.empty:
                print(f"东方财富筛选后剩余 {len(df)} 只股票")
                return df

            print(f"\n正在使用 akshare 获取A股行情数据...")

            # 获取A股实时行情
            df = ak.stock_zh_a_spot_em()

            if df is None or df.empty:
                print("akshare返回数据为空")
                return None

            print(f"获取到 {len(df)} 只股票的实时行情")

            # 筛选条件
            # 1. 排除ST股票
            df = df[~df['名称'].str.contains('ST', case=False, na=False)]

            # 2. 排除科创板（688开头）和创业板（300开头）
            df = df[~df['代码'].str.startswith('688')]
            df = df[~df['代码'].str.startswith('300')]

            # 3. 市盈率筛选
            df = df[df['市盈率-动态'] > 0]  # 排除亏损股
            df = df[df['市盈率-动态'] <= pe_max]

            # 4. 市净率筛选
            df = df[df['市净率'] > 0]
            df = df[df['市净率'] <= pb_max]

            # 按流通市值排序（升序）
            df = df.sort_values(by='流通市值', ascending=True)

            # 重命名列以匹配原有格式
            df = df.rename(columns={
                '代码': '股票代码',
                '名称': '股票简称',
                '市盈率-动态': '市盈率',
                '市净率': '市净率',
                '流通市值': '流通市值',
                '总市值': '总市值',
                '最新价': '最新价',
                '涨跌幅': '涨跌幅',
            })

            print(f"akshare筛选后剩余 {len(df)} 只股票")
            return df

        except Exception as e:
            print(f"akshare获取失败: {e}")
            return None

    def _get_value_stocks_eastmoney(self, pe_max: float, pb_max: float) -> Optional[pd.DataFrame]:
        urls = [
            "https://82.push2.eastmoney.com/api/qt/clist/get",
            "https://push2.eastmoney.com/api/qt/clist/get",
        ]
        params = {
            "pn": "1",
            "pz": "5000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f12",
            "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
            "fields": (
                "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,"
                "f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152"
            ),
        }

        data_json = self.eastmoney_client.get_json(
            urls=urls,
            params=params,
            referer="https://quote.eastmoney.com/",
        )
        if not data_json or not data_json.get("data", {}).get("diff"):
            return None

        df = pd.DataFrame(data_json["data"]["diff"])
        rename_map = {
            "f12": "股票代码",
            "f14": "股票简称",
            "f2": "最新价",
            "f3": "涨跌幅",
            "f9": "市盈率",
            "f23": "市净率",
            "f20": "总市值",
            "f21": "流通市值",
        }
        df = df.rename(columns=rename_map)
        required_cols = ["股票代码", "股票简称", "市盈率", "市净率", "流通市值"]
        if any(col not in df.columns for col in required_cols):
            return None

        df["股票代码"] = df["股票代码"].astype(str).str.zfill(6)
        df["股票简称"] = df["股票简称"].astype(str)
        for col in ["市盈率", "市净率", "流通市值", "总市值", "最新价", "涨跌幅"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[~df["股票简称"].str.contains("ST", case=False, na=False)]
        df = df[~df["股票代码"].str.startswith("688")]
        df = df[~df["股票代码"].str.startswith("300")]
        df = df[df["市盈率"] > 0]
        df = df[df["市盈率"] <= pe_max]
        df = df[df["市净率"] > 0]
        df = df[df["市净率"] <= pb_max]
        df = df.sort_values(by="流通市值", ascending=True)
        return df

    def _get_value_stocks_tencent(self, pe_max: float, pb_max: float) -> Optional[pd.DataFrame]:
        """使用腾讯行情批量接口兜底获取 PE/PB/市值。"""
        try:
            basic_df = self._get_tencent_stock_universe()
            if basic_df is None or basic_df.empty:
                logger.warning("腾讯兜底股票代码列表为空")
                return None

            basic_df["symbol"] = basic_df["symbol"].astype(str).str.zfill(6)
            basic_df["name"] = basic_df["name"].astype(str)
            if "exchange" not in basic_df.columns:
                basic_df["exchange"] = ""
            basic_df["exchange"] = basic_df["exchange"].astype(str).str.lower()
            basic_df = basic_df[~basic_df["name"].str.contains("ST", case=False, na=False)]
            basic_df = basic_df[~basic_df["symbol"].str.startswith("688")]
            basic_df = basic_df[~basic_df["symbol"].str.startswith("300")]

            quote_symbols = []
            for _, row in basic_df.iterrows():
                quote_symbol = self._to_tencent_symbol(
                    str(row.get("ts_code", "")),
                    row["symbol"],
                    str(row.get("exchange", "")),
                )
                if quote_symbol:
                    quote_symbols.append(quote_symbol)

            if not quote_symbols:
                return None

            records = []
            headers = {
                "User-Agent": EastmoneyClient.DEFAULT_HEADERS["User-Agent"],
                "Referer": "https://gu.qq.com/",
                "Accept": "*/*",
            }
            batch_size = 200
            for start in range(0, len(quote_symbols), batch_size):
                batch = quote_symbols[start:start + batch_size]
                url = "https://qt.gtimg.cn/q=" + ",".join(batch)
                try:
                    response = requests.get(url, headers=headers, timeout=12)
                    response.raise_for_status()
                    text = response.content.decode("gbk", errors="ignore")
                    records.extend(self._parse_tencent_quotes(text))
                except Exception as exc:
                    logger.warning(f"腾讯行情批量请求失败: start={start} size={len(batch)} error={type(exc).__name__}: {exc}")

            if not records:
                return None

            df = pd.DataFrame(records)
            df = df[~df["股票简称"].str.contains("ST", case=False, na=False)]
            df = df[~df["股票代码"].str.startswith("688")]
            df = df[~df["股票代码"].str.startswith("300")]
            df = df[df["市盈率"] > 0]
            df = df[df["市盈率"] <= pe_max]
            df = df[df["市净率"] > 0]
            df = df[df["市净率"] <= pb_max]
            df = df.sort_values(by="流通市值", ascending=True)
            print(f"腾讯行情筛选后剩余 {len(df)} 只股票")
            return df

        except Exception as e:
            logger.warning(f"腾讯行情低估值选股兜底失败: {type(e).__name__}: {e}")
            return None

    def _get_tencent_stock_universe(self) -> Optional[pd.DataFrame]:
        tdx_base_url = os.getenv("TDX_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
        try:
            response = requests.get(f"{tdx_base_url}/api/codes", timeout=10)
            response.raise_for_status()
            payload = response.json()
            codes = payload.get("data", {}).get("codes", [])
            if codes:
                df = pd.DataFrame(codes)
                df = df.rename(columns={"code": "symbol"})
                return df[["symbol", "name", "exchange"]]
        except Exception as exc:
            logger.warning(f"从 tdx-api 获取股票代码列表失败: {type(exc).__name__}: {exc}")

        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            return None

        try:
            import tushare as ts

            pro = ts.pro_api(token)
            df = pro.stock_basic(
                exchange="",
                list_status="L",
                fields="ts_code,symbol,name,market,list_date",
            )
            if df is None or df.empty:
                return None
            df["exchange"] = df["ts_code"].astype(str).str.split(".").str[-1].str.lower()
            return df[["ts_code", "symbol", "name", "exchange"]]
        except Exception as exc:
            logger.warning(f"从 Tushare 获取股票代码列表失败: {type(exc).__name__}: {exc}")
            return None

    def _to_tencent_symbol(self, ts_code: str, symbol: str, exchange: str = "") -> Optional[str]:
        exchange = exchange.lower()
        if exchange in {"sh", "sz", "bj"}:
            return f"{exchange}{symbol}"

        suffix = ts_code.split(".")[-1].upper() if "." in ts_code else ""
        if suffix == "SH" or symbol.startswith("6"):
            return f"sh{symbol}"
        if suffix == "SZ" or symbol.startswith(("0", "2", "3")):
            return f"sz{symbol}"
        if suffix == "BJ" or symbol.startswith(("4", "8", "9")):
            return f"bj{symbol}"
        return None

    def _parse_tencent_quotes(self, text: str):
        def to_float(value, default=None):
            try:
                if value in (None, "", "--"):
                    return default
                return float(value)
            except (TypeError, ValueError):
                return default

        records = []
        for line in text.split(";"):
            if '="' not in line:
                continue
            raw = line.split('="', 1)[1].rstrip('"')
            parts = raw.split("~")
            if len(parts) < 47 or not parts[2]:
                continue

            pe = to_float(parts[39])
            pb = to_float(parts[46])
            total_mv_yi = to_float(parts[44])
            circ_mv_yi = to_float(parts[45])
            if pe is None or pb is None or total_mv_yi is None or circ_mv_yi is None:
                continue

            records.append({
                "股票代码": parts[2].zfill(6),
                "股票简称": parts[1],
                "最新价": to_float(parts[3], 0),
                "涨跌幅": to_float(parts[32], 0),
                "市盈率": pe,
                "市净率": pb,
                "总市值": total_mv_yi * 100000000,
                "流通市值": circ_mv_yi * 100000000,
                "数据来源": "tencent",
            })
        return records

    def _get_value_stocks_tushare(self, pe_max: float, pb_max: float) -> Optional[pd.DataFrame]:
        """使用 Tushare daily_basic 作为东方财富不可用时的兜底数据源。"""
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            logger.warning("Tushare Token 未配置，跳过低估值选股兜底")
            return None

        try:
            import tushare as ts

            pro = ts.pro_api(token)
            daily_fields = "ts_code,trade_date,close,pe,pe_ttm,pb,total_mv,circ_mv"
            daily_df = None
            used_trade_date = None

            for offset in range(20):
                trade_date = (datetime.now() - timedelta(days=offset)).strftime("%Y%m%d")
                candidate = pro.daily_basic(trade_date=trade_date, fields=daily_fields)
                if candidate is not None and not candidate.empty:
                    daily_df = candidate
                    used_trade_date = trade_date
                    break

            if daily_df is None or daily_df.empty:
                logger.warning("Tushare daily_basic 未获取到最近交易日数据")
                return None

            basic_df = pro.stock_basic(
                exchange="",
                list_status="L",
                fields="ts_code,symbol,name,market,list_date",
            )
            if basic_df is None or basic_df.empty:
                logger.warning("Tushare stock_basic 返回为空")
                return None

            df = daily_df.merge(basic_df, on="ts_code", how="left")
            for col in ["close", "pe", "pe_ttm", "pb", "total_mv", "circ_mv"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df["股票代码"] = df["symbol"].astype(str).str.zfill(6)
            df["股票简称"] = df["name"].astype(str)
            df["最新价"] = df["close"]
            df["市盈率"] = df["pe_ttm"].where(df["pe_ttm"].gt(0), df["pe"])
            df["市净率"] = df["pb"]
            df["总市值"] = df["total_mv"] * 10000
            df["流通市值"] = df["circ_mv"] * 10000
            df["涨跌幅"] = None
            df["数据来源"] = f"tushare:{used_trade_date}"

            df = df[~df["股票简称"].str.contains("ST", case=False, na=False)]
            df = df[~df["股票代码"].str.startswith("688")]
            df = df[~df["股票代码"].str.startswith("300")]
            df = df[df["市盈率"] > 0]
            df = df[df["市盈率"] <= pe_max]
            df = df[df["市净率"] > 0]
            df = df[df["市净率"] <= pb_max]
            df = df.sort_values(by="流通市值", ascending=True)

            columns = ["股票代码", "股票简称", "最新价", "涨跌幅", "市盈率", "市净率", "总市值", "流通市值", "数据来源"]
            df = df[[col for col in columns if col in df.columns]]
            print(f"Tushare({used_trade_date})筛选后剩余 {len(df)} 只股票")
            return df

        except Exception as e:
            logger.warning(f"Tushare低估值选股兜底失败: {type(e).__name__}: {e}")
            return None

    def _get_value_stocks_wencai(self, pe_max: float, pb_max: float, top_n: int) -> Optional[pd.DataFrame]:
        """使用 pywencai 获取低估值股票（备用）"""
        try:
            # 构建问财查询语句
            query = (
                f"市盈率小于等于{pe_max}，"
                f"市净率小于等于{pb_max}，"
                "股息率大于等于1%，"
                "资产负债率小于等于30%，"
                "非st，"
                "非科创板，"
                "非创业板，"
                "按流通市值由小到大排名"
            )

            print(f"\n查询语句: {query}")
            print(f"正在调用问财接口...")

            result = self._query_wencai(query)

            if result is None:
                return None

            # 转换为DataFrame
            df_result = self._convert_to_dataframe(result)

            return df_result

        except Exception as e:
            print(f"pywencai获取失败: {e}")
            return None

    def _query_wencai(self, query: str, retries: int = 2):
        """统一处理问财查询，兼容接口偶发返回空响应的情况"""
        loop_options = [True, False]

        for attempt in range(1, retries + 1):
            for loop in loop_options:
                try:
                    result = pywencai.get(query=query, loop=loop)
                    if self._has_valid_result(result):
                        return result
                    logger.warning(
                        f"问财返回空结果: attempt={attempt} loop={loop} query={query[:80]}"
                    )
                except Exception as exc:
                    logger.warning(
                        f"问财调用失败: attempt={attempt} loop={loop} error={type(exc).__name__}: {exc}"
                    )
            time.sleep(1)

        return None

    def _has_valid_result(self, result) -> bool:
        """判断问财返回是否包含可转换的数据"""
        if result is None:
            return False

        if isinstance(result, pd.DataFrame):
            return not result.empty

        if isinstance(result, list):
            return len(result) > 0

        if isinstance(result, dict):
            for key in ("data", "result", "tableV1"):
                value = result.get(key)
                if isinstance(value, pd.DataFrame) and not value.empty:
                    return True
                if isinstance(value, list) and len(value) > 0:
                    return True
                if isinstance(value, dict) and len(value) > 0:
                    return True
            return len(result) > 0

        return False

    def _convert_to_dataframe(self, result) -> Optional[pd.DataFrame]:
        """将pywencai返回结果转换为DataFrame"""
        try:
            if isinstance(result, pd.DataFrame):
                return result
            elif isinstance(result, dict):
                if 'tableV1' in result:
                    table = result['tableV1']
                    if isinstance(table, pd.DataFrame):
                        return table
                    if isinstance(table, list):
                        return pd.DataFrame(table)
                elif 'data' in result:
                    return pd.DataFrame(result['data'])
                elif 'result' in result:
                    return pd.DataFrame(result['result'])
                else:
                    return pd.DataFrame(result)
            elif isinstance(result, list):
                return pd.DataFrame(result)
            else:
                print(f"⚠️ 未知的数据格式: {type(result)}")
                return None
        except Exception as e:
            print(f"转换DataFrame失败: {e}")
            return None

    def get_stock_codes(self) -> list:
        """
        获取选中股票的代码列表（去掉市场后缀）

        Returns:
            股票代码列表
        """
        if self.selected_stocks is None or self.selected_stocks.empty:
            return []

        codes = []
        for code in self.selected_stocks['股票代码'].tolist():
            if isinstance(code, str):
                clean_code = code.split('.')[0] if '.' in code else code
                codes.append(clean_code)
            else:
                codes.append(str(code))

        return codes


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试低估值选股模块")
    print("=" * 60)

    selector = ValueStockSelector()
    success, df, msg = selector.get_value_stocks(top_n=10)
    print(f"\n结果: {msg}")
    if success and df is not None:
        print(f"共 {len(df)} 只股票")
