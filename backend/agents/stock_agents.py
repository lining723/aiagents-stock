"""
股票AI分析师
专注于股票多维度深度分析
"""

from agents.deepseek_client import DeepSeekClient
from typing import Dict, Any, Optional
import time
import config.config as config


class StockAgents:
    """股票AI分析师"""

    def __init__(self, model=None):
        self.model = model or config.DEFAULT_MODEL_NAME
        self.deepseek_client = DeepSeekClient(model=self.model)
        print(f"[股票分析] AI分析师系统初始化 (模型: {self.model})")

    def _format_technical_data(self, tech_data: Dict) -> str:
        """格式化技术分析数据"""
        if not tech_data:
            return ""

        text = "【技术面数据】\n"
        text += f"股票名称: {tech_data.get('name', 'N/A')}\n"
        text += f"当前价格: {tech_data.get('current_price', 0):.2f}\n"
        text += f"涨跌幅: {tech_data.get('change_percent', 0):.2f}%\n\n"

        text += "【技术指标】\n"
        indicators = tech_data.get('indicators', [])
        for ind in indicators:
            name = ind.get('name', '')
            value = ind.get('value', 0)
            signal = ind.get('signal', '')
            desc = ind.get('description', '')
            signal_text = {'buy': '买入', 'sell': '卖出', 'hold': '观望'}.get(signal, signal)
            text += f"- {name}: {value:.2f} ({signal_text}) - {desc}\n"

        return text

    def _format_fundamental_data(self, fund_data: Dict) -> str:
        """格式化基本面分析数据"""
        if not fund_data:
            return ""

        text = "【基本面数据】\n"
        text += f"股票名称: {fund_data.get('name', 'N/A')}\n"
        text += f"所属行业: {fund_data.get('industry', 'N/A')}\n"
        text += f"总市值: {fund_data.get('market_cap', 0):,.0f} 元\n\n"

        text += "【核心指标】\n"
        metrics = fund_data.get('metrics', [])
        for metric in metrics:
            name = metric.get('name', '')
            value = metric.get('value', 0)
            unit = metric.get('unit', '')
            rank = metric.get('rank', '')
            desc = metric.get('description', '')
            rank_text = {'excellent': '优秀', 'good': '良好', 'average': '一般', 'poor': '较差'}.get(rank, rank)
            text += f"- {name}: {value:.2f}{unit} ({rank_text}) - {desc}\n"

        return text

    def comprehensive_stock_analyst(
        self,
        symbol: str,
        tech_data: Optional[Dict] = None,
        fund_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        综合股票分析师 - 基于技术面和基本面数据进行深度分析

        Args:
            symbol: 股票代码
            tech_data: 技术分析数据
            fund_data: 基本面分析数据

        Returns:
            AI分析结果
        """
        print("🤖 综合股票分析师正在分析...")
        time.sleep(1)

        tech_text = self._format_technical_data(tech_data) if tech_data else "暂无技术面数据"
        fund_text = self._format_fundamental_data(fund_data) if fund_data else "暂无基本面数据"

        prompt = f"""你是一名资深的股票投资分析师，拥有15年以上的A股市场投资研究经验。请基于以下提供的股票数据，进行专业、全面、深入的分析。

股票代码: {symbol}

{tech_text}

{fund_text}

请基于以上数据，按照以下结构撰写一份专业的股票分析报告：

## 一、股票概况与最新走势
- 简要介绍股票基本情况
- 分析近期价格表现和趋势
- 结合技术指标给出初步判断

## 二、技术面深度分析
- MACD、RSI、KDJ等指标的详细解读
- 均线系统分析（MA5、MA20等）
- 技术形态判断和买卖信号识别
- 给出技术面的操作建议

## 三、基本面综合评估
- 估值水平分析（PE、PB）
- 盈利能力评价（毛利率、净利率、ROE）
- 成长能力分析（营收增长、净利润增长）
- 偿债能力评估（资产负债率、流动比率、速动比率）
- 营运能力分析（存货周转、应收账款周转）
- 资金动向解读（机构持仓、北向资金）

## 四、多维度综合评分
- 技术面评分（0-100分）及理由
- 基本面评分（0-100分）及理由
- 综合评分（0-100分）及理由
- 给出投资评级（强烈推荐/推荐/持有/观望/回避）

## 五、风险提示与机会分析
- 主要投资风险（3-5点）
- 潜在投资机会（3-5点）
- 关键关注因素

## 六、操作建议与策略
- 建议仓位配置
- 入场时机参考
- 止损止盈设置
- 中长期投资策略
- 短线交易建议（如适用）

请用专业、客观、理性的语言进行分析，避免过度乐观或悲观。报告要结构清晰、逻辑严密、数据详实、具有可操作性。使用Markdown格式输出。"""

        messages = [
            {"role": "system", "content": "你是一名专业的股票投资分析师，擅长技术分析和基本面分析的结合应用。"},
            {"role": "user", "content": prompt}
        ]

        try:
            analysis = self.deepseek_client.call_api(messages, max_tokens=6000)
            print("  ✓ 综合股票分析师分析完成")

            return {
                "agent_name": "综合股票分析师",
                "agent_role": "基于技术面和基本面数据进行多维度深度分析",
                "analysis": analysis,
                "focus_areas": ["技术面分析", "基本面分析", "综合评分", "风险提示", "操作建议"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"  ✗ 综合股票分析师分析失败: {str(e)}")
            raise


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试股票AI分析师系统")
    print("=" * 60)

    # 创建模拟数据
    test_tech_data = {
        'name': '示例股票',
        'current_price': 15.68,
        'change_percent': 2.35,
        'indicators': [
            {'name': 'MACD', 'value': 0.25, 'signal': 'buy', 'description': 'MACD金叉'},
            {'name': 'RSI', 'value': 55.0, 'signal': 'hold', 'description': '中性区间'},
        ]
    }

    test_fund_data = {
        'name': '示例股票',
        'industry': '计算机应用',
        'market_cap': 15000000000,
        'metrics': [
            {'name': '市盈率(PE)', 'value': 18.5, 'unit': '倍', 'rank': 'good', 'description': '合理估值'},
            {'name': '净资产收益率(ROE)', 'value': 15.2, 'unit': '%', 'rank': 'excellent', 'description': '盈利能力较强'},
        ]
    }

    agents = StockAgents()

    print("\n测试综合股票分析师...")
    result = agents.comprehensive_stock_analyst("000001", test_tech_data, test_fund_data)
    print(f"分析师: {result['agent_name']}")
    print(f"分析内容长度: {len(result['analysis'])} 字符")
