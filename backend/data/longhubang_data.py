"""
智瞰龙虎数据采集模块
使用StockAPI获取龙虎榜数据
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import warnings
from utils.redis_cache import redis_cache

warnings.filterwarnings('ignore')


class LonghubangDataFetcher:
    """龙虎榜数据获取类"""
    
    def __init__(self, api_key=None):
        """
        初始化数据获取器
        
        Args:
            api_key: StockAPI的API密钥（可选，普通请求每日免费1000次）
        """
        print("[智瞰龙虎] 龙虎榜数据获取器初始化...")
        self.base_urls = [
            "http://lhb-api.ws4.cn/v1",
            "https://api-lhb.zhongdu.net",
        ]
        self.api_key = api_key
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2  # 重试延迟（秒）
        self.request_delay = 0.025  # 请求间隔（秒），40次/秒 = 0.025秒/次
        self.logger = logging.getLogger(__name__)
    
    def _safe_request(self, url, params=None):
        """
        安全的HTTP请求，包含重试机制
        
        Args:
            url: 请求URL
            params: 请求参数
            
        Returns:
            dict: 响应数据
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                
                # 添加请求延迟，遵守40次/秒的限制
                time.sleep(self.request_delay)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 20000:
                        return data
                    else:
                        print(f"    API返回错误: {data.get('msg', '未知错误')}")
                        return None
                else:
                    print(f"    HTTP错误: {response.status_code}")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"    请求失败，{self.retry_delay}秒后重试... (尝试 {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    print(f"    请求失败，已达最大重试次数: {e}")
                    return None
        
        return None
    
    def get_longhubang_data(self, date):
        """
        获取指定日期的龙虎榜数据
        
        Args:
            date: 日期，格式为 YYYY-MM-DD，如 "2023-03-21"
            
        Returns:
            dict: 龙虎榜数据
        """
        cache_result = redis_cache.get_or_set(
            "longhubang",
            ("date", date),
            lambda: self._fetch_longhubang_data_uncached(date),
            is_valid=lambda result: bool(result and result.get("data")),
        )
        if cache_result.hit:
            status = "过期缓存兜底" if cache_result.stale else "缓存命中"
            print(f"[智瞰龙虎] {date} 龙虎榜数据{status}: {len(cache_result.value.get('data', []))} 条")
        return cache_result.value

    def _fetch_longhubang_data_uncached(self, date):
        """从外部源获取指定日期的龙虎榜数据。"""
        print(f"[智瞰龙虎] 获取 {date} 的龙虎榜数据...")
        
        params = {'date': date}

        for base_url in self.base_urls:
            url = f"{base_url}/youzi/all"
            result = self._safe_request(url, params)
            if result and result.get('data'):
                print(f"    ✓ 成功获取 {len(result['data'])} 条龙虎榜记录")
                return result

        fallback = self._get_longhubang_data_akshare(date)
        if fallback and fallback.get('data'):
            print(f"    ✓ 使用 AkShare 兜底获取 {len(fallback['data'])} 条龙虎榜记录")
            return fallback

        print(f"    ✗ 未获取到数据")
        return None
    
    def get_longhubang_data_range(self, start_date, end_date):
        """
        获取日期范围内的龙虎榜数据
        
        Args:
            start_date: 开始日期，格式为 YYYY-MM-DD
            end_date: 结束日期，格式为 YYYY-MM-DD
            
        Returns:
            list: 龙虎榜数据列表
        """
        print(f"[智瞰龙虎] 获取 {start_date} 至 {end_date} 的龙虎榜数据...")
        
        all_data = []
        
        # 转换日期
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 跳过周末
            if current_date.weekday() < 5:  # 0-4表示周一到周五
                result = self.get_longhubang_data(date_str)
                if result and result.get('data'):
                    all_data.extend(result['data'])
            
            # 下一天
            current_date += timedelta(days=1)
        
        print(f"[智瞰龙虎] ✓ 共获取 {len(all_data)} 条记录")
        return all_data
    
    def get_recent_days_data(self, days=5):
        """
        获取最近N个交易日的龙虎榜数据
        
        Args:
            days: 天数（默认5天）
            
        Returns:
            list: 龙虎榜数据列表
        """
        all_data = []
        current_date = datetime.now()
        collected_days = 0
        checked_days = 0
        max_lookback_days = max(days * 5, 10)

        while collected_days < days and checked_days < max_lookback_days:
            if current_date.weekday() < 5:
                result = self.get_longhubang_data(current_date.strftime('%Y-%m-%d'))
                if result and result.get('data'):
                    all_data.extend(result['data'])
                    collected_days += 1
            current_date -= timedelta(days=1)
            checked_days += 1

        print(f"[智瞰龙虎] ✓ 共获取 {len(all_data)} 条记录")
        return all_data

    def _get_longhubang_data_akshare(self, date):
        """
        使用 AkShare 作为兜底源获取龙虎榜数据。
        优先取东方财富席位级明细，失败后退化到日度汇总。
        """
        date_compact = date.replace('-', '')

        try:
            import akshare as ak

            detail_df = ak.stock_lhb_detail_em(start_date=date_compact, end_date=date_compact)
            records = self._convert_em_detail_to_records(detail_df, date)
            if records:
                return {
                    'code': 20000,
                    'msg': 'ok',
                    'data': records,
                    'source': 'akshare_eastmoney',
                }
        except Exception as e:
            self.logger.warning(f"AkShare 东方财富龙虎榜详情兜底失败 {date}: {type(e).__name__}: {e}")

        try:
            import akshare as ak

            daily_df = ak.stock_lhb_detail_daily_sina(date=date_compact)
            records = self._convert_sina_daily_to_records(daily_df, date)
            if records:
                return {
                    'code': 20000,
                    'msg': 'ok',
                    'data': records,
                    'source': 'akshare_sina',
                }
        except Exception as e:
            self.logger.warning(f"AkShare 新浪龙虎榜兜底失败 {date}: {type(e).__name__}: {e}")

        return None

    def _convert_em_detail_to_records(self, detail_df, date):
        """将东方财富龙虎榜详情转换为当前系统兼容的记录结构。"""
        if detail_df is None or detail_df.empty:
            return []

        records = []
        trade_date = pd.to_datetime(date).date()
        filtered_df = detail_df.copy()
        if '上榜日' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['上榜日'] == trade_date]

        if filtered_df.empty:
            return []

        try:
            import akshare as ak
        except Exception:
            ak = None

        for _, row in filtered_df.iterrows():
            stock_code = str(row.get('代码', '')).zfill(6)
            stock_name = row.get('名称', '')
            reason = row.get('上榜原因') or row.get('解读') or ''
            trade_date_compact = pd.to_datetime(row.get('上榜日', trade_date)).strftime('%Y%m%d')

            detail_frames = []
            if ak is not None:
                for flag in ('买入', '卖出'):
                    try:
                        seat_df = ak.stock_lhb_stock_detail_em(
                            symbol=stock_code,
                            date=trade_date_compact,
                            flag=flag,
                        )
                        if seat_df is not None and not seat_df.empty:
                            detail_frames.append(seat_df)
                    except Exception as e:
                        self.logger.warning(
                            f"AkShare 个股席位详情失败 {stock_code} {trade_date_compact} {flag}: "
                            f"{type(e).__name__}: {e}"
                        )

            if detail_frames:
                seat_df = pd.concat(detail_frames, ignore_index=True)
                seat_df['交易营业部名称'] = seat_df['交易营业部名称'].fillna('未知营业部')
                seat_df['类型'] = seat_df['类型'].fillna('')
                for col in ('买入金额', '卖出金额', '净额'):
                    seat_df[col] = pd.to_numeric(seat_df[col], errors='coerce').fillna(0.0)

                grouped = seat_df.groupby('交易营业部名称', as_index=False).agg({
                    '买入金额': 'sum',
                    '卖出金额': 'sum',
                    '净额': 'sum',
                    '类型': 'first',
                })

                for _, seat in grouped.iterrows():
                    yyb = str(seat.get('交易营业部名称', '')).strip() or '未知营业部'
                    seat_type = str(seat.get('类型', '')).strip()
                    yzmc = f"{yyb}({seat_type})" if seat_type else yyb
                    records.append({
                        'rq': date,
                        'gpdm': stock_code,
                        'gpmc': stock_name,
                        'yzmc': yzmc,
                        'yyb': yyb,
                        'sblx': reason,
                        'mrje': float(seat.get('买入金额', 0) or 0),
                        'mcje': float(seat.get('卖出金额', 0) or 0),
                        'jlrje': float(seat.get('净额', 0) or 0),
                        'gl': reason,
                    })
                continue

            # 如果席位明细也拿不到，至少保留股票级汇总，避免整天数据直接为空
            buy_amount = float(row.get('龙虎榜买入额', 0) or 0)
            sell_amount = float(row.get('龙虎榜卖出额', 0) or 0)
            net_inflow = float(row.get('龙虎榜净买额', 0) or 0)
            records.append({
                'rq': date,
                'gpdm': stock_code,
                'gpmc': stock_name,
                'yzmc': '龙虎榜汇总',
                'yyb': '龙虎榜汇总',
                'sblx': reason,
                'mrje': buy_amount,
                'mcje': sell_amount,
                'jlrje': net_inflow,
                'gl': reason,
            })

        return records

    def _convert_sina_daily_to_records(self, daily_df, date):
        """将新浪龙虎榜日度详情退化映射到兼容结构。"""
        if daily_df is None or daily_df.empty:
            return []

        records = []
        for _, row in daily_df.iterrows():
            stock_code = str(row.get('股票代码', '')).zfill(6)
            stock_name = row.get('股票名称', '')
            indicator = row.get('指标', '') or ''
            amount = pd.to_numeric(row.get('成交额', 0), errors='coerce')
            amount = 0.0 if pd.isna(amount) else float(amount)

            records.append({
                'rq': date,
                'gpdm': stock_code,
                'gpmc': stock_name,
                'yzmc': '新浪龙虎榜汇总',
                'yyb': '新浪龙虎榜汇总',
                'sblx': indicator,
                'mrje': amount,
                'mcje': 0.0,
                'jlrje': amount,
                'gl': indicator,
            })

        return records
    
    def parse_to_dataframe(self, data_list):
        """
        将龙虎榜数据转换为DataFrame
        
        Args:
            data_list: 龙虎榜数据列表
            
        Returns:
            pd.DataFrame: 数据框
        """
        if not data_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(data_list)
        
        # 重命名列
        column_mapping = {
            'yzmc': '游资名称',
            'yyb': '营业部',
            'sblx': '榜单类型',
            'gpdm': '股票代码',
            'gpmc': '股票名称',
            'mrje': '买入金额',
            'mcje': '卖出金额',
            'jlrje': '净流入金额',
            'rq': '日期',
            'gl': '概念'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 转换数据类型
        numeric_columns = ['买入金额', '卖出金额', '净流入金额']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 排序
        if '净流入金额' in df.columns:
            df = df.sort_values('净流入金额', ascending=False)
        
        return df
    
    def analyze_data_summary(self, data_list):
        """
        分析龙虎榜数据，生成摘要统计
        
        Args:
            data_list: 龙虎榜数据列表
            
        Returns:
            dict: 统计摘要
        """
        if not data_list:
            return {}
        
        df = self.parse_to_dataframe(data_list)
        
        summary = {
            'total_records': len(df),
            'total_stocks': df['股票代码'].nunique() if '股票代码' in df.columns else 0,
            'total_youzi': df['游资名称'].nunique() if '游资名称' in df.columns else 0,
            'total_buy_amount': df['买入金额'].sum() if '买入金额' in df.columns else 0,
            'total_sell_amount': df['卖出金额'].sum() if '卖出金额' in df.columns else 0,
            'total_net_inflow': df['净流入金额'].sum() if '净流入金额' in df.columns else 0,
        }
        
        # Top游资排名
        if '游资名称' in df.columns and '净流入金额' in df.columns:
            top_youzi = df.groupby('游资名称')['净流入金额'].sum().sort_values(ascending=False)
            summary['top_youzi'] = top_youzi.head(10).to_dict()
        
        # Top股票排名
        if '股票代码' in df.columns and '净流入金额' in df.columns:
            top_stocks = df.groupby(['股票代码', '股票名称'])['净流入金额'].sum().sort_values(ascending=False)
            summary['top_stocks'] = [
                {'code': code, 'name': name, 'net_inflow': amount}
                for (code, name), amount in top_stocks.head(20).items()
            ]
        
        # 热门概念统计
        if '概念' in df.columns:
            all_concepts = []
            for concepts in df['概念'].dropna():
                all_concepts.extend([c.strip() for c in str(concepts).split(',')])
            
            from collections import Counter
            concept_counter = Counter(all_concepts)
            summary['hot_concepts'] = dict(concept_counter.most_common(20))
        
        return summary
    
    def format_data_for_ai(self, data_list, summary=None):
        """
        将龙虎榜数据格式化为适合AI分析的文本格式
        
        Args:
            data_list: 龙虎榜数据列表
            summary: 统计摘要（可选）
            
        Returns:
            str: 格式化的文本
        """
        if not data_list:
            return "暂无龙虎榜数据"
        
        df = self.parse_to_dataframe(data_list)
        
        if summary is None:
            summary = self.analyze_data_summary(data_list)
        
        text_parts = []
        
        # 总体概况
        text_parts.append(f"""
【龙虎榜总体概况】
数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
记录总数: {summary.get('total_records', 0)}
涉及股票: {summary.get('total_stocks', 0)} 只
涉及游资: {summary.get('total_youzi', 0)} 个
总买入金额: {summary.get('total_buy_amount', 0):,.2f} 元
总卖出金额: {summary.get('total_sell_amount', 0):,.2f} 元
净流入金额: {summary.get('total_net_inflow', 0):,.2f} 元
""")
        
        # Top游资
        if summary.get('top_youzi'):
            text_parts.append("\n【活跃游资 TOP10】")
            for idx, (name, amount) in enumerate(summary['top_youzi'].items(), 1):
                text_parts.append(f"{idx}. {name}: {amount:,.2f} 元")
        
        # Top股票
        if summary.get('top_stocks'):
            text_parts.append("\n【资金净流入 TOP20股票】")
            for idx, stock in enumerate(summary['top_stocks'], 1):
                text_parts.append(
                    f"{idx}. {stock['name']}({stock['code']}): {stock['net_inflow']:,.2f} 元"
                )
        
        # 热门概念
        if summary.get('hot_concepts'):
            text_parts.append("\n【热门概念 TOP20】")
            for idx, (concept, count) in enumerate(list(summary['hot_concepts'].items())[:20], 1):
                text_parts.append(f"{idx}. {concept}: {count} 次")
        
        # 详细交易记录（前50条）
        text_parts.append("\n【详细交易记录 TOP50】")
        for idx, row in df.head(50).iterrows():
            text_parts.append(
                f"{row.get('游资名称', 'N/A')} | "
                f"{row.get('股票名称', 'N/A')}({row.get('股票代码', 'N/A')}) | "
                f"买入:{row.get('买入金额', 0):,.0f} "
                f"卖出:{row.get('卖出金额', 0):,.0f} "
                f"净流入:{row.get('净流入金额', 0):,.0f} | "
                f"日期:{row.get('日期', 'N/A')}"
            )
        
        return "\n".join(text_parts)


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎数据采集模块")
    print("=" * 60)
    
    fetcher = LonghubangDataFetcher()
    
    # 测试获取单日数据
    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    result = fetcher.get_longhubang_data(date)
    
    if result and result.get('data'):
        # 分析数据
        summary = fetcher.analyze_data_summary(result['data'])
        
        print("\n" + "=" * 60)
        print("数据采集成功！")
        print("=" * 60)
        
        # 格式化输出
        formatted_text = fetcher.format_data_for_ai(result['data'], summary)
        print(formatted_text[:2000])  # 显示前2000字符
        print(f"\n... (总长度: {len(formatted_text)} 字符)")
    else:
        print("\n数据采集失败")
