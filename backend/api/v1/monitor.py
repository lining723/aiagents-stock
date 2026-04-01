from fastapi import APIRouter, HTTPException
from typing import List
import sys
import os

from schemas.monitor import (
    MonitoredStockCreate,
    MonitoredStockUpdate,
    MonitoredStockListResponse,
    MonitoredStockResponse,
    MonitoredStockInfo,
    NotificationListResponse,
    NotificationInfo,
    MonitorConfig,
    MonitorConfigResponse,
)
from schemas.response import SuccessResponse
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["智能盯盘模块"])

monitor_config = MonitorConfig(
    monitor_enabled=False,
    check_interval=300,
    auto_notification=True,
)


def get_monitor_db():
    from db.monitor_db import StockMonitorDatabase
    return StockMonitorDatabase()


@router.get("/config", response_model=SuccessResponse[MonitorConfigResponse])
async def get_monitor_config():
    """
    获取监控配置
    """
    try:
        logger.info("获取监控配置")
        return SuccessResponse.success(
            data=MonitorConfigResponse(
                success=True,
                message="获取成功",
                config=monitor_config,
            ),
            message="监控配置获取成功",
        )
    except Exception as e:
        logger.error(f"获取监控配置异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取监控配置失败: {str(e)}")


@router.put("/config", response_model=SuccessResponse[MonitorConfigResponse])
async def update_monitor_config(config: MonitorConfig):
    """
    更新监控配置
    """
    try:
        logger.info(f"更新监控配置: {config}")
        global monitor_config
        monitor_config = config
        return SuccessResponse.success(
            data=MonitorConfigResponse(
                success=True,
                message="更新成功",
                config=monitor_config,
            ),
            message="监控配置更新成功",
        )
    except Exception as e:
        logger.error(f"更新监控配置异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新监控配置失败: {str(e)}")


@router.get("/stocks", response_model=SuccessResponse[MonitoredStockListResponse])
async def get_monitored_stocks():
    """
    获取所有监测股票
    """
    try:
        logger.info("获取监测股票列表")
        db = get_monitor_db()
        stocks = db.get_monitored_stocks()
        
        stock_list = []
        for stock in stocks:
            stock_list.append(MonitoredStockInfo(
                id=str(stock.get("id", "")),
                symbol=stock.get("symbol", ""),
                name=stock.get("name", ""),
                rating=stock.get("rating", "持有"),
                entry_range=stock.get("entry_range", {}),
                take_profit=stock.get("take_profit"),
                stop_loss=stock.get("stop_loss"),
                current_price=stock.get("current_price"),
                last_checked=str(stock.get("last_checked", "")) if stock.get("last_checked") else None,
                check_interval=stock.get("check_interval", 30),
                notification_enabled=stock.get("notification_enabled", True),
                trading_hours_only=stock.get("trading_hours_only", True),
                quant_enabled=stock.get("quant_enabled", False),
                quant_config=stock.get("quant_config"),
                created_at=str(stock.get("created_at", "")),
                updated_at=str(stock.get("updated_at", "")),
            ))
        
        logger.info(f"获取到 {len(stock_list)} 只监测股票")
        
        return SuccessResponse.success(
            data=MonitoredStockListResponse(
                success=True,
                message="获取成功",
                stocks=stock_list,
                total=len(stock_list),
            ),
            message="监测股票列表获取成功",
        )
    except Exception as e:
        logger.error(f"获取监测股票列表异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取监测股票列表失败: {str(e)}")


@router.post("/stocks", response_model=SuccessResponse[MonitoredStockResponse])
async def add_monitored_stock(stock: MonitoredStockCreate):
    """
    添加监测股票
    """
    try:
        logger.info(f"添加监测股票: {stock.symbol}")
        db = get_monitor_db()
        
        stock_id = db.add_monitored_stock(
            symbol=stock.symbol,
            name=stock.name,
            rating=stock.rating,
            entry_range=stock.entry_range.model_dump(),
            take_profit=stock.take_profit,
            stop_loss=stock.stop_loss,
            check_interval=stock.check_interval,
            notification_enabled=stock.notification_enabled,
            trading_hours_only=stock.trading_hours_only,
            quant_enabled=stock.quant_enabled,
            quant_config=stock.quant_config,
        )
        
        stock_info = db.get_stock_by_id(stock_id)
        if not stock_info:
            raise HTTPException(status_code=404, detail="添加成功但获取股票信息失败")
        
        logger.info(f"添加监测股票成功: {stock.symbol}, id={stock_id}")
        
        return SuccessResponse.success(
            data=MonitoredStockResponse(
                success=True,
                message="添加成功",
                stock=MonitoredStockInfo(
                    id=str(stock_info.get("id", "")),
                    symbol=stock_info.get("symbol", ""),
                    name=stock_info.get("name", ""),
                    rating=stock_info.get("rating", "持有"),
                    entry_range=stock_info.get("entry_range", {}),
                    take_profit=stock_info.get("take_profit"),
                    stop_loss=stock_info.get("stop_loss"),
                    current_price=stock_info.get("current_price"),
                    last_checked=str(stock_info.get("last_checked", "")) if stock_info.get("last_checked") else None,
                    check_interval=stock_info.get("check_interval", 30),
                    notification_enabled=stock_info.get("notification_enabled", True),
                    trading_hours_only=stock_info.get("trading_hours_only", True),
                    quant_enabled=stock_info.get("quant_enabled", False),
                    quant_config=stock_info.get("quant_config"),
                    created_at=str(stock_info.get("created_at", "")),
                    updated_at=str(stock_info.get("updated_at", "")),
                ),
            ),
            message="监测股票添加成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加监测股票异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"添加监测股票失败: {str(e)}")


@router.get("/stocks/{stock_id}", response_model=SuccessResponse[MonitoredStockResponse])
async def get_monitored_stock(stock_id: str):
    """
    获取监测股票详情
    """
    try:
        logger.info(f"获取监测股票详情: stock_id={stock_id}")
        db = get_monitor_db()
        stock_info = db.get_stock_by_id(stock_id)
        
        if not stock_info:
            logger.warning(f"监测股票不存在: stock_id={stock_id}")
            raise HTTPException(status_code=404, detail="监测股票不存在")
        
        logger.info(f"获取监测股票详情成功: stock_id={stock_id}")
        
        return SuccessResponse.success(
            data=MonitoredStockResponse(
                success=True,
                message="获取成功",
                stock=MonitoredStockInfo(
                    id=str(stock_info.get("id", "")),
                    symbol=stock_info.get("symbol", ""),
                    name=stock_info.get("name", ""),
                    rating=stock_info.get("rating", "持有"),
                    entry_range=stock_info.get("entry_range", {}),
                    take_profit=stock_info.get("take_profit"),
                    stop_loss=stock_info.get("stop_loss"),
                    current_price=stock_info.get("current_price"),
                    last_checked=str(stock_info.get("last_checked", "")) if stock_info.get("last_checked") else None,
                    check_interval=stock_info.get("check_interval", 30),
                    notification_enabled=stock_info.get("notification_enabled", True),
                    trading_hours_only=stock_info.get("trading_hours_only", True),
                    quant_enabled=stock_info.get("quant_enabled", False),
                    quant_config=stock_info.get("quant_config"),
                    created_at=str(stock_info.get("created_at", "")),
                    updated_at=str(stock_info.get("updated_at", "")),
                ),
            ),
            message="监测股票详情获取成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监测股票详情异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取监测股票详情失败: {str(e)}")


@router.put("/stocks/{stock_id}", response_model=SuccessResponse[MonitoredStockResponse])
async def update_monitored_stock(stock_id: str, stock_update: MonitoredStockUpdate):
    """
    更新监测股票
    """
    try:
        logger.info(f"更新监测股票: stock_id={stock_id}")
        db = get_monitor_db()
        
        existing_stock = db.get_stock_by_id(stock_id)
        if not existing_stock:
            logger.warning(f"监测股票不存在: stock_id={stock_id}")
            raise HTTPException(status_code=404, detail="监测股票不存在")
        
        success = db.update_monitored_stock(
            stock_id=stock_id,
            rating=stock_update.rating or existing_stock.get("rating", "持有"),
            entry_range=stock_update.entry_range.model_dump() if stock_update.entry_range else existing_stock.get("entry_range", {}),
            take_profit=stock_update.take_profit or existing_stock.get("take_profit"),
            stop_loss=stock_update.stop_loss or existing_stock.get("stop_loss"),
            check_interval=stock_update.check_interval or existing_stock.get("check_interval", 30),
            notification_enabled=stock_update.notification_enabled if stock_update.notification_enabled is not None else existing_stock.get("notification_enabled", True),
            trading_hours_only=stock_update.trading_hours_only if stock_update.trading_hours_only is not None else existing_stock.get("trading_hours_only", True),
            quant_enabled=stock_update.quant_enabled if stock_update.quant_enabled is not None else existing_stock.get("quant_enabled", False),
            quant_config=stock_update.quant_config or existing_stock.get("quant_config"),
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="更新失败")
        
        stock_info = db.get_stock_by_id(stock_id)
        logger.info(f"更新监测股票成功: stock_id={stock_id}")
        
        return SuccessResponse.success(
            data=MonitoredStockResponse(
                success=True,
                message="更新成功",
                stock=MonitoredStockInfo(
                    id=str(stock_info.get("id", "")),
                    symbol=stock_info.get("symbol", ""),
                    name=stock_info.get("name", ""),
                    rating=stock_info.get("rating", "持有"),
                    entry_range=stock_info.get("entry_range", {}),
                    take_profit=stock_info.get("take_profit"),
                    stop_loss=stock_info.get("stop_loss"),
                    current_price=stock_info.get("current_price"),
                    last_checked=str(stock_info.get("last_checked", "")) if stock_info.get("last_checked") else None,
                    check_interval=stock_info.get("check_interval", 30),
                    notification_enabled=stock_info.get("notification_enabled", True),
                    trading_hours_only=stock_info.get("trading_hours_only", True),
                    quant_enabled=stock_info.get("quant_enabled", False),
                    quant_config=stock_info.get("quant_config"),
                    created_at=str(stock_info.get("created_at", "")),
                    updated_at=str(stock_info.get("updated_at", "")),
                ),
            ),
            message="监测股票更新成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新监测股票异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新监测股票失败: {str(e)}")


@router.delete("/stocks/{stock_id}", response_model=SuccessResponse[dict])
async def delete_monitored_stock(stock_id: str):
    """
    删除监测股票
    """
    try:
        logger.info(f"删除监测股票: stock_id={stock_id}")
        db = get_monitor_db()
        success = db.remove_monitored_stock(stock_id)
        
        if not success:
            logger.warning(f"监测股票删除失败或不存在: stock_id={stock_id}")
            raise HTTPException(status_code=404, detail="监测股票不存在")
        
        logger.info(f"删除监测股票成功: stock_id={stock_id}")
        
        return SuccessResponse.success(
            data={"stock_id": stock_id},
            message="监测股票删除成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除监测股票异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除监测股票失败: {str(e)}")


@router.get("/notifications", response_model=SuccessResponse[NotificationListResponse])
async def get_notifications(limit: int = 20):
    """
    获取通知列表
    """
    try:
        logger.info(f"获取通知列表: limit={limit}")
        db = get_monitor_db()
        notifications = db.get_all_recent_notifications(limit=limit)
        
        notification_list = []
        for notification in notifications:
            notification_list.append(NotificationInfo(
                id=str(notification.get("id", "")),
                stock_id=str(notification.get("stock_id", "")),
                symbol=notification.get("symbol", ""),
                name=notification.get("name", ""),
                type=notification.get("type", ""),
                message=notification.get("message", ""),
                triggered_at=str(notification.get("triggered_at", "")),
                sent=notification.get("sent", False),
            ))
        
        logger.info(f"获取到 {len(notification_list)} 条通知")
        
        return SuccessResponse.success(
            data=NotificationListResponse(
                success=True,
                message="获取成功",
                notifications=notification_list,
                total=len(notification_list),
            ),
            message="通知列表获取成功",
        )
    except Exception as e:
        logger.error(f"获取通知列表异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取通知列表失败: {str(e)}")


@router.post("/notifications/mark-read", response_model=SuccessResponse[dict])
async def mark_notifications_read():
    """
    标记所有通知为已读
    """
    try:
        logger.info("标记所有通知为已读")
        db = get_monitor_db()
        count = db.mark_all_notifications_sent()
        
        logger.info(f"标记了 {count} 条通知为已读")
        
        return SuccessResponse.success(
            data={"marked_count": count},
            message=f"已标记 {count} 条通知为已读",
        )
    except Exception as e:
        logger.error(f"标记通知为已读异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"标记通知为已读失败: {str(e)}")


@router.delete("/notifications", response_model=SuccessResponse[dict])
async def clear_notifications():
    """
    清空所有通知
    """
    try:
        logger.info("清空所有通知")
        db = get_monitor_db()
        count = db.clear_all_notifications()
        
        logger.info(f"清空了 {count} 条通知")
        
        return SuccessResponse.success(
            data={"cleared_count": count},
            message=f"已清空 {count} 条通知",
        )
    except Exception as e:
        logger.error(f"清空通知异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空通知失败: {str(e)}")
