from fastapi import APIRouter, HTTPException
from typing import Any
import math
from schemas.analysis import (
    TechnicalAnalysisRequest,
    FundamentalAnalysisRequest,
    ComprehensiveAnalysisRequest,
    AIAnalysisRequest,
    AIAnalysisResponse,
    BatchAIAnalysisRequest,
    BatchAIAnalysisResponse,
    TechnicalAnalysisResponse,
    FundamentalAnalysisResponse,
    ComprehensiveAnalysisResponse,
    TechnicalIndicator,
    KlineData,
    FundamentalMetric,
    AnalysisScore,
    AnalysisHistoryItem,
    AnalysisHistoryListResponse,
    AnalysisHistoryDetailResponse,
)
from schemas.response import SuccessResponse
from utils.logger import get_logger

logger = get_logger(__name__)


def clean_nan_values(data: Any) -> Any:
    """递归清理数据中的NaN和无穷大值"""
    if isinstance(data, dict):
        return {k: clean_nan_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return 0.0
        return data
    else:
        return data

router = APIRouter(tags=["股票分析"])


@router.post("/technical", response_model=SuccessResponse[TechnicalAnalysisResponse])
async def get_technical_analysis(request: TechnicalAnalysisRequest):
    """
    技术分析
    """
    try:
        logger.info(f"技术分析请求: symbol={request.symbol}, days_ago={request.days_ago}")
        
        from services.stock_analyzer import StockAnalyzer
        
        analyzer = StockAnalyzer()
        success, data, message = analyzer.get_technical_analysis(
            symbol=request.symbol,
            days_ago=request.days_ago
        )
        
        if not success or data is None:
            logger.warning(f"技术分析失败: {message}")
            return SuccessResponse.success(
                data=TechnicalAnalysisResponse(
                    success=False,
                    message=message,
                    symbol=request.symbol,
                    indicators=[],
                ),
                message=message,
            )
        
        indicators = []
        for ind_data in data.get('indicators', []):
            indicators.append(TechnicalIndicator(
                name=ind_data.get('name', ''),
                value=ind_data.get('value'),
                signal=ind_data.get('signal'),
                description=ind_data.get('description'),
            ))
        
        buy_signals = sum(1 for ind in indicators if ind.signal == "buy")
        sell_signals = sum(1 for ind in indicators if ind.signal == "sell")
        
        if buy_signals > sell_signals:
            summary = "技术面整体向好，建议关注"
        elif sell_signals > buy_signals:
            summary = "技术面存在调整压力，建议观望"
        else:
            summary = "技术面中性，保持观望"

        kline_data = []
        for k_data in data.get('kline_data', []):
            kline_data.append(KlineData(**k_data))

        response = TechnicalAnalysisResponse(
            success=True,
            message="技术分析完成",
            symbol=data.get('symbol', request.symbol),
            name=data.get('name'),
            current_price=data.get('current_price'),
            change_percent=data.get('change_percent'),
            indicators=indicators,
            kline_data=kline_data,
            summary=summary,
        )
        
        response_dict = response.model_dump()
        response_dict = clean_nan_values(response_dict)
        response = TechnicalAnalysisResponse(**response_dict)
        
        logger.info(f"技术分析完成: {request.symbol}")
        
        return SuccessResponse.success(
            data=response,
            message="技术分析完成",
        )
        
    except Exception as e:
        logger.error(f"技术分析异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"技术分析失败: {str(e)}")


@router.post("/fundamental", response_model=SuccessResponse[FundamentalAnalysisResponse])
async def get_fundamental_analysis(request: FundamentalAnalysisRequest):
    """
    基本面分析
    """
    try:
        logger.info(f"基本面分析请求: symbol={request.symbol}")
        
        from services.stock_analyzer import StockAnalyzer
        
        analyzer = StockAnalyzer()
        success, data, message = analyzer.get_fundamental_analysis(
            symbol=request.symbol
        )
        
        if not success or data is None:
            logger.warning(f"基本面分析失败: {message}")
            return SuccessResponse.success(
                data=FundamentalAnalysisResponse(
                    success=False,
                    message=message,
                    symbol=request.symbol,
                    metrics=[],
                ),
                message=message,
            )
        
        metrics = []
        for metric_data in data.get('metrics', []):
            metrics.append(FundamentalMetric(
                name=metric_data.get('name', ''),
                value=metric_data.get('value'),
                unit=metric_data.get('unit'),
                rank=metric_data.get('rank'),
                description=metric_data.get('description'),
            ))
        
        excellent_count = sum(1 for m in metrics if m.rank == "excellent")
        good_count = sum(1 for m in metrics if m.rank == "good")
        
        if excellent_count >= 3:
            summary = "基本面优秀，具备长期投资价值"
        elif excellent_count + good_count >= 4:
            summary = "基本面良好，值得关注"
        else:
            summary = "基本面一般，需谨慎对待"
        
        response = FundamentalAnalysisResponse(
            success=True,
            message="基本面分析完成",
            symbol=data.get('symbol', request.symbol),
            name=data.get('name'),
            industry=data.get('industry'),
            market_cap=data.get('market_cap'),
            pe_ratio=data.get('pe_ratio'),
            pb_ratio=data.get('pb_ratio'),
            roe=data.get('roe'),
            debt_ratio=data.get('debt_ratio'),
            dividend_rate=data.get('dividend_rate'),
            metrics=metrics,
            summary=summary,
        )
        
        response_dict = response.model_dump()
        response_dict = clean_nan_values(response_dict)
        response = FundamentalAnalysisResponse(**response_dict)
        
        logger.info(f"基本面分析完成: {request.symbol}")
        
        return SuccessResponse.success(
            data=response,
            message="基本面分析完成",
        )
        
    except Exception as e:
        logger.error(f"基本面分析异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"基本面分析失败: {str(e)}")


@router.post("/comprehensive", response_model=SuccessResponse[ComprehensiveAnalysisResponse])
async def get_comprehensive_analysis(request: ComprehensiveAnalysisRequest):
    """
    综合分析
    """
    try:
        logger.info(f"综合分析请求: symbol={request.symbol}, days_ago={request.days_ago}")
        
        technical_response = (await get_technical_analysis(
            TechnicalAnalysisRequest(symbol=request.symbol, days_ago=request.days_ago)
        )).data
        
        fundamental_response = (await get_fundamental_analysis(
            FundamentalAnalysisRequest(symbol=request.symbol)
        )).data
        
        technical_score = 0.0
        if technical_response and technical_response.success:
            buy_count = sum(1 for ind in technical_response.indicators if ind.signal == "buy")
            sell_count = sum(1 for ind in technical_response.indicators if ind.signal == "sell")
            hold_count = len(technical_response.indicators) - buy_count - sell_count
            technical_score = (buy_count * 100 + hold_count * 50) / max(len(technical_response.indicators), 1)
        
        fundamental_score = 0.0
        if fundamental_response and fundamental_response.success:
            excellent_count = sum(1 for m in fundamental_response.metrics if m.rank == "excellent")
            good_count = sum(1 for m in fundamental_response.metrics if m.rank == "good")
            average_count = sum(1 for m in fundamental_response.metrics if m.rank == "average")
            poor_count = sum(1 for m in fundamental_response.metrics if m.rank == "poor")
            total = len(fundamental_response.metrics)
            if total > 0:
                fundamental_score = (excellent_count * 100 + good_count * 75 + average_count * 50 + poor_count * 25) / total
        
        if technical_score == 0:
            technical_score = 70
        if fundamental_score == 0:
            fundamental_score = 70
        
        overall_score = (technical_score * 0.4 + fundamental_score * 0.6)
        
        if overall_score >= 80:
            overall_rating = "强烈推荐"
        elif overall_score >= 70:
            overall_rating = "推荐"
        elif overall_score >= 60:
            overall_rating = "持有"
        elif overall_score >= 50:
            overall_rating = "观望"
        else:
            overall_rating = "回避"
        
        scores = [
            AnalysisScore(category="技术面", score=round(technical_score, 2), weight=0.4),
            AnalysisScore(category="基本面", score=round(fundamental_score, 2), weight=0.6),
        ]
        
        risks = [
            "短期市场波动风险",
            "行业政策变化风险",
            "估值回调风险",
        ]
        
        opportunities = [
            "行业景气度提升",
            "公司业务拓展顺利",
            "业绩稳定增长",
        ]
        
        recommendations = []
        if overall_rating in ["强烈推荐", "推荐"]:
            recommendations = [
                "可逢低关注，分批建仓",
                "设置合理止损位，控制风险",
                "关注公司最新公告和行业动态",
                "中长期持有为主，避免频繁交易",
            ]
        elif overall_rating == "持有":
            recommendations = [
                "继续持有，观察后市",
                "关注关键支撑位和压力位",
                "做好仓位管理",
            ]
        else:
            recommendations = [
                "建议观望为主",
                "等待更明确的信号",
                "控制仓位，防范风险",
            ]
        
        response = ComprehensiveAnalysisResponse(
            success=True,
            message="综合分析完成",
            symbol=request.symbol,
            name=technical_response.name if technical_response else (fundamental_response.name if fundamental_response else None),
            overall_score=round(overall_score, 2),
            overall_rating=overall_rating,
            scores=scores,
            technical_analysis=technical_response,
            fundamental_analysis=fundamental_response,
            risks=risks,
            opportunities=opportunities,
            recommendations=recommendations,
        )
        
        response_dict = response.model_dump()
        response_dict = clean_nan_values(response_dict)
        response = ComprehensiveAnalysisResponse(**response_dict)
        
        logger.info(f"综合分析完成: {request.symbol}")
        
        return SuccessResponse.success(
            data=response,
            message="综合分析完成",
        )
        
    except Exception as e:
        logger.error(f"综合分析异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"综合分析失败: {str(e)}")


@router.post("/ai", response_model=SuccessResponse[AIAnalysisResponse])
async def get_ai_analysis(request: AIAnalysisRequest):
    """
    AI深度分析
    """
    try:
        logger.info(f"AI分析请求: symbol={request.symbol}, days_ago={request.days_ago}")
        
        from agents.stock_agents import StockAgents
        from services.stock_analyzer import StockAnalyzer

        analyzer = StockAnalyzer()
        agents = StockAgents()

        tech_success, tech_data, tech_msg = analyzer.get_technical_analysis(
            symbol=request.symbol,
            days_ago=request.days_ago
        )

        fund_success, fund_data, fund_msg = analyzer.get_fundamental_analysis(
            symbol=request.symbol
        )

        stock_name = None
        if tech_success and tech_data:
            stock_name = tech_data.get('name')
        elif fund_success and fund_data:
            stock_name = fund_data.get('name')

        ai_result = agents.comprehensive_stock_analyst(
            symbol=request.symbol,
            tech_data=tech_data if tech_success else None,
            fund_data=fund_data if fund_success else None,
        )

        response = AIAnalysisResponse(
            success=True,
            message="AI分析完成",
            symbol=request.symbol,
            name=stock_name,
            ai_report=ai_result.get('analysis', ''),
        )

        response_dict = response.model_dump()
        response_dict = clean_nan_values(response_dict)
        response = AIAnalysisResponse(**response_dict)

        # 保存分析历史
        try:
            from db.database import db
            db.save_analysis(
                symbol=request.symbol,
                stock_name=stock_name or request.symbol,
                period="AI深度分析",
                stock_info=fund_data if fund_success else {},
                agents_results={},
                discussion_result={"ai_report": ai_result.get('analysis', '')},
                final_decision={}
            )
            logger.info(f"AI分析结果已保存到历史记录: {request.symbol}")
        except Exception as e:
            logger.error(f"保存AI分析历史记录失败: {str(e)}")

        logger.info(f"AI分析完成: {request.symbol}")

        return SuccessResponse.success(
            data=response,
            message="AI分析完成",
        )

    except Exception as e:
        logger.error(f"AI分析异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")


@router.post("/batch-ai", response_model=SuccessResponse[BatchAIAnalysisResponse])
async def get_batch_ai_analysis(request: BatchAIAnalysisRequest):
    """
    批量AI深度分析
    """
    try:
        logger.info(f"批量AI分析请求: symbols={request.symbols}, days_ago={request.days_ago}")
        
        from agents.stock_agents import StockAgents
        from services.stock_analyzer import StockAnalyzer
        from db.database import db
        
        analyzer = StockAnalyzer()
        agents = StockAgents()
        
        results = []
        failed_symbols = []
        
        for symbol in request.symbols:
            try:
                logger.info(f"正在分析股票: {symbol}")
                
                tech_success, tech_data, tech_msg = analyzer.get_technical_analysis(
                    symbol=symbol,
                    days_ago=request.days_ago
                )

                fund_success, fund_data, fund_msg = analyzer.get_fundamental_analysis(
                    symbol=symbol
                )

                stock_name = None
                if tech_success and tech_data:
                    stock_name = tech_data.get('name')
                elif fund_success and fund_data:
                    stock_name = fund_data.get('name')

                ai_result = agents.comprehensive_stock_analyst(
                    symbol=symbol,
                    tech_data=tech_data if tech_success else None,
                    fund_data=fund_data if fund_success else None,
                )
                
                response_item = AIAnalysisResponse(
                    success=True,
                    message="AI分析完成",
                    symbol=symbol,
                    name=stock_name,
                    ai_report=ai_result.get('analysis', ''),
                )
                
                response_dict = response_item.model_dump()
                response_dict = clean_nan_values(response_dict)
                response_item = AIAnalysisResponse(**response_dict)
                
                results.append(response_item)
                
                # 保存分析历史
                try:
                    db.save_analysis(
                        symbol=symbol,
                        stock_name=stock_name or symbol,
                        period="AI深度分析(批量)",
                        stock_info=fund_data if fund_success else {},
                        agents_results={},
                        discussion_result={"ai_report": ai_result.get('analysis', '')},
                        final_decision={}
                    )
                    logger.info(f"批量AI分析结果已保存到历史记录: {symbol}")
                except Exception as db_e:
                    logger.error(f"保存批量AI分析历史记录失败 ({symbol}): {str(db_e)}")
                    
            except Exception as single_e:
                logger.error(f"分析股票 {symbol} 时发生异常: {str(single_e)}")
                failed_symbols.append(symbol)
                
        response_data = BatchAIAnalysisResponse(
            success=True,
            message="批量分析完成",
            total=len(request.symbols),
            success_count=len(results),
            failed_count=len(failed_symbols),
            results=results,
            failed_symbols=failed_symbols
        )
        
        return SuccessResponse.success(
            data=response_data,
            message=f"批量分析完成, 成功 {len(results)} 只, 失败 {len(failed_symbols)} 只",
        )
        
    except Exception as e:
        logger.error(f"批量AI分析异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量AI分析失败: {str(e)}")


@router.get("/history", response_model=SuccessResponse[AnalysisHistoryListResponse])
async def get_analysis_history(limit: int = 50, offset: int = 0):
    """获取分析历史列表"""
    try:
        from db.database import db
        records = db.get_all_records()
        
        # 处理分页
        paginated_records = records[offset:offset+limit] if records else []
        
        items = []
        for record in paginated_records:
            items.append(AnalysisHistoryItem(
                id=record.get("id"),
                symbol=record.get("symbol"),
                name=record.get("stock_name"),
                created_at=record.get("created_at"),
            ))
            
        return SuccessResponse.success(
            data=AnalysisHistoryListResponse(
                success=True,
                message="获取成功",
                total=len(records) if records else 0,
                items=items
            ),
            message="分析历史列表获取成功"
        )
    except Exception as e:
        logger.error(f"获取分析历史列表异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分析历史列表失败: {str(e)}")


@router.get("/history/{history_id}", response_model=SuccessResponse[AnalysisHistoryDetailResponse])
async def get_analysis_history_detail(history_id: str):
    """获取单条分析历史详情"""
    try:
        from db.database import db
        record = db.get_record_by_id(history_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="历史记录不存在")
            
        # 尝试从 discussion_result 中获取 ai_report
        ai_report = ""
        discussion = record.get("discussion_result", {})
        if isinstance(discussion, dict) and "ai_report" in discussion:
            ai_report = discussion["ai_report"]
            
        item = AnalysisHistoryItem(
            id=record.get("id"),
            symbol=record.get("symbol"),
            name=record.get("stock_name"),
            created_at=record.get("created_at"),
            ai_report=ai_report
        )
        
        return SuccessResponse.success(
            data=AnalysisHistoryDetailResponse(
                success=True,
                message="获取成功",
                data=item
            ),
            message="分析历史详情获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析历史详情异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分析历史详情失败: {str(e)}")


@router.delete("/history/{history_id}", response_model=SuccessResponse[dict])
async def delete_analysis_history(history_id: str):
    """删除分析历史"""
    try:
        from db.database import db
        success = db.delete_record(history_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="历史记录不存在或删除失败")
            
        return SuccessResponse.success(
            data={"id": history_id},
            message="删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除分析历史异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除分析历史失败: {str(e)}")
