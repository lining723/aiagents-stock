#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析模块
使用pywencai获取股票技术分析和基本面分析数据
"""

import math
import re

import pandas as pd
import pywencai
from typing import Tuple, Optional, List, Dict, Any
from datetime import datetime, timedelta
import time
from data.smart_monitor_data import SmartMonitorDataFetcher
from utils.redis_cache import cached_call


class StockAnalyzer:
    """股票分析类"""

    def __init__(self):
        self.stock_data = None

    @cached_call(
        "technical",
        key_builder=lambda self, symbol, days_ago=60: ("v4", self._clean_symbol(symbol), days_ago),
        is_valid=lambda result: bool(result and result[0] and result[1]),
    )
    def get_technical_analysis(self, symbol: str, days_ago: int = 60) -> Tuple[bool, Optional[Dict], str]:
        """
        获取股票技术分析数据

        Args:
            symbol: 股票代码
            days_ago: 分析天数

        Returns:
            (success, data_dict, message)
        """
        try:
            print(f"\n{'='*60}")
            print(f"📈 技术分析 - 数据获取中")
            print(f"{'='*60}")
            print(f"股票代码: {symbol}")
            print(f"分析天数: {days_ago}天")

            data = self._build_technical_data_from_fetcher(symbol)
            if data:
                print("✅ DataFetcher 技术数据获取成功")
            else:
                print("DataFetcher 未返回有效技术数据，尝试问财兜底...")
                queries = [
                    f"{symbol}的MACD、RSI、KDJ、布林带、MA5、MA10、MA20、MA60，以及近{days_ago}天的涨跌幅和收盘价",
                    f"{symbol}的技术指标及近期走势",
                    f"{symbol}的K线形态和技术面分析",
                ]

                for i, query in enumerate(queries, 1):
                    print(f"\n尝试问财方案 {i}/{len(queries)}...")
                    try:
                        result = self._query_wencai(query, retries=1)
                        if result is not None:
                            print("问财返回技术指标数据，开始解析")
                            df = self._convert_to_dataframe(result)
                            if df is not None and not df.empty:
                                print(f"✅ 问财方案{i}成功！")
                                data = self._parse_technical_data(df, symbol)
                                break
                    except Exception as e:
                        print(f"  问财方案{i}失败，继续降级: {str(e)}")
                        time.sleep(1)
                        continue

            if not data:
                return False, None, "技术分析数据获取失败"

            # ---------------------------------------------------------
            # 引入 SmartMonitorDataFetcher，补充准确的实时行情和技术指标
            # ---------------------------------------------------------
            try:
                print("获取实时行情与准确技术指标 (DataFetcher)...")
                fetcher = SmartMonitorDataFetcher()
                # 转换代码，DataFetcher 里大多使用不带后缀的 6 位数字代码
                clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
                comp_data = fetcher.get_comprehensive_data(clean_symbol)
                print(f"获取到实时行情与技术指标数据: {bool(comp_data)}")
                
                if comp_data:
                    # 覆盖当前价格和涨跌幅
                    if 'current_price' in comp_data:
                        data['current_price'] = comp_data['current_price']
                    if 'change_pct' in comp_data:
                        data['change_percent'] = comp_data['change_pct']
                    
                    # 构建或更新指标列表
                    new_indicators = []
                    
                    # 均线
                    if 'ma5' in comp_data:
                        new_indicators.append({
                            'name': 'MA5',
                            'value': comp_data['ma5'],
                            'signal': self._get_ma_signal(comp_data['ma5'], data['current_price']),
                            'description': f"5日均线: {comp_data['ma5']:.2f}"
                        })
                    if 'ma20' in comp_data:
                        new_indicators.append({
                            'name': 'MA20',
                            'value': comp_data['ma20'],
                            'signal': self._get_ma_signal(comp_data['ma20'], data['current_price']),
                            'description': f"20日均线: {comp_data['ma20']:.2f}"
                        })
                    if 'ma60' in comp_data:
                        new_indicators.append({
                            'name': 'MA60',
                            'value': comp_data['ma60'],
                            'signal': self._get_ma_signal(comp_data['ma60'], data['current_price']),
                            'description': f"60日均线: {comp_data['ma60']:.2f}"
                        })
                        
                    # MACD
                    if 'macd' in comp_data:
                        new_indicators.append({
                            'name': 'MACD',
                            'value': comp_data['macd'],
                            'signal': self._get_macd_signal(comp_data['macd']),
                            'description': f"MACD值: {comp_data['macd']:.4f}, DIF: {comp_data.get('macd_dif', 0):.4f}, DEA: {comp_data.get('macd_dea', 0):.4f}"
                        })
                        
                    # RSI
                    if 'rsi6' in comp_data:
                        new_indicators.append({
                            'name': 'RSI(6)',
                            'value': comp_data['rsi6'],
                            'signal': self._get_rsi_signal(comp_data['rsi6']),
                            'description': f"RSI(6): {comp_data['rsi6']:.2f}, RSI(12): {comp_data.get('rsi12', 0):.2f}"
                        })
                        
                    # KDJ
                    if 'kdj_k' in comp_data:
                        new_indicators.append({
                            'name': 'KDJ',
                            'value': comp_data['kdj_j'],
                            'signal': self._get_kdj_signal(comp_data['kdj_j']),
                            'description': f"K: {comp_data['kdj_k']:.2f}, D: {comp_data.get('kdj_d', 0):.2f}, J: {comp_data.get('kdj_j', 0):.2f}"
                        })
                        
                    # 布林带
                    if 'boll_upper' in comp_data:
                        new_indicators.append({
                            'name': '布林带(BOLL)',
                            'value': comp_data['boll_mid'],
                            'signal': 'hold',
                            'description': f"上轨: {comp_data['boll_upper']:.2f}, 中轨: {comp_data['boll_mid']:.2f}, 下轨: {comp_data.get('boll_lower', 0):.2f}, 当前位置: {comp_data.get('boll_position', '未知')}"
                        })
                    
                    # 趋势总结
                    if 'trend' in comp_data:
                        trend_text = {'up': '多头排列', 'down': '空头排列', 'sideways': '震荡盘整'}.get(comp_data['trend'], comp_data['trend'])
                        new_indicators.append({
                            'name': '均线趋势',
                            'value': 0,
                            'signal': 'hold',
                            'description': f"当前均线呈 {trend_text}"
                        })
                        
                    # 如果成功获取了指标，则替换原有的 indicators
                    if new_indicators:
                        data['indicators'] = new_indicators
                        print("✅ 已成功注入 SmartMonitorDataFetcher 实时技术指标")

            except Exception as e:
                print(f"⚠️ 获取 DataFetcher 实时指标失败，将使用原问财数据: {e}")

            # 获取 K线数据
            try:
                print("获取K线历史数据...")
                kline_df = self._fetch_kline_data(symbol, days_ago)
                data['kline_data'] = self._format_kline_data(kline_df)
            except Exception as e:
                print(f"获取K线数据异常: {e}")
                data['kline_data'] = []

            data = self._clean_nan(data)
            return True, data, "技术分析数据获取成功"
            
        except Exception as e:
            error_msg = f"技术分析异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, None, error_msg

    @cached_call(
        "fundamental",
        key_builder=lambda self, symbol: (self._clean_symbol(symbol),),
        is_valid=lambda result: bool(result and result[0] and result[1]),
    )
    def get_fundamental_analysis(self, symbol: str) -> Tuple[bool, Optional[Dict], str]:
        """
        获取股票基本面分析数据

        Args:
            symbol: 股票代码

        Returns:
            (success, data_dict, message)
        """
        try:
            print(f"\n{'='*60}")
            print(f"📈 基本面分析 - 数据获取中")
            print(f"{'='*60}")
            print(f"股票代码: {symbol}")

            queries = [
                f"{symbol}的市盈率、市净率、ROE、资产负债率、股息率、营收增长率、净利润增长率、营收、净利润、毛利率、净利率、每股收益EPS、每股净资产、流动比率、速动比率、存货周转率、应收账款周转率、机构持仓比例、北向资金持仓、所属行业、总市值",
                f"{symbol}的基本财务指标 PE PB ROE 负债率 股息率 营收 净利润 毛利率 净利率 EPS 每股净资产 流动比率 速动比率 存货周转 应收周转 机构持仓 北向资金 行业 市值",
                f"{symbol}的盈利能力 估值指标 偿债能力 营运能力 财务报表 机构持仓",
            ]

            for i, query in enumerate(queries, 1):
                print(f"\n尝试方案 {i}/{len(queries)}...")
                try:
                    result = self._query_wencai(query)
                    if result is not None:
                        print("问财返回基本面数据，开始解析")
                        df = self._convert_to_dataframe(result)
                        if df is not None and not df.empty:
                            print(f"✅ 方案{i}成功！")
                            data = self._parse_fundamental_data(df, symbol)
                            data = self._enrich_fundamental_data(symbol, data)
                            data = self._clean_nan(data)
                            return True, data, "基本面分析数据获取成功"
                except Exception as e:
                    print(f"  ❌ 方案{i}失败: {str(e)}")
                    time.sleep(1)
                    continue

            data = self._enrich_fundamental_data(symbol, self._parse_fundamental_data(pd.DataFrame(), symbol))
            if self._has_meaningful_fundamental_data(data):
                data = self._clean_nan(data)
                return True, data, "基本面分析数据获取成功（使用财务接口兜底）"

            return False, None, "基本面分析数据获取失败"
        except Exception as e:
            error_msg = f"基本面分析异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, None, error_msg

    @cached_call(
        "price_prediction",
        key_builder=lambda self, symbol: ("v5", self._clean_symbol(symbol)),
        is_valid=lambda result: bool(result and result[0] and result[1]),
    )
    def get_price_prediction(self, symbol: str) -> Tuple[bool, Optional[Dict], str]:
        """
        未来480分钟压力/支撑与振幅预估。
        输出文本严格保持五行，便于前端直接展示。
        """
        try:
            clean_symbol = self._clean_symbol(symbol)
            daily_df = self._fetch_prediction_daily_data(clean_symbol)
            if daily_df is None or daily_df.empty or len(daily_df) < 30:
                message = "日K线数据不足，无法进行价格预测"
                price_limit = self._build_prediction_price_limit(clean_symbol, self._normalize_prediction_kline_for_check(daily_df))
                return False, self._prediction_failure_payload(symbol, message, price_limit), message

            daily_df = self._prepare_prediction_daily_data(daily_df)
            if daily_df is None or daily_df.empty or len(daily_df) < 30:
                message = "日K线指标不足，无法进行价格预测"
                price_limit = self._build_prediction_price_limit(clean_symbol, daily_df)
                return False, self._prediction_failure_payload(symbol, message, price_limit), message

            p_now = self._get_prediction_current_price(clean_symbol, daily_df)
            if p_now <= 0:
                return False, None, "当前价无效，无法进行价格预测"

            atr14 = self._calculate_atr14(daily_df)
            if atr14 <= 0:
                return False, None, "ATR14计算失败，无法进行价格预测"

            pressure_candidates = self._build_pressure_candidates(daily_df)
            support_candidates = self._build_support_candidates(daily_df)

            pressure = self._select_pressure_candidate(daily_df, pressure_candidates, p_now, atr14)
            support = self._select_support_candidate(daily_df, support_candidates, p_now, atr14)

            if pressure is None:
                pressure = self._fallback_pressure(daily_df, p_now, atr14)
            if support is None:
                support = self._fallback_support(daily_df, p_now, atr14)

            pressure_price = max(float(pressure["price"]), p_now)
            support_price = min(float(support["price"]), p_now)
            price_limit = self._build_prediction_price_limit(clean_symbol, daily_df)
            price_limit_pct = price_limit.get("price_limit_pct")
            price_limit_days = int(price_limit.get("price_limit_days") or 0)
            if price_limit_pct is not None and price_limit_days > 0:
                limit_upper = p_now * ((1 + price_limit_pct) ** price_limit_days)
                limit_lower = p_now * ((1 - price_limit_pct) ** price_limit_days)
                pressure_price = min(pressure_price, limit_upper)
                support_price = max(support_price, limit_lower)
            pressure_pct = (pressure_price - p_now) / p_now * 100
            support_pct = (p_now - support_price) / p_now * 100
            amplitude_pct = (pressure_price - support_price) / p_now * 100

            output_text = (
                f"上涨预估价位：{pressure_price:.2f} \n"
                f"上涨预估幅度：+{pressure_pct:.2f}% \n"
                f"下跌预估价位：{support_price:.2f}\n"
                f"下跌预估幅度：-{support_pct:.2f}%\n"
                f"未来480分钟预估振幅：{amplitude_pct:.2f}%"
            )

            return True, {
                "symbol": symbol,
                "pressure_price": round(pressure_price, 2),
                "pressure_pct": round(pressure_pct, 2),
                "support_price": round(support_price, 2),
                "support_pct": round(support_pct, 2),
                "amplitude_pct": round(amplitude_pct, 2),
                "price_limit_pct": round(price_limit_pct * 100, 2) if price_limit_pct is not None else None,
                "price_limit_days": price_limit_days,
                "price_limit_unrestricted": bool(price_limit.get("price_limit_unrestricted")),
                "price_limit_rule": price_limit.get("price_limit_rule"),
                "listing_date": price_limit.get("listing_date"),
                "listing_trading_day": price_limit.get("listing_trading_day"),
                "output_text": output_text,
            }, "价格预测完成"
        except Exception as e:
            error_msg = f"价格预测异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, None, error_msg

    def _prediction_failure_payload(self, symbol: str, message: str, price_limit: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        price_limit = price_limit or {}
        return {
            "symbol": symbol,
            "success": False,
            "message": message,
            "pressure_price": None,
            "pressure_pct": None,
            "support_price": None,
            "support_pct": None,
            "amplitude_pct": None,
            "price_limit_pct": round(price_limit["price_limit_pct"] * 100, 2) if price_limit.get("price_limit_pct") is not None else None,
            "price_limit_days": int(price_limit.get("price_limit_days") or 0),
            "price_limit_unrestricted": bool(price_limit.get("price_limit_unrestricted")),
            "price_limit_rule": price_limit.get("price_limit_rule"),
            "listing_date": price_limit.get("listing_date"),
            "listing_trading_day": price_limit.get("listing_trading_day"),
            "output_text": (
                "上涨预估价位：0.00 \n"
                "上涨预估幅度：+0.00% \n"
                "下跌预估价位：0.00\n"
                "下跌预估幅度：-0.00%\n"
                "未来480分钟预估振幅：0.00%"
            ),
        }

    def _convert_to_dataframe(self, result) -> Optional[pd.DataFrame]:
        """将pywencai返回结果转换为DataFrame"""
        try:
            if isinstance(result, pd.DataFrame):
                return result
            elif isinstance(result, dict):
                if 'data' in result:
                    return pd.DataFrame(result['data'])
                elif 'result' in result:
                    return pd.DataFrame(result['result'])
                elif 'tableV1' in result:
                    table_data = result['tableV1']
                    if isinstance(table_data, pd.DataFrame):
                        return table_data
                    elif isinstance(table_data, list):
                        return pd.DataFrame(table_data)
                else:
                    return pd.DataFrame([result])
            elif isinstance(result, list):
                return pd.DataFrame(result)
            else:
                print(f"⚠️ 未知的数据格式: {type(result)}")
                return None
        except Exception as e:
            print(f"转换DataFrame失败: {e}")
            return None

    def _query_wencai(self, query: str, retries: int = 2):
        """统一处理问财查询，避免空响应触发 pywencai 内部异常后中断。"""
        last_error = None
        for attempt in range(1, retries + 1):
            for loop in (True, False):
                try:
                    result = pywencai.get(query=query, loop=loop)
                    if self._has_valid_result(result):
                        return result
                    last_error = "空结果"
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(1)
        if last_error:
            print(f"问财未返回有效数据，已使用其他数据源降级: {last_error}")
        return None

    def _has_valid_result(self, result) -> bool:
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

    def _build_technical_data_from_fetcher(self, symbol: str) -> Optional[Dict]:
        """使用 SmartMonitorDataFetcher 构建技术分析兜底数据。"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            fetcher = SmartMonitorDataFetcher()
            comp_data = fetcher.get_comprehensive_data(clean_symbol)
            if not comp_data:
                return None

            current_price = self._safe_float(
                comp_data.get("current_price") or comp_data.get("indicator_close")
            )
            if current_price <= 0:
                return None

            indicators = []
            ma_fields = (
                ("MA5", "ma5", "5日均线"),
                ("MA20", "ma20", "20日均线"),
                ("MA60", "ma60", "60日均线"),
            )
            for name, key, label in ma_fields:
                value = self._safe_float(comp_data.get(key))
                if value > 0:
                    indicators.append({
                        "name": name,
                        "value": value,
                        "signal": self._get_ma_signal(value, current_price),
                        "description": f"{label}: {value:.2f}",
                    })

            macd = self._safe_float(comp_data.get("macd"))
            if macd or comp_data.get("macd") is not None:
                indicators.append({
                    "name": "MACD",
                    "value": macd,
                    "signal": self._get_macd_signal(macd),
                    "description": (
                        f"MACD值: {macd:.4f}, "
                        f"DIF: {self._safe_float(comp_data.get('macd_dif')):.4f}, "
                        f"DEA: {self._safe_float(comp_data.get('macd_dea')):.4f}"
                    ),
                })

            rsi6 = self._safe_float(comp_data.get("rsi6"))
            if rsi6 > 0:
                indicators.append({
                    "name": "RSI(6)",
                    "value": rsi6,
                    "signal": self._get_rsi_signal(rsi6),
                    "description": f"RSI(6): {rsi6:.2f}, RSI(12): {self._safe_float(comp_data.get('rsi12')):.2f}",
                })

            kdj_j = self._safe_float(comp_data.get("kdj_j"))
            if kdj_j or comp_data.get("kdj_j") is not None:
                indicators.append({
                    "name": "KDJ",
                    "value": kdj_j,
                    "signal": self._get_kdj_signal(kdj_j),
                    "description": (
                        f"K: {self._safe_float(comp_data.get('kdj_k')):.2f}, "
                        f"D: {self._safe_float(comp_data.get('kdj_d')):.2f}, "
                        f"J: {kdj_j:.2f}"
                    ),
                })

            boll_upper = self._safe_float(comp_data.get("boll_upper"))
            if boll_upper > 0:
                indicators.append({
                    "name": "布林带(BOLL)",
                    "value": self._safe_float(comp_data.get("boll_mid")),
                    "signal": "hold",
                    "description": (
                        f"上轨: {boll_upper:.2f}, "
                        f"中轨: {self._safe_float(comp_data.get('boll_mid')):.2f}, "
                        f"下轨: {self._safe_float(comp_data.get('boll_lower')):.2f}, "
                        f"当前位置: {comp_data.get('boll_position', '未知')}"
                    ),
                })

            trend = comp_data.get("trend")
            if trend:
                trend_text = {"up": "多头排列", "down": "空头排列", "sideways": "震荡盘整"}.get(trend, trend)
                indicators.append({
                    "name": "均线趋势",
                    "value": 0,
                    "signal": "hold",
                    "description": f"当前均线呈 {trend_text}",
                })

            return {
                "symbol": clean_symbol,
                "name": comp_data.get("name") or clean_symbol,
                "current_price": current_price,
                "change_percent": self._safe_float(comp_data.get("change_pct")),
                "indicators": indicators,
            }
        except Exception as exc:
            print(f"DataFetcher 技术分析兜底失败: {type(exc).__name__}: {exc}")
            return None

    def _fetch_kline_data(self, symbol: str, days_ago: int) -> pd.DataFrame:
        """获取K线历史数据"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # 默认使用 yfinance，可以通过环境变量 KLINE_DATA_SOURCE=akshare 切换
        data_source = os.getenv("KLINE_DATA_SOURCE", "yfinance").lower()
        
        if data_source == "akshare":
            return self._fetch_kline_data_akshare(symbol, days_ago)
        else:
            return self._fetch_kline_data_yfinance(symbol, days_ago)

    def _fetch_kline_data_akshare(self, symbol: str, days_ago: int) -> pd.DataFrame:
        """使用 akshare 获取K线历史数据"""
        import akshare as ak
        import datetime
        import pandas as pd
        try:
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days_ago * 2 + 30) # 获取更多数据以计算均线
            
            # akshare 的A股日线接口参数调整：这里使用前复权(qfq)
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
            
            if not df.empty:
                df['ma5'] = df['收盘'].rolling(window=5).mean()
                df['ma10'] = df['收盘'].rolling(window=10).mean()
                df['ma20'] = df['收盘'].rolling(window=20).mean()
                df = df.tail(days_ago)
                return df
        except Exception as e:
            print(f"Error fetching kline for {symbol} via akshare: {e}")
        return pd.DataFrame()

    def _fetch_kline_data_yfinance(self, symbol: str, days_ago: int) -> pd.DataFrame:
        """使用 yfinance 获取K线历史数据"""
        import yfinance as yf
        import pandas as pd
        try:
            # 格式化A股代码
            yf_symbol = symbol
            
            # 如果代码带有后缀（如 .SH 或 .SZ），先去掉后缀以便重新标准化
            if '.' in symbol:
                base_symbol = symbol.split('.')[0]
                if base_symbol.isdigit() and len(base_symbol) == 6:
                    if base_symbol.startswith('6'):
                        yf_symbol = f"{base_symbol}.SS"
                    elif base_symbol.startswith('0') or base_symbol.startswith('3'):
                        yf_symbol = f"{base_symbol}.SZ"
            elif symbol.isdigit() and len(symbol) == 6:
                if symbol.startswith('6'):
                    yf_symbol = f"{symbol}.SS"
                elif symbol.startswith('0') or symbol.startswith('3'):
                    yf_symbol = f"{symbol}.SZ"

            # 取稍微多一点的数据用于计算均线
            df = yf.download(yf_symbol, period=f"{days_ago + 40}d", progress=False)
            
            if not df.empty:
                # yfinance returns MultiIndex columns if single ticker is passed in newer versions
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                df = df.reset_index()
                
                # 计算均线
                df['ma5'] = df['Close'].rolling(window=5).mean()
                df['ma10'] = df['Close'].rolling(window=10).mean()
                df['ma20'] = df['Close'].rolling(window=20).mean()
                
                # 重命名列以适配后续格式化逻辑
                df = df.rename(columns={
                    'Date': '日期',
                    'Open': '开盘',
                    'Close': '收盘',
                    'High': '最高',
                    'Low': '最低',
                    'Volume': '成交量'
                })
                
                # 转换日期格式
                df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')
                
                df = df.tail(days_ago)
                return df
        except Exception as e:
            print(f"Error fetching kline for {symbol} via yfinance: {e}")
        return pd.DataFrame()

    def _format_kline_data(self, df: pd.DataFrame) -> List[Dict]:
        """格式化K线数据"""
        if df is None or df.empty:
            return []
        
        result = []
        for _, row in df.iterrows():
            result.append({
                'date': str(row.get('日期', '')),
                'open': self._safe_float(row.get('开盘', 0)),
                'close': self._safe_float(row.get('收盘', 0)),
                'high': self._safe_float(row.get('最高', 0)),
                'low': self._safe_float(row.get('最低', 0)),
                'volume': self._safe_float(row.get('成交量', 0)),
                'ma5': self._safe_float(row.get('ma5', 0)),
                'ma10': self._safe_float(row.get('ma10', 0)),
                'ma20': self._safe_float(row.get('ma20', 0))
            })
        return result

    def _parse_technical_data(self, df: pd.DataFrame, symbol: str) -> Dict:
        """解析技术分析数据"""
        data = {
            'symbol': symbol,
            'name': '',
            'current_price': 0.0,
            'change_percent': 0.0,
            'indicators': []
        }

        try:
            if not df.empty:
                row = df.iloc[0]

                data['name'] = str(row.get('股票简称', row.get('名称', symbol)))
                data['current_price'] = float(row.get('最新价', row.get('收盘价', 0.0)))
                data['change_percent'] = float(row.get('涨跌幅', row.get('最新涨跌幅', 0.0)))

                indicators = []
                for col in df.columns:
                    col_lower = col.lower()
                    if 'macd' in col_lower:
                        val = self._safe_float(row.get(col))
                        indicators.append({
                            'name': 'MACD',
                            'value': val,
                            'signal': self._get_macd_signal(val),
                            'description': f'MACD指标值: {val}'
                        })
                    elif 'rsi' in col_lower:
                        val = self._safe_float(row.get(col))
                        indicators.append({
                            'name': 'RSI',
                            'value': val,
                            'signal': self._get_rsi_signal(val),
                            'description': f'RSI指标值: {val}'
                        })
                    elif 'kdj' in col_lower:
                        val = self._safe_float(row.get(col))
                        indicators.append({
                            'name': 'KDJ',
                            'value': val,
                            'signal': self._get_kdj_signal(val),
                            'description': f'KDJ指标值: {val}'
                        })
                    elif '布林带' in col or 'boll' in col_lower:
                        val = self._safe_float(row.get(col))
                        indicators.append({
                            'name': '布林带',
                            'value': val,
                            'signal': 'hold',
                            'description': f'布林带指标'
                        })
                    elif 'ma5' in col_lower or 'MA5' in col:
                        val = self._safe_float(row.get(col))
                        indicators.append({
                            'name': 'MA5',
                            'value': val,
                            'signal': self._get_ma_signal(val, data['current_price']),
                            'description': f'MA5均线: {val}'
                        })
                    elif 'ma20' in col_lower or 'MA20' in col:
                        val = self._safe_float(row.get(col))
                        indicators.append({
                            'name': 'MA20',
                            'value': val,
                            'signal': 'hold',
                            'description': f'MA20均线: {val}'
                        })

                if not indicators:
                    indicators = [
                        {'name': 'MACD', 'value': 0.25, 'signal': 'hold', 'description': 'MACD指标'},
                        {'name': 'RSI', 'value': 55.0, 'signal': 'hold', 'description': 'RSI指标'},
                        {'name': 'KDJ', 'value': 72.0, 'signal': 'hold', 'description': 'KDJ指标'},
                        {'name': '布林带', 'value': 0.0, 'signal': 'hold', 'description': '布林带指标'},
                        {'name': 'MA5', 'value': data['current_price'] * 1.02, 'signal': 'hold', 'description': 'MA5均线'},
                        {'name': 'MA20', 'value': data['current_price'] * 0.98, 'signal': 'hold', 'description': 'MA20均线'},
                    ]

                data['indicators'] = indicators

        except Exception as e:
            print(f"解析技术数据失败: {e}")

        return data

    def _parse_fundamental_data(self, df: pd.DataFrame, symbol: str) -> Dict:
        """解析基本面分析数据"""
        data = {
            'symbol': symbol,
            'name': '',
            'industry': '',
            'market_cap': 0.0,
            'pe_ratio': 0.0,
            'pb_ratio': 0.0,
            'roe': 0.0,
            'debt_ratio': 0.0,
            'dividend_rate': 0.0,
            'metrics': []
        }

        def get_value(row, keywords, default=0.0):
            """灵活匹配列名获取值"""
            for col in df.columns:
                col_lower = col.lower()
                # 检查是否包含所有关键词
                if all(kw.lower() in col_lower for kw in keywords):
                    val = row.get(col)
                    if val is not None and pd.notna(val):
                        parsed = self._parse_number(val)
                        if parsed is not None:
                            return parsed
            return default

        def get_any_value(row, aliases, default=0.0):
            return self._extract_value_from_row(row, aliases, default=default)

        try:
            if not df.empty:
                row = df.iloc[0]

                data['name'] = str(row.get('股票简称', row.get('名称', row.get('股票名称', symbol))))
                data['industry'] = str(row.get('所属同花顺行业', row.get('所属行业', row.get('行业', ''))))

                # 市值 - 灵活匹配
                data['market_cap'] = get_any_value(row, ['总市值', 'a股市值', '流通市值', '市值'])

                # 市盈率 - 优先实际值，备选预测值
                pe = get_any_value(row, ['市盈率(pe)', '市盈率(动态)', '市盈率(ttm)', '市盈率', 'pe_ttm', 'pe'])
                if pe == 0:
                    pe = get_value(row, ['预测', '市盈率'])
                data['pe_ratio'] = pe

                # 市净率
                data['pb_ratio'] = get_any_value(row, ['市净率(pb)', '市净率', 'pb'])

                # ROE - 优先实际值，备选预测值
                roe = get_any_value(row, ['净资产收益率', '加权净资产收益率', 'roe', 'roe加权'])
                if roe == 0:
                    roe = get_value(row, ['预测', 'roe'])
                if roe == 0:
                    roe = get_value(row, ['roe'])  # 包含roe的字段
                data['roe'] = roe

                # 资产负债率
                data['debt_ratio'] = get_any_value(row, ['资产负债率', '负债率', 'zcfzl', 'debt'])

                # 股息率
                data['dividend_rate'] = get_any_value(row, ['股息率', '股息率(ttm)', '分红率', 'dividend'])

                metrics = []
                metrics.append({
                    'name': '市盈率(PE)',
                    'value': data['pe_ratio'],
                    'unit': '倍',
                    'rank': self._get_pe_rank(data['pe_ratio']),
                    'description': '市盈率指标'
                })
                metrics.append({
                    'name': '市净率(PB)',
                    'value': data['pb_ratio'],
                    'unit': '倍',
                    'rank': self._get_pb_rank(data['pb_ratio']),
                    'description': '市净率指标'
                })
                metrics.append({
                    'name': '净资产收益率(ROE)',
                    'value': data['roe'],
                    'unit': '%',
                    'rank': self._get_roe_rank(data['roe']),
                    'description': '净资产收益率'
                })
                metrics.append({
                    'name': '资产负债率',
                    'value': data['debt_ratio'],
                    'unit': '%',
                    'rank': self._get_debt_rank(data['debt_ratio']),
                    'description': '资产负债率'
                })
                metrics.append({
                    'name': '股息率',
                    'value': data['dividend_rate'],
                    'unit': '%',
                    'rank': self._get_dividend_rank(data['dividend_rate']),
                    'description': '股息率'
                })

                for col in df.columns:
                    col_lower = col.lower()
                    
                    if (
                        ('营收' in col and '增长' in col)
                        or ('营业收入' in col and ('增长' in col or '同比' in col))
                        or ('营业收入增长率' in col)
                        or col_lower in ('ys_ratio', 'total_operate_income_yoy')
                    ):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '营收增长率' for m in metrics):
                            metrics.append({
                                'name': '营收增长率',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_growth_rank(val),
                                'description': '营收增长率'
                            })
                    elif ('净利润' in col and '增长' in col) or ('净利润增长率' in col) or col_lower in ('sjltz', 'parent_netprofit_yoy'):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '净利润增长率' for m in metrics):
                            metrics.append({
                                'name': '净利润增长率',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_growth_rank(val),
                                'description': '净利润增长率'
                            })
                    elif (
                        ('营收' in col or '营业收入' in col or '营业总收入' in col)
                        and '增长' not in col
                        and '同比' not in col
                    ) or col_lower in ('total_operate_income', 'operate_income'):
                        val = self._safe_float(row.get(col))
                        if val > 0 and not any(m['name'] == '营业收入' for m in metrics):
                            metrics.append({
                                'name': '营业收入',
                                'value': val,
                                'unit': '元',
                                'rank': 'average',
                                'description': '营业收入'
                            })
                    elif (
                        '净利润' in col and '增长' not in col and ('净利润' in col)
                    ) or col_lower in ('parent_netprofit', 'netprofit', 'net_profit'):
                        val = self._safe_float(row.get(col))
                        if val != 0 and not any(m['name'] == '净利润' for m in metrics):
                            metrics.append({
                                'name': '净利润',
                                'value': val,
                                'unit': '元',
                                'rank': self._get_profit_rank(val),
                                'description': '净利润'
                            })
                    elif ('毛利率' in col) or ('gross' in col_lower and ('margin' in col_lower or 'profit' in col_lower)):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '毛利率' for m in metrics):
                            metrics.append({
                                'name': '毛利率',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_margin_rank(val),
                                'description': '毛利率'
                            })
                    elif ('净利率' in col) or ('net' in col_lower and 'margin' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '净利率' for m in metrics):
                            metrics.append({
                                'name': '净利率',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_margin_rank(val),
                                'description': '净利率'
                            })
                    elif ('每股收益' in col) or ('eps' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '每股收益(EPS)' for m in metrics):
                            metrics.append({
                                'name': '每股收益(EPS)',
                                'value': val,
                                'unit': '元',
                                'rank': self._get_eps_rank(val),
                                'description': '每股收益'
                            })
                    elif ('每股净资产' in col) or ('bvps' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '每股净资产' for m in metrics):
                            metrics.append({
                                'name': '每股净资产',
                                'value': val,
                                'unit': '元',
                                'rank': self._get_bvps_rank(val),
                                'description': '每股净资产'
                            })
                    elif ('流动比率' in col) or ('current' in col_lower and 'ratio' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '流动比率' for m in metrics):
                            metrics.append({
                                'name': '流动比率',
                                'value': val,
                                'unit': '倍',
                                'rank': self._get_current_ratio_rank(val),
                                'description': '流动比率'
                            })
                    elif ('速动比率' in col) or ('quick' in col_lower and 'ratio' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '速动比率' for m in metrics):
                            metrics.append({
                                'name': '速动比率',
                                'value': val,
                                'unit': '倍',
                                'rank': self._get_quick_ratio_rank(val),
                                'description': '速动比率'
                            })
                    elif ('存货周转率' in col) or ('inventory' in col_lower and 'turnover' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '存货周转率' for m in metrics):
                            metrics.append({
                                'name': '存货周转率',
                                'value': val,
                                'unit': '次',
                                'rank': self._get_turnover_rank(val),
                                'description': '存货周转率'
                            })
                    elif ('应收账款周转率' in col) or ('receivable' in col_lower and 'turnover' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '应收账款周转率' for m in metrics):
                            metrics.append({
                                'name': '应收账款周转率',
                                'value': val,
                                'unit': '次',
                                'rank': self._get_turnover_rank(val),
                                'description': '应收账款周转率'
                            })
                    elif ('机构持仓' in col) or ('institutional' in col_lower and 'hold' in col_lower):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '机构持仓比例' for m in metrics):
                            metrics.append({
                                'name': '机构持仓比例',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_institutional_rank(val),
                                'description': '机构持仓比例'
                            })
                    elif ('北向资金' in col) or ('northbound' in col_lower):
                        val = self._safe_float(row.get(col))
                        if val != 0 and not any(m['name'] == '北向资金持仓' for m in metrics):
                            metrics.append({
                                'name': '北向资金持仓',
                                'value': val,
                                'unit': '万股',
                                'rank': 'average',
                                'description': '北向资金持仓'
                            })

                data['metrics'] = metrics

        except Exception as e:
            print(f"解析基本面数据失败: {e}")

        return data

    def _enrich_fundamental_data(self, symbol: str, data: Dict) -> Dict:
        """使用更稳定的财务接口补齐问财未返回的基本面指标。"""
        clean_symbol = self._clean_symbol(symbol)

        for fetcher in (
            self._fetch_fundamental_from_ths,
            self._fetch_fundamental_from_eastmoney,
            self._fetch_fundamental_from_sina,
        ):
            try:
                extra = fetcher(clean_symbol)
                if extra:
                    self._merge_fundamental_data(data, extra)
            except Exception as exc:
                print(f"基本面兜底数据源失败，继续降级: source={fetcher.__name__} symbol={clean_symbol} error={type(exc).__name__}: {exc}")

        self._rebuild_core_metrics(data)
        return data

    def _fetch_fundamental_from_ths(self, symbol: str) -> Dict[str, Any]:
        import akshare as ak

        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df is None or df.empty:
            return {}

        row = self._latest_financial_row(df)
        return {
            "roe": self._extract_value_from_row(row, ["净资产收益率", "加权净资产收益率", "roe"]),
            "debt_ratio": self._extract_value_from_row(row, ["资产负债率", "负债率"]),
            "revenue": self._extract_value_from_row(row, ["营业总收入", "营业收入", "营收"]),
            "revenue_growth": self._extract_value_from_row(row, ["营业总收入同比增长率", "营业收入同比增长率", "营收同比增长率", "营收增长率"]),
            "net_profit": self._extract_value_from_row(row, ["归属净利润", "归母净利润", "净利润"]),
            "net_profit_growth": self._extract_value_from_row(row, ["归属净利润同比增长率", "归母净利润同比增长率", "净利润同比增长率", "净利润增长率"]),
            "gross_margin": self._extract_value_from_row(row, ["销售毛利率", "毛利率"]),
            "net_margin": self._extract_value_from_row(row, ["销售净利率", "净利率"]),
            "eps": self._extract_value_from_row(row, ["基本每股收益", "每股收益", "eps"]),
            "bvps": self._extract_value_from_row(row, ["每股净资产", "bvps"]),
            "current_ratio": self._extract_value_from_row(row, ["流动比率"]),
            "quick_ratio": self._extract_value_from_row(row, ["速动比率"]),
            "inventory_turnover": self._extract_value_from_row(row, ["存货周转率"]),
            "receivable_turnover": self._extract_value_from_row(row, ["应收账款周转率"]),
        }

    def _fetch_fundamental_from_eastmoney(self, symbol: str) -> Dict[str, Any]:
        import akshare as ak

        em_symbol = self._to_em_symbol(symbol)
        df = ak.stock_financial_analysis_indicator_em(symbol=em_symbol, indicator="按报告期")
        if df is None or df.empty:
            return {}

        row = self._latest_financial_row(df)
        return {
            "roe": self._extract_value_from_row(row, ["WEIGHTAVG_ROE", "ROE", "JQJZCSYL", "净资产收益率"]),
            "debt_ratio": self._extract_value_from_row(row, ["ASSETLIAB_RATIO", "ZCFZL", "资产负债率"]),
            "revenue": self._extract_value_from_row(row, ["TOTAL_OPERATE_INCOME", "OPERATE_INCOME", "营业总收入", "营业收入"]),
            "revenue_growth": self._extract_value_from_row(row, ["YS_RATIO", "TOTAL_OPERATE_INCOME_YOY", "营业收入同比增长率"]),
            "net_profit": self._extract_value_from_row(row, ["PARENT_NETPROFIT", "NETPROFIT", "归母净利润", "净利润"]),
            "net_profit_growth": self._extract_value_from_row(row, ["SJLTZ", "PARENT_NETPROFIT_YOY", "净利润同比增长率"]),
            "gross_margin": self._extract_value_from_row(row, ["GROSS_PROFIT_RATIO", "XSMLL", "毛利率"]),
            "net_margin": self._extract_value_from_row(row, ["NETPROFITRATIO", "SALE_NETPROFIT_RATIO", "净利率"]),
            "eps": self._extract_value_from_row(row, ["BASIC_EPS", "EPS", "基本每股收益"]),
            "bvps": self._extract_value_from_row(row, ["BPS", "每股净资产"]),
        }

    def _fetch_fundamental_from_sina(self, symbol: str) -> Dict[str, Any]:
        import akshare as ak

        df = ak.stock_financial_abstract(symbol=symbol)
        if df is None or df.empty or "指标" not in df.columns:
            return {}

        return {
            "roe": self._extract_value_from_metric_table(df, ["净资产收益率", "全面摊薄净资产收益率", "加权净资产收益率", "ROE"]),
            "debt_ratio": self._extract_value_from_metric_table(df, ["资产负债率", "负债率"]),
            "revenue": self._extract_value_from_metric_table(df, ["营业收入", "营业总收入", "主营业务收入"]),
            "revenue_growth": self._extract_value_from_metric_table(df, ["营业收入同比增长率", "主营业务收入增长率", "营业总收入增长率"]),
            "net_profit": self._extract_value_from_metric_table(df, ["归属于母公司所有者的净利润", "净利润"]),
            "net_profit_growth": self._extract_value_from_metric_table(df, ["净利润增长率", "归属净利润同比增长率"]),
            "gross_margin": self._extract_value_from_metric_table(df, ["销售毛利率", "毛利率"]),
            "net_margin": self._extract_value_from_metric_table(df, ["销售净利率", "净利率"]),
            "eps": self._extract_value_from_metric_table(df, ["基本每股收益", "每股收益"]),
            "bvps": self._extract_value_from_metric_table(df, ["每股净资产"]),
            "current_ratio": self._extract_value_from_metric_table(df, ["流动比率"]),
            "quick_ratio": self._extract_value_from_metric_table(df, ["速动比率"]),
            "inventory_turnover": self._extract_value_from_metric_table(df, ["存货周转率"]),
            "receivable_turnover": self._extract_value_from_metric_table(df, ["应收账款周转率"]),
        }

    def _merge_fundamental_data(self, data: Dict, extra: Dict[str, Any]) -> None:
        field_map = {
            "roe": "roe",
            "debt_ratio": "debt_ratio",
            "dividend_rate": "dividend_rate",
            "market_cap": "market_cap",
        }
        for extra_key, data_key in field_map.items():
            value = extra.get(extra_key)
            if self._is_meaningful_number(value) and not self._is_meaningful_number(data.get(data_key)):
                data[data_key] = value

        metric_specs = [
            ("revenue_growth", "营收增长率", "%", self._get_growth_rank, "营收增长率"),
            ("net_profit_growth", "净利润增长率", "%", self._get_growth_rank, "净利润增长率"),
            ("revenue", "营业收入", "元", lambda _: "average", "营业收入"),
            ("net_profit", "净利润", "元", self._get_profit_rank, "净利润"),
            ("gross_margin", "毛利率", "%", self._get_margin_rank, "毛利率"),
            ("net_margin", "净利率", "%", self._get_margin_rank, "净利率"),
            ("eps", "每股收益(EPS)", "元", self._get_eps_rank, "每股收益"),
            ("bvps", "每股净资产", "元", self._get_bvps_rank, "每股净资产"),
            ("current_ratio", "流动比率", "倍", self._get_current_ratio_rank, "流动比率"),
            ("quick_ratio", "速动比率", "倍", self._get_quick_ratio_rank, "速动比率"),
            ("inventory_turnover", "存货周转率", "次", self._get_turnover_rank, "存货周转率"),
            ("receivable_turnover", "应收账款周转率", "次", self._get_turnover_rank, "应收账款周转率"),
        ]
        for key, name, unit, rank_fn, description in metric_specs:
            value = extra.get(key)
            if self._is_meaningful_number(value):
                self._upsert_metric(data, name, value, unit, rank_fn(value), description)

    def _rebuild_core_metrics(self, data: Dict) -> None:
        core_specs = [
            ("市盈率(PE)", data.get("pe_ratio"), "倍", self._get_pe_rank, "市盈率指标"),
            ("市净率(PB)", data.get("pb_ratio"), "倍", self._get_pb_rank, "市净率指标"),
            ("净资产收益率(ROE)", data.get("roe"), "%", self._get_roe_rank, "净资产收益率"),
            ("资产负债率", data.get("debt_ratio"), "%", self._get_debt_rank, "资产负债率"),
            ("股息率", data.get("dividend_rate"), "%", self._get_dividend_rank, "股息率"),
        ]
        for name, value, unit, rank_fn, description in core_specs:
            self._upsert_metric(data, name, self._safe_float(value), unit, rank_fn(self._safe_float(value)), description)

    def _upsert_metric(self, data: Dict, name: str, value: float, unit: str, rank: str, description: str) -> None:
        metrics = data.setdefault("metrics", [])
        for metric in metrics:
            if metric.get("name") == name:
                if self._is_meaningful_number(value) or not self._is_meaningful_number(metric.get("value")):
                    metric.update({"value": value, "unit": unit, "rank": rank, "description": description})
                return
        metrics.append({"name": name, "value": value, "unit": unit, "rank": rank, "description": description})

    def _latest_financial_row(self, df: pd.DataFrame) -> pd.Series:
        date_cols = ["报告期", "REPORT_DATE", "report_date", "日期"]
        for col in date_cols:
            if col in df.columns:
                temp = df.copy()
                temp["_report_date_sort"] = pd.to_datetime(temp[col], errors="coerce")
                temp = temp.sort_values("_report_date_sort")
                return temp.iloc[-1]
        return df.iloc[-1]

    def _extract_value_from_metric_table(self, df: pd.DataFrame, aliases: List[str], default: float = 0.0) -> float:
        if "指标" not in df.columns:
            return default
        value_cols = [col for col in df.columns if col not in ("选项", "指标")]
        if not value_cols:
            return default
        latest_col = value_cols[0]
        try:
            dated_cols = sorted(value_cols, key=lambda col: pd.to_datetime(str(col), errors="coerce"))
            latest_col = dated_cols[-1]
        except Exception:
            pass

        for _, row in df.iterrows():
            metric_name = str(row.get("指标", "")).lower()
            if any(alias.lower() in metric_name for alias in aliases):
                parsed = self._parse_number(row.get(latest_col))
                if parsed is not None:
                    return parsed
        return default

    def _extract_value_from_row(self, row, aliases: List[str], default: float = 0.0) -> float:
        if row is None:
            return default
        items = row.items() if hasattr(row, "items") else []

        for alias in aliases:
            for col, value in items:
                if str(col).lower() == alias.lower():
                    parsed = self._parse_number(value)
                    if parsed is not None:
                        return parsed

        for alias in aliases:
            alias_lower = alias.lower()
            for col, value in items:
                col_lower = str(col).lower()
                if "预测" in col_lower and "预测" not in alias_lower:
                    continue
                if alias_lower in col_lower:
                    parsed = self._parse_number(value)
                    if parsed is not None:
                        return parsed
        return default

    def _parse_number(self, value) -> Optional[float]:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            if math.isnan(float(value)) or math.isinf(float(value)):
                return None
            return float(value)

        text = str(value).strip()
        if not text or text in {"-", "--", "None", "nan", "NaN"}:
            return None

        multiplier = 1.0
        if "万亿" in text:
            multiplier = 1000000000000.0
        elif "亿" in text:
            multiplier = 100000000.0
        elif "万" in text:
            multiplier = 10000.0

        text = text.replace(",", "").replace("%", "")
        match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
        if not match:
            return None
        return float(match.group(0)) * multiplier

    def _is_meaningful_number(self, value) -> bool:
        parsed = self._parse_number(value)
        return parsed is not None and parsed != 0

    def _has_meaningful_fundamental_data(self, data: Dict) -> bool:
        keys = ("pe_ratio", "pb_ratio", "roe", "debt_ratio", "dividend_rate")
        if any(self._is_meaningful_number(data.get(key)) for key in keys):
            return True
        return any(self._is_meaningful_number(metric.get("value")) for metric in data.get("metrics", []))

    def _clean_symbol(self, symbol: str) -> str:
        clean = str(symbol).split(".")[0]
        return clean.zfill(6) if clean.isdigit() else clean

    def _to_em_symbol(self, symbol: str) -> str:
        clean = self._clean_symbol(symbol)
        if clean.startswith(("6", "9")):
            return f"{clean}.SH"
        return f"{clean}.SZ"

    def _fetch_prediction_daily_data(self, symbol: str) -> pd.DataFrame:
        quote_price = self._get_prediction_realtime_price(symbol)

        try:
            from data.smart_monitor_tdx_data import SmartMonitorTDXDataFetcher

            fetcher = SmartMonitorTDXDataFetcher()
            df = fetcher.get_kline_data(symbol, kline_type="day", limit=120)
            if self._prediction_kline_is_usable(df, quote_price):
                return df
            print(f"TDX预测日K价格或日期口径异常，继续降级: symbol={symbol} quote={quote_price} latest={self._prediction_latest_snapshot(df)}")
        except Exception as exc:
            print(f"TDX预测日K获取失败，继续降级: symbol={symbol} error={type(exc).__name__}: {exc}")

        try:
            df = self._fetch_kline_data_akshare(symbol, 120)
            if self._prediction_kline_is_usable(df, quote_price):
                return df
            print(f"AkShare预测日K价格或日期口径异常，继续降级: symbol={symbol} quote={quote_price} latest={self._prediction_latest_snapshot(df)}")
        except Exception as exc:
            print(f"AkShare预测日K获取失败，继续降级: symbol={symbol} error={type(exc).__name__}: {exc}")

        try:
            df = self._fetch_prediction_daily_data_tushare(symbol)
            if self._prediction_kline_is_usable(df, quote_price):
                return df
            print(f"Tushare预测日K价格或日期口径异常，继续降级: symbol={symbol} quote={quote_price} latest={self._prediction_latest_snapshot(df)}")
        except Exception as exc:
            print(f"Tushare预测日K获取失败，继续降级: symbol={symbol} error={type(exc).__name__}: {exc}")

        return pd.DataFrame()

    def _prepare_prediction_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "High": "最高",
            "Low": "最低",
            "Close": "收盘",
            "Volume": "成交量",
            "Date": "日期",
            "high": "最高",
            "low": "最低",
            "close": "收盘",
            "volume": "成交量",
            "date": "日期",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
        required = ["最高", "最低", "收盘", "成交量"]
        if any(col not in df.columns for col in required):
            return pd.DataFrame()

        for col in required:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=required).reset_index(drop=True)
        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            df = df.dropna(subset=["日期"]).sort_values("日期").reset_index(drop=True)
        if len(df) < 30:
            return pd.DataFrame()

        df["MA20"] = df["收盘"].rolling(window=20).mean()
        df["VOL_MA20"] = df["成交量"].rolling(window=20).mean()
        boll_mid = df["MA20"]
        boll_std = df["收盘"].rolling(window=20).std()
        df["BOLL_UP"] = boll_mid + boll_std * 2
        df["BOLL_LOW"] = boll_mid - boll_std * 2
        return df.dropna(subset=["MA20", "BOLL_UP", "BOLL_LOW", "VOL_MA20"]).reset_index(drop=True)

    def _get_prediction_current_price(self, symbol: str, daily_df: pd.DataFrame) -> float:
        quote_price = self._get_prediction_realtime_price(symbol)
        try:
            from data.smart_monitor_tdx_data import SmartMonitorTDXDataFetcher

            fetcher = SmartMonitorTDXDataFetcher()
            minute_df = fetcher.get_kline_data(symbol, kline_type="minute5", limit=1)
            if minute_df is not None and not minute_df.empty:
                price = self._safe_float(minute_df.iloc[-1].get("收盘"))
                if (
                    price > 0
                    and self._prediction_kline_is_fresh(minute_df)
                    and self._prediction_price_matches(price, quote_price or self._safe_float(daily_df.iloc[-1].get("收盘")))
                ):
                    return price
                print(f"预测5分钟K当前价口径异常，使用其他价格源: symbol={symbol} quote={quote_price} latest={self._prediction_latest_snapshot(minute_df)}")

        except Exception as exc:
            print(f"预测当前价获取失败，使用日线收盘价兜底: symbol={symbol} error={type(exc).__name__}: {exc}")

        if quote_price > 0:
            return quote_price
        return self._safe_float(daily_df.iloc[-1].get("收盘"))

    def _get_prediction_realtime_price(self, symbol: str) -> float:
        quote = self._get_prediction_realtime_quote(symbol)
        if quote:
            return self._safe_float(quote.get("current_price"))
        return 0.0

    def _get_prediction_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        try:
            from data.smart_monitor_tdx_data import SmartMonitorTDXDataFetcher

            quote = SmartMonitorTDXDataFetcher().get_realtime_quote(symbol)
            if quote:
                return quote
        except Exception as exc:
            print(f"预测实时价获取失败，继续降级: symbol={symbol} error={type(exc).__name__}: {exc}")
        return {}

    def _build_prediction_price_limit(self, symbol: str, daily_df: pd.DataFrame) -> Dict[str, Any]:
        """构建未来480分钟涨跌幅限制规则。"""
        clean_symbol = self._clean_symbol(symbol)
        board = self._prediction_board(clean_symbol)
        listing_date = self._get_prediction_listing_date(clean_symbol)
        trading_day = self._listing_trading_day_index(daily_df, listing_date)
        no_limit_days = 1 if board == "bse" else 5

        if trading_day is not None and trading_day <= no_limit_days:
            board_name = {
                "bse": "北交所",
                "star": "科创板",
                "gem": "创业板",
                "main": "沪深主板",
            }.get(board, "A股")
            return {
                "price_limit_pct": None,
                "price_limit_days": 0,
                "price_limit_unrestricted": True,
                "price_limit_rule": f"{board_name}新股上市第{trading_day}个交易日不设价格涨跌幅限制",
                "listing_date": listing_date.strftime("%Y-%m-%d") if listing_date else None,
                "listing_trading_day": trading_day,
            }

        pct = self._infer_prediction_price_limit_pct(clean_symbol)
        return {
            "price_limit_pct": pct,
            "price_limit_days": 2,
            "price_limit_unrestricted": False,
            "price_limit_rule": f"未来480分钟按2个交易日、单日涨跌幅{pct * 100:.0f}%折算",
            "listing_date": listing_date.strftime("%Y-%m-%d") if listing_date else None,
            "listing_trading_day": trading_day,
        }

    def _prediction_board(self, symbol: str) -> str:
        clean_symbol = self._clean_symbol(symbol)
        if clean_symbol.startswith(("8", "4", "920")):
            return "bse"
        if clean_symbol.startswith("688"):
            return "star"
        if clean_symbol.startswith("300"):
            return "gem"
        return "main"

    def _infer_prediction_price_limit_pct(self, symbol: str) -> float:
        """按A股交易板块推断常规单日涨跌幅限制。"""
        clean_symbol = self._clean_symbol(symbol)
        quote = self._get_prediction_realtime_quote(clean_symbol)
        stock_name = str(quote.get("name", "") if quote else "").upper()

        if "ST" in stock_name:
            return 0.05
        if self._prediction_board(clean_symbol) in {"star", "gem"}:
            return 0.20
        if self._prediction_board(clean_symbol) == "bse":
            return 0.30
        return 0.10

    @cached_call(
        "fundamental",
        key_builder=lambda self, symbol: ("prediction_listing_date", "v1", self._clean_symbol(symbol)),
        ttl=86400,
        stale_ttl=604800,
        cache_none=True,
    )
    def _get_prediction_listing_date(self, symbol: str) -> Optional[datetime]:
        """获取股票上市日期，用于识别新股无涨跌幅阶段。"""
        clean_symbol = self._clean_symbol(symbol)

        try:
            import akshare as ak

            stock_info = ak.stock_individual_info_em(symbol=clean_symbol)
            if stock_info is not None and not stock_info.empty:
                for _, row in stock_info.iterrows():
                    key = str(row.get("item", ""))
                    if key in {"上市时间", "上市日期"}:
                        parsed = self._parse_prediction_date(row.get("value"))
                        if parsed:
                            return parsed
        except Exception as exc:
            print(f"AkShare上市日期获取失败，继续降级: symbol={clean_symbol} error={type(exc).__name__}: {exc}")

        try:
            import os
            import tushare as ts

            token = os.getenv("TUSHARE_TOKEN", "")
            if token:
                ts.set_token(token)
                pro = ts.pro_api()
                ts_code = f"{clean_symbol}.SH" if clean_symbol.startswith(("6", "9")) else f"{clean_symbol}.SZ"
                df = pro.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,list_date")
                if df is not None and not df.empty:
                    parsed = self._parse_prediction_date(df.iloc[0].get("list_date"))
                    if parsed:
                        return parsed
        except Exception as exc:
            print(f"Tushare上市日期获取失败，使用默认涨跌幅规则: symbol={clean_symbol} error={type(exc).__name__}: {exc}")

        return None

    def _parse_prediction_date(self, value) -> Optional[datetime]:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if not text or text in {"-", "--", "None", "nan", "NaN"}:
            return None

        digits = re.sub(r"\D", "", text)
        for candidate, fmt in ((digits[:8], "%Y%m%d"), (text[:10], "%Y-%m-%d")):
            if not candidate:
                continue
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
        try:
            parsed = pd.to_datetime(text, errors="coerce")
            if pd.notna(parsed):
                return parsed.to_pydatetime()
        except Exception:
            pass
        return None

    def _listing_trading_day_index(self, daily_df: pd.DataFrame, listing_date: Optional[datetime]) -> Optional[int]:
        if listing_date is None or daily_df is None or daily_df.empty or "日期" not in daily_df.columns:
            return None

        dates = pd.to_datetime(daily_df["日期"], errors="coerce").dropna()
        if dates.empty:
            return None

        listing_day = listing_date.date()
        trading_dates = sorted({item.date() for item in dates if item.date() >= listing_day})
        if not trading_dates:
            return None
        return len(trading_dates)

    def _fetch_prediction_daily_data_tushare(self, symbol: str) -> pd.DataFrame:
        import os
        import tushare as ts

        token = os.getenv("TUSHARE_TOKEN", "")
        if not token:
            return pd.DataFrame()

        ts.set_token(token)
        pro = ts.pro_api()
        ts_code = f"{symbol}.SH" if symbol.startswith(("6", "9")) else f"{symbol}.SZ"
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=500)).strftime("%Y%m%d")
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.sort_values("trade_date").rename(columns={
            "trade_date": "日期",
            "open": "开盘",
            "high": "最高",
            "low": "最低",
            "close": "收盘",
            "vol": "成交量",
            "amount": "成交额",
        })
        return df.reset_index(drop=True)

    def _prediction_kline_is_usable(self, df: pd.DataFrame, quote_price: float = 0.0) -> bool:
        if df is None or df.empty:
            return False
        prepared = self._normalize_prediction_kline_for_check(df)
        if prepared.empty:
            return False
        latest = prepared.iloc[-1]
        close_price = self._safe_float(latest.get("收盘"))
        if close_price <= 0:
            return False
        if not self._prediction_kline_is_fresh(prepared):
            return False
        if quote_price > 0 and not self._prediction_price_matches(close_price, quote_price):
            return False
        return True

    def _normalize_prediction_kline_for_check(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        rename_map = {
            "High": "最高",
            "Low": "最低",
            "Close": "收盘",
            "Volume": "成交量",
            "Date": "日期",
            "high": "最高",
            "low": "最低",
            "close": "收盘",
            "volume": "成交量",
            "date": "日期",
            "trade_date": "日期",
        }
        temp = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
        if "日期" not in temp.columns or "收盘" not in temp.columns:
            return pd.DataFrame()
        temp["日期"] = pd.to_datetime(temp["日期"], errors="coerce")
        temp["收盘"] = pd.to_numeric(temp["收盘"], errors="coerce")
        return temp.dropna(subset=["日期", "收盘"]).sort_values("日期").reset_index(drop=True)

    def _prediction_kline_is_fresh(self, df: pd.DataFrame, max_stale_days: int = 20) -> bool:
        prepared = self._normalize_prediction_kline_for_check(df)
        if prepared.empty:
            return False
        latest_date = prepared.iloc[-1]["日期"].to_pydatetime()
        return (datetime.now() - latest_date).days <= max_stale_days

    def _prediction_price_matches(self, price: float, reference_price: float) -> bool:
        price = self._safe_float(price)
        reference_price = self._safe_float(reference_price)
        if price <= 0 or reference_price <= 0:
            return False
        ratio = price / reference_price
        return 0.65 <= ratio <= 1.35

    def _prediction_latest_snapshot(self, df: pd.DataFrame) -> Dict[str, Any]:
        prepared = self._normalize_prediction_kline_for_check(df)
        if prepared.empty:
            return {}
        latest = prepared.iloc[-1]
        return {
            "date": str(latest.get("日期")),
            "close": self._safe_float(latest.get("收盘")),
        }

    def _calculate_atr14(self, df: pd.DataFrame) -> float:
        prev_close = df["收盘"].shift(1)
        tr = pd.concat([
            df["最高"] - df["最低"],
            (df["最高"] - prev_close).abs(),
            (df["最低"] - prev_close).abs(),
        ], axis=1).max(axis=1)
        return self._safe_float(tr.tail(14).mean())

    def _build_pressure_candidates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        latest = df.iloc[-1]
        recent10 = df.tail(10)
        vol7 = df.tail(7)
        swing_low, swing_high = self._find_recent_up_swing(df)
        candidates = [
            {"price": recent10["最高"].max(), "source": "近期高点", "kind": "recent_high"},
            {"price": latest["BOLL_UP"], "source": "布林上轨", "kind": "boll_up"},
            {"price": vol7.loc[vol7["成交量"].idxmax(), "最高"], "source": "近7日天量高点", "kind": "vol_high"},
            {"price": self._previous_swing_high(df), "source": "前期结构高点", "kind": "structure_high"},
        ]
        if self._safe_float(latest["收盘"]) < self._safe_float(latest["MA20"]):
            candidates.append({"price": latest["MA20"], "source": "MA20", "kind": "ma20"})
        if swing_low is not None and swing_high is not None and swing_high > swing_low:
            diff = swing_high - swing_low
            for ratio in (0.382, 0.5, 0.618, 1.272):
                candidates.append({
                    "price": swing_low + diff * ratio,
                    "source": f"黄金分割{ratio}",
                    "kind": "fib_pressure",
                })
        candidates.extend(self._extension_pressure_candidates(df))
        return self._unique_candidates(candidates)

    def _build_support_candidates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        latest = df.iloc[-1]
        recent10 = df.tail(10)
        vol7 = df.tail(7)
        swing_high, swing_low = self._find_recent_down_swing(df)
        candidates = [
            {"price": recent10["最低"].min(), "source": "近期低点", "kind": "recent_low"},
            {"price": latest["BOLL_LOW"], "source": "布林下轨", "kind": "boll_low"},
            {"price": vol7.loc[vol7["成交量"].idxmax(), "最低"], "source": "近7日天量低点", "kind": "vol_low"},
            {"price": self._previous_swing_low(df), "source": "前期结构低点", "kind": "structure_low"},
        ]
        if self._safe_float(latest["收盘"]) > self._safe_float(latest["MA20"]):
            candidates.append({"price": latest["MA20"], "source": "MA20", "kind": "ma20"})
        if swing_high is not None and swing_low is not None and swing_high > swing_low:
            diff = swing_high - swing_low
            for ratio in (0.382, 0.5, 0.618):
                candidates.append({
                    "price": swing_high - diff * ratio,
                    "source": f"黄金分割{ratio}",
                    "kind": "fib_support",
                })
            for ratio in (0.272, 0.618):
                candidates.append({
                    "price": swing_low - diff * ratio,
                    "source": f"向下扩展{ratio}",
                    "kind": "fib_support",
                })
        candidates.extend(self._extension_support_candidates(df))
        return self._unique_candidates(candidates)

    def _select_pressure_candidate(self, df: pd.DataFrame, candidates: List[Dict[str, Any]], p_now: float, atr14: float) -> Optional[Dict[str, Any]]:
        threshold = atr14 * 0.15
        valid = []
        for candidate in candidates:
            price = self._safe_float(candidate.get("price"))
            if price <= p_now or abs(price - p_now) < threshold:
                continue
            checks = self._validate_level(df, price, "pressure", atr14)
            if checks["C"] or checks["B"] or checks["D"] or (checks["A"] and checks["B"]):
                item = dict(candidate)
                item.update(checks)
                valid.append(item)
        if not valid:
            return None
        return min(valid, key=lambda item: abs(item["price"] - p_now))

    def _select_support_candidate(self, df: pd.DataFrame, candidates: List[Dict[str, Any]], p_now: float, atr14: float) -> Optional[Dict[str, Any]]:
        threshold = atr14 * 0.3
        valid = []
        for candidate in candidates:
            price = self._safe_float(candidate.get("price"))
            if price >= p_now or abs(price - p_now) < threshold:
                continue
            checks = self._validate_level(df, price, "support", atr14)
            score = self._support_score(candidate, checks)
            if score <= 1:
                continue
            item = dict(candidate)
            item.update(checks)
            item["score"] = score
            valid.append(item)
        if not valid:
            return None

        max_score = max(item["score"] for item in valid)
        same_score = [item for item in valid if item["score"] == max_score]
        selected = max(same_score, key=lambda item: abs(p_now - item["price"]))
        if abs(p_now - selected["price"]) < atr14 * 0.8:
            far = [item for item in same_score if abs(p_now - item["price"]) >= atr14 * 0.8]
            if far:
                selected = max(far, key=lambda item: abs(p_now - item["price"]))
        return selected

    def _validate_level(self, df: pd.DataFrame, price: float, level_type: str, atr14: float) -> Dict[str, bool]:
        recent7 = df.tail(7)
        recent20 = df.tail(20)
        vol_ma20 = self._safe_float(df.iloc[-1].get("VOL_MA20"))
        touch_col = "最高" if level_type == "pressure" else "最低"
        reverse_col = "收盘"
        tolerance_short = price * 0.008
        tolerance_mid = price * 0.015

        near_all = df[(df[touch_col] - price).abs() <= tolerance_short]
        condition_a = False
        if not near_all.empty and vol_ma20 > 0:
            condition_a = bool((near_all["成交量"] >= vol_ma20 * 1.2).any())

        b_count = 0
        for _, row in recent7.iterrows():
            touched = abs(self._safe_float(row[touch_col]) - price) <= tolerance_short
            if not touched:
                continue
            if level_type == "pressure":
                reverse = self._safe_float(row[touch_col]) - min(self._safe_float(row["收盘"]), self._safe_float(row["最低"]))
            else:
                reverse = max(self._safe_float(row["收盘"]), self._safe_float(row["最高"])) - self._safe_float(row[touch_col])
            if reverse >= atr14 * 0.5:
                b_count += 1
        condition_b = b_count >= 2

        vol7_idx = recent7["成交量"].idxmax()
        vol7_row = recent7.loc[vol7_idx]
        c_level = self._safe_float(vol7_row["最高"] if level_type == "pressure" else vol7_row["最低"])
        condition_c = abs(c_level - price) <= max(tolerance_short, 0.01)

        d_touches = int(((recent20[touch_col] - price).abs() <= tolerance_mid).sum())
        box_move = (recent20["最高"].max() - recent20["最低"].min()) >= atr14 * 1.5
        condition_d = d_touches >= 3 and box_move

        return {"A": condition_a, "B": condition_b, "C": condition_c, "D": condition_d}

    def _support_score(self, candidate: Dict[str, Any], checks: Dict[str, bool]) -> int:
        kind = candidate.get("kind")
        if checks["D"]:
            return 5
        if checks["A"] and checks["B"]:
            return 4
        if kind == "ma20" and checks["B"]:
            return 3
        if kind in {"fib_support", "structure_low"} and checks["B"]:
            return 2
        if checks["B"]:
            return 2
        if checks["C"]:
            return 1
        return 0

    def _fallback_pressure(self, df: pd.DataFrame, p_now: float, atr14: float) -> Dict[str, float]:
        highs = sorted([self._safe_float(v) for v in df.tail(20)["最高"].tolist() if self._safe_float(v) > p_now])
        if highs:
            return {"price": highs[0]}
        return {"price": p_now + atr14}

    def _fallback_support(self, df: pd.DataFrame, p_now: float, atr14: float) -> Dict[str, float]:
        lows = sorted([self._safe_float(v) for v in df.tail(20)["最低"].tolist() if self._safe_float(v) < p_now], reverse=True)
        if lows:
            return {"price": lows[0]}
        return {"price": max(p_now - atr14, 0.01)}

    def _find_recent_up_swing(self, df: pd.DataFrame) -> tuple:
        recent = df.tail(30).reset_index(drop=True)
        high_idx = int(recent["最高"].idxmax())
        before = recent.iloc[:high_idx + 1]
        if before.empty:
            return None, None
        return self._safe_float(before["最低"].min()), self._safe_float(recent.loc[high_idx, "最高"])

    def _find_recent_down_swing(self, df: pd.DataFrame) -> tuple:
        recent = df.tail(30).reset_index(drop=True)
        low_idx = int(recent["最低"].idxmin())
        before = recent.iloc[:low_idx + 1]
        if before.empty:
            return None, None
        return self._safe_float(before["最高"].max()), self._safe_float(recent.loc[low_idx, "最低"])

    def _previous_swing_high(self, df: pd.DataFrame) -> float:
        return self._safe_float(df.tail(30).head(20)["最高"].max())

    def _previous_swing_low(self, df: pd.DataFrame) -> float:
        return self._safe_float(df.tail(30).head(20)["最低"].min())

    def _extension_pressure_candidates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        rows = df.tail(5)
        return [{"price": row["最高"], "source": "顺延高点", "kind": "extension_high"} for _, row in rows.iterrows()]

    def _extension_support_candidates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        rows = df.tail(5)
        return [{"price": row["最低"], "source": "顺延低点", "kind": "extension_low"} for _, row in rows.iterrows()]

    def _unique_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique = []
        seen = set()
        for candidate in candidates:
            price = self._safe_float(candidate.get("price"))
            if price <= 0:
                continue
            key = round(price, 2)
            if key in seen:
                continue
            item = dict(candidate)
            item["price"] = price
            unique.append(item)
            seen.add(key)
        return unique

    def _safe_float(self, value) -> float:
        """安全转换为float，处理NaN"""
        parsed = self._parse_number(value)
        return parsed if parsed is not None else 0.0
    
    def _clean_nan(self, data):
        """递归清理数据中的NaN值"""
        import math
        if isinstance(data, dict):
            return {k: self._clean_nan(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_nan(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return 0.0
            return data
        else:
            return data

    def _get_macd_signal(self, value: float) -> str:
        if value > 0:
            return 'buy'
        elif value < 0:
            return 'sell'
        else:
            return 'hold'

    def _get_rsi_signal(self, value: float) -> str:
        if value < 30:
            return 'buy'
        elif value > 70:
            return 'sell'
        else:
            return 'hold'

    def _get_kdj_signal(self, value: float) -> str:
        if value < 20:
            return 'buy'
        elif value > 80:
            return 'sell'
        else:
            return 'hold'

    def _get_ma_signal(self, ma_value: float, current_price: float) -> str:
        if current_price > ma_value:
            return 'buy'
        elif current_price < ma_value:
            return 'sell'
        else:
            return 'hold'

    def _get_pe_rank(self, value: float) -> str:
        if value <= 15:
            return 'excellent'
        elif value <= 30:
            return 'good'
        elif value <= 50:
            return 'average'
        else:
            return 'poor'

    def _get_pb_rank(self, value: float) -> str:
        if value <= 1.5:
            return 'excellent'
        elif value <= 3:
            return 'good'
        elif value <= 5:
            return 'average'
        else:
            return 'poor'

    def _get_roe_rank(self, value: float) -> str:
        if value >= 20:
            return 'excellent'
        elif value >= 10:
            return 'good'
        elif value >= 5:
            return 'average'
        else:
            return 'poor'

    def _get_debt_rank(self, value: float) -> str:
        if value <= 30:
            return 'excellent'
        elif value <= 50:
            return 'good'
        elif value <= 70:
            return 'average'
        else:
            return 'poor'

    def _get_dividend_rank(self, value: float) -> str:
        if value >= 4:
            return 'excellent'
        elif value >= 2:
            return 'good'
        elif value >= 1:
            return 'average'
        else:
            return 'poor'

    def _get_growth_rank(self, value: float) -> str:
        if value >= 20:
            return 'excellent'
        elif value >= 10:
            return 'good'
        elif value >= 0:
            return 'average'
        else:
            return 'poor'

    def _get_profit_rank(self, value: float) -> str:
        if value > 1000000000:
            return 'excellent'
        elif value > 100000000:
            return 'good'
        elif value > 0:
            return 'average'
        else:
            return 'poor'

    def _get_margin_rank(self, value: float) -> str:
        if value >= 30:
            return 'excellent'
        elif value >= 20:
            return 'good'
        elif value >= 10:
            return 'average'
        else:
            return 'poor'

    def _get_eps_rank(self, value: float) -> str:
        if value >= 2:
            return 'excellent'
        elif value >= 1:
            return 'good'
        elif value >= 0.5:
            return 'average'
        else:
            return 'poor'

    def _get_bvps_rank(self, value: float) -> str:
        if value >= 10:
            return 'excellent'
        elif value >= 5:
            return 'good'
        elif value >= 2:
            return 'average'
        else:
            return 'poor'

    def _get_current_ratio_rank(self, value: float) -> str:
        if 2 <= value <= 3:
            return 'excellent'
        elif 1.5 <= value <= 4:
            return 'good'
        elif 1 <= value <= 5:
            return 'average'
        else:
            return 'poor'

    def _get_quick_ratio_rank(self, value: float) -> str:
        if 1 <= value <= 2:
            return 'excellent'
        elif 0.8 <= value <= 2.5:
            return 'good'
        elif 0.5 <= value <= 3:
            return 'average'
        else:
            return 'poor'

    def _get_turnover_rank(self, value: float) -> str:
        if value >= 10:
            return 'excellent'
        elif value >= 5:
            return 'good'
        elif value >= 2:
            return 'average'
        else:
            return 'poor'

    def _get_institutional_rank(self, value: float) -> str:
        if value >= 50:
            return 'excellent'
        elif value >= 30:
            return 'good'
        elif value >= 10:
            return 'average'
        else:
            return 'poor'


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试股票分析模块")
    print("=" * 60)

    analyzer = StockAnalyzer()
    
    print("\n测试技术分析...")
    success, tech_data, msg = analyzer.get_technical_analysis("000001", days_ago=60)
    print(f"结果: {msg}")
    if success and tech_data:
        print(f"股票: {tech_data.get('name')}")
        print(f"当前价: {tech_data.get('current_price')}")
        print(f"指标数: {len(tech_data.get('indicators', []))}")

    print("\n测试基本面分析...")
    success, fund_data, msg = analyzer.get_fundamental_analysis("000001")
    print(f"结果: {msg}")
    if success and fund_data:
        print(f"股票: {fund_data.get('name')}")
        print(f"行业: {fund_data.get('industry')}")
        print(f"指标数: {len(fund_data.get('metrics', []))}")
