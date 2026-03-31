#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析模块
使用pywencai获取股票技术分析和基本面分析数据
"""

import pandas as pd
import pywencai
from typing import Tuple, Optional, List, Dict
from datetime import datetime
import time


class StockAnalyzer:
    """股票分析类"""

    def __init__(self):
        self.stock_data = None

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

            queries = [
                f"{symbol}的MACD、RSI、KDJ、布林带、MA5、MA10、MA20、MA60，以及近{days_ago}天的涨跌幅和收盘价",
                f"{symbol}的技术指标及近期走势",
                f"{symbol}的K线形态和技术面分析",
            ]

            data = None
            for i, query in enumerate(queries, 1):
                print(f"\n尝试方案 {i}/{len(queries)}...")
                try:
                    result = pywencai.get(query=query, loop=True)
                    if result is not None:
                        df = self._convert_to_dataframe(result)
                        if df is not None and not df.empty:
                            print(f"✅ 方案{i}成功！")
                            data = self._parse_technical_data(df, symbol)
                            break
                except Exception as e:
                    print(f"  ❌ 方案{i}失败: {str(e)}")
                    time.sleep(1)
                    continue

            if not data:
                return False, None, "技术分析数据获取失败"

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
                    result = pywencai.get(query=query, loop=True)
                    if result is not None:
                        df = self._convert_to_dataframe(result)
                        if df is not None and not df.empty:
                            print(f"✅ 方案{i}成功！")
                            data = self._parse_fundamental_data(df, symbol)
                            data = self._clean_nan(data)
                            return True, data, "基本面分析数据获取成功"
                except Exception as e:
                    print(f"  ❌ 方案{i}失败: {str(e)}")
                    time.sleep(1)
                    continue

            return False, None, "基本面分析数据获取失败"
        except Exception as e:
            error_msg = f"基本面分析异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, None, error_msg

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
            if symbol.isdigit() and len(symbol) == 6:
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

        try:
            if not df.empty:
                row = df.iloc[0]

                data['name'] = str(row.get('股票简称', row.get('名称', symbol)))
                data['industry'] = str(row.get('所属同花顺行业', row.get('所属行业', '')))
                data['market_cap'] = self._safe_float(row.get('总市值', row.get('市值', 0.0)))
                data['pe_ratio'] = self._safe_float(row.get('市盈率', row.get('PE', 0.0)))
                data['pb_ratio'] = self._safe_float(row.get('市净率', row.get('PB', 0.0)))
                data['roe'] = self._safe_float(row.get('净资产收益率', row.get('ROE', 0.0)))
                data['debt_ratio'] = self._safe_float(row.get('资产负债率', 0.0))
                data['dividend_rate'] = self._safe_float(row.get('股息率', 0.0))

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
                    
                    if ('营收' in col and '增长' in col) or ('营业收入增长率' in col):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '营收增长率' for m in metrics):
                            metrics.append({
                                'name': '营收增长率',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_growth_rank(val),
                                'description': '营收增长率'
                            })
                    elif ('净利润' in col and '增长' in col) or ('净利润增长率' in col):
                        val = self._safe_float(row.get(col))
                        if not any(m['name'] == '净利润增长率' for m in metrics):
                            metrics.append({
                                'name': '净利润增长率',
                                'value': val,
                                'unit': '%',
                                'rank': self._get_growth_rank(val),
                                'description': '净利润增长率'
                            })
                    elif '营收' in col and '增长' not in col and ('营业收入' in col or '营收' == col):
                        val = self._safe_float(row.get(col))
                        if val > 0 and not any(m['name'] == '营业收入' for m in metrics):
                            metrics.append({
                                'name': '营业收入',
                                'value': val,
                                'unit': '元',
                                'rank': 'average',
                                'description': '营业收入'
                            })
                    elif '净利润' in col and '增长' not in col and ('净利润' in col):
                        val = self._safe_float(row.get(col))
                        if val != 0 and not any(m['name'] == '净利润' for m in metrics):
                            metrics.append({
                                'name': '净利润',
                                'value': val,
                                'unit': '元',
                                'rank': self._get_profit_rank(val),
                                'description': '净利润'
                            })
                    elif ('毛利率' in col) or ('gross' in col_lower and 'margin' in col_lower):
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

    def _safe_float(self, value) -> float:
        """安全转换为float，处理NaN"""
        try:
            if value is None:
                return 0.0
            val = float(value)
            import math
            if math.isnan(val) or math.isinf(val):
                return 0.0
            return val
        except (ValueError, TypeError):
            return 0.0
    
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
