from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List
import sys
import os
from datetime import datetime, timedelta
import uuid

from schemas.longhubang import (
    LonghubangAnalysisRequest,
    LonghubangAnalysisResponse,
    LonghubangReportListResponse,
    LonghubangReportInfo,
    LonghubangReportDetail,
)
from schemas.response import SuccessResponse
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["智瞰龙虎模块"])


@router.post("/analyze", response_model=SuccessResponse[LonghubangAnalysisResponse])
async def analyze_longhubang(request: LonghubangAnalysisRequest):
    """
    龙虎榜分析
    """
    try:
        logger.info(f"智瞰龙虎分析请求: {request}")
        
        from services.longhubang_engine import LonghubangEngine
        
        engine = LonghubangEngine()
        
        if request.analysis_mode == "指定日期" and request.date:
            results = await run_in_threadpool(
                engine.run_comprehensive_analysis,
                date=request.date,
            )
        else:
            results = await run_in_threadpool(
                engine.run_comprehensive_analysis,
                days=request.days,
            )
        
        if not results.get("success", False):
            error_msg = results.get("error", "分析失败")
            logger.warning(f"智瞰龙虎分析失败: {error_msg}")
            return SuccessResponse.success(
                data=LonghubangAnalysisResponse(
                    success=False,
                    message=error_msg,
                ),
                message=error_msg,
            )
        
        report_id = str(results.get("report_id", uuid.uuid4()))
        
        logger.info(f"智瞰龙虎分析成功: report_id={report_id}")
        
        return SuccessResponse.success(
            data=LonghubangAnalysisResponse(
                success=True,
                message="分析完成",
                report_id=report_id,
                data_info=results.get("data_info", {}),
                agents_analysis=results.get("agents_analysis", {}),
                final_report=results.get("final_report", {}),
                recommended_stocks=results.get("recommended_stocks", []),
            ),
            message="龙虎榜分析完成",
        )
        
    except Exception as e:
        logger.error(f"智瞰龙虎分析异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"龙虎榜分析失败: {str(e)}")


@router.get("/reports", response_model=SuccessResponse[LonghubangReportListResponse])
async def get_reports_list():
    """
    获取历史报告列表
    """
    try:
        logger.info("获取智瞰龙虎历史报告列表")
        
        from db.longhubang_db import LonghubangDatabase
        
        db = LonghubangDatabase()
        df = db.get_analysis_reports(limit=100)
        
        report_list = []
        for _, report in df.iterrows():
            report_list.append(LonghubangReportInfo(
                report_id=str(report.get("id", "")),
                date=str(report.get("analysis_date", "")),
                created_at=report.get("created_at", datetime.now()),
                stock_count=0,
                youzi_count=0,
            ))
        
        logger.info(f"获取到 {len(report_list)} 个历史报告")
        
        return SuccessResponse.success(
            data=LonghubangReportListResponse(
                success=True,
                message="获取成功",
                reports=report_list,
                total=len(report_list),
            ),
            message="历史报告列表获取成功",
        )
        
    except Exception as e:
        logger.error(f"获取历史报告列表异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取历史报告列表失败: {str(e)}")


@router.get("/reports/{report_id}", response_model=SuccessResponse[LonghubangReportDetail])
async def get_report_detail(report_id: str):
    """
    获取报告详情
    """
    try:
        logger.info(f"获取智瞰龙虎报告详情: report_id={report_id}")
        
        from db.longhubang_db import LonghubangDatabase
        
        db = LonghubangDatabase()
        report = db.get_analysis_report(report_id)
        
        if not report:
            logger.warning(f"报告不存在: report_id={report_id}")
            raise HTTPException(status_code=404, detail="报告不存在")
        
        logger.info(f"获取报告详情成功: report_id={report_id}")
        
        analysis_content = report.get('analysis_content_parsed', {}) or {}
        data_info = analysis_content.get("data_info", {}) if isinstance(analysis_content, dict) else {}
        agents_analysis = analysis_content.get("agents_analysis", analysis_content) if isinstance(analysis_content, dict) else {}
        final_report = analysis_content.get("final_report", {}) if isinstance(analysis_content, dict) else {}
        if not final_report:
            final_report = {"summary": report.get("summary", "")}
        
        return SuccessResponse.success(
            data=LonghubangReportDetail(
                report_id=str(report.get("id", "")),
                date=str(report.get("analysis_date", "")),
                created_at=report.get("created_at", datetime.now()),
                data_info=data_info,
                agents_analysis=agents_analysis,
                final_report=final_report,
                recommended_stocks=report.get("recommended_stocks", []),
            ),
            message="报告详情获取成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告详情异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取报告详情失败: {str(e)}")


@router.delete("/reports/{report_id}", response_model=SuccessResponse[dict])
async def delete_report(report_id: str):
    """
    删除报告
    """
    try:
        logger.info(f"删除智瞰龙虎报告: report_id={report_id}")
        
        from db.longhubang_db import LonghubangDatabase
        
        db = LonghubangDatabase()
        success = db.delete_analysis_report(report_id)
        
        if not success:
            logger.warning(f"报告删除失败或不存在: report_id={report_id}")
            raise HTTPException(status_code=404, detail="报告不存在")
        
        logger.info(f"报告删除成功: report_id={report_id}")
        
        return SuccessResponse.success(
            data={"report_id": report_id},
            message="报告删除成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除报告失败: {str(e)}")


@router.get("/statistics", response_model=SuccessResponse[dict])
async def get_statistics():
    """
    获取数据统计
    """
    try:
        logger.info("获取智瞰龙虎数据统计")
        
        from db.longhubang_db import LonghubangDatabase
        
        db = LonghubangDatabase()
        stats = db.get_statistics()
        
        logger.info("获取数据统计成功")
        
        return SuccessResponse.success(
            data=stats,
            message="数据统计获取成功",
        )
        
    except Exception as e:
        logger.error(f"获取数据统计异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取数据统计失败: {str(e)}")
