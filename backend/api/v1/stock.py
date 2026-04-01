from fastapi import APIRouter, HTTPException
from typing import List
import sys
import os
import pandas as pd

from schemas.stock import (
    ValueStockRequest,
    MainForceStockRequest,
    StockInfo,
    StockListResponse
)
from schemas.response import SuccessResponse
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["选股模块"])


def convert_df_to_stock_info(df) -> List[StockInfo]:
    """将 DataFrame 转换为 StockInfo 列表"""
    stocks = []
    if df is None or df.empty:
        return stocks
    
    def get_val(row, keys, default=0):
        for k in keys:
            # 1. 优先尝试精确匹配
            if k in row.index:
                val = row[k]
                if not pd.isna(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            
            # 2. 尝试前缀/包含匹配（应对问财的动态日期后缀如：市盈率(pe)[20260331]）
            for col in row.index:
                if isinstance(col, str) and (col.startswith(k) or k in col):
                    # 避免将预测值误认为当前值
                    if '预测' in col and '预测' not in k:
                        continue
                    val = row[col]
                    if not pd.isna(val):
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
        return default

    for _, row in df.iterrows():
        # 提取市值，并标准化单位为元
        market_cap_val = get_val(row, ['总市值', 'a股市值', '流通市值'])
        # 如果数值小于 10万，我们认为其单位为"亿"，需转换为"元"以适配前端
        if market_cap_val and market_cap_val < 100000:
            market_cap_val = market_cap_val * 100000000

        stock = StockInfo(
            symbol=str(row.get('股票代码', row.get('代码', 'N/A'))),
            name=str(row.get('股票简称', row.get('名称', 'N/A'))),
            pe_ratio=get_val(row, ['市盈率(pe)', '市盈率(动态)', '市盈率']),
            pb_ratio=get_val(row, ['市净率(pb)', '市净率']),
            dividend_rate=get_val(row, ['股息率']),
            debt_ratio=get_val(row, ['资产负债率']),
            market_cap=market_cap_val,
            industry=str(row.get('所属同花顺行业', row.get('所属行业', 'N/A'))),
            range_change=get_val(row, ['区间涨跌幅:前复权', '区间涨跌幅', '涨跌幅']),
            main_fund_inflow=get_val(row, ['区间主力资金流向', '主力资金净流入', '区间主力资金净流入']),
        )
        stocks.append(stock)
    return stocks


@router.post("/value", response_model=SuccessResponse[StockListResponse])
async def get_value_stocks(request: ValueStockRequest):
    """
    低估值策略选股
    """
    try:
        logger.info(f"低估值选股请求: top_n={request.top_n}")
        
        from strategies.value_stock_selector import ValueStockSelector
        
        selector = ValueStockSelector()
        success, df, message = selector.get_value_stocks(
            pe_max=request.pe_max,
            pb_max=request.pb_max,
            top_n=request.top_n
        )
        
        # 如果 df 只有一列（表示没有匹配数据）或者是字符串（错误信息）
        if isinstance(df, str) or (isinstance(df, pd.DataFrame) and df.empty):
            logger.warning(f"低估值选股失败: {message}")
            return SuccessResponse.success(
                data=StockListResponse(
                    success=False,
                    message=message,
                    count=0,
                    stocks=[],
                ),
                message=message,
            )
        
        stocks = convert_df_to_stock_info(df)
        
        logger.info(f"低估值选股成功: {len(stocks)} 只股票")
        
        return SuccessResponse.success(
            data=StockListResponse(
                success=True,
                message=message,
                count=len(stocks),
                stocks=stocks,
            ),
            message="低估值选股完成",
        )
        
    except Exception as e:
        logger.error(f"低估值选股异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"低估值选股失败: {str(e)}")


@router.post("/main-force", response_model=SuccessResponse[StockListResponse])
async def get_main_force_stocks(request: MainForceStockRequest):
    """
    主力选股
    """
    try:
        logger.info(f"主力选股请求: {request}")
        
        from strategies.main_force_selector import MainForceStockSelector
        
        selector = MainForceStockSelector()
        
        success, df, message = selector.get_main_force_stocks(
            days_ago=request.days_ago,
            min_market_cap=request.min_market_cap,
            max_market_cap=request.max_market_cap,
        )
        
        if not success or df is None:
            logger.warning(f"主力选股失败: {message}")
            return SuccessResponse.success(
                data=StockListResponse(
                    success=False,
                    message=message,
                    count=0,
                    stocks=[],
                ),
                message=message,
            )
        
        filtered_df = selector.filter_stocks(
            df,
            max_range_change=request.max_range_change,
            min_market_cap=request.min_market_cap,
            max_market_cap=request.max_market_cap,
        )
        
        top_df = selector.get_top_stocks(filtered_df, top_n=request.top_n)
        
        stocks = convert_df_to_stock_info(top_df)
        
        logger.info(f"主力选股成功: {len(stocks)} 只股票")
        
        return SuccessResponse.success(
            data=StockListResponse(
                success=True,
                message=f"成功筛选出{len(stocks)}只主力股票",
                count=len(stocks),
                stocks=stocks,
            ),
            message="主力选股完成",
        )
        
    except Exception as e:
        logger.error(f"主力选股异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"主力选股失败: {str(e)}")


@router.get("/strategies", response_model=SuccessResponse[List[str]])
async def get_stock_strategies():
    """
    获取所有选股策略列表
    """
    strategies = [
        "value",
        "main-force",
        "small-cap",
        "profit-growth",
        "sector-rotation",
    ]
    
    return SuccessResponse.success(
        data=strategies,
        message="选股策略列表获取成功",
    )
