#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低价擒牛策略监控模块 (MongoDB 版)
监控持仓股票的卖出信号
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import os
import pymongo
from bson import ObjectId

from utils.mongo_client import mongo_client

class LowPriceBullMonitor:
    """低价擒牛策略监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.logger = logging.getLogger(__name__)
        self.db = mongo_client.db
        if self.db is not None:
            self._init_database()
        else:
            self.logger.error("MongoDB 连接未初始化，LowPriceBullMonitor 无法正常工作")
    
    def _init_database(self):
        """初始化数据库索引"""
        try:
            # 创建监控列表表索引
            self.db['low_price_monitored_stocks'].create_index([("stock_code", pymongo.ASCENDING), ("status", pymongo.ASCENDING)], unique=True)
            self.db['low_price_monitored_stocks'].create_index([("add_time", pymongo.DESCENDING)])
            
            # 创建卖出提醒表索引
            self.db['low_price_sell_alerts'].create_index([("stock_code", pymongo.ASCENDING)])
            self.db['low_price_sell_alerts'].create_index([("alert_time", pymongo.DESCENDING)])
            
            self.logger.info("低价擒牛监控数据库初始化完成 (MongoDB)")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")

    def _format_doc(self, doc: dict) -> dict:
        """格式化 MongoDB 文档，将 _id 转换为 id 字符串"""
        if not doc:
            return None
        formatted = doc.copy()
        if '_id' in formatted:
            formatted['id'] = str(formatted.pop('_id'))
        return formatted
    
    def add_stock(self, stock_code: str, stock_name: str, buy_price: float, 
                  buy_date: str = None) -> Tuple[bool, str]:
        """添加股票到监控列表"""
        try:
            if buy_date is None:
                buy_date = datetime.now().strftime("%Y-%m-%d")
            
            # 检查是否已存在
            existing = self.db['low_price_monitored_stocks'].find_one({
                "stock_code": stock_code,
                "status": "holding"
            })
            
            if existing:
                return False, f"股票 {stock_code} 已在监控列表中"
            
            doc = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "buy_price": buy_price,
                "buy_date": buy_date,
                "holding_days": 0,
                "status": "holding",
                "add_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "remove_time": None,
                "remove_reason": None
            }
            
            self.db['low_price_monitored_stocks'].insert_one(doc)
            
            self.logger.info(f"添加股票到监控: {stock_code} {stock_name}")
            return True, f"成功添加 {stock_code} {stock_name} 到监控列表"
            
        except Exception as e:
            self.logger.error(f"添加股票失败: {e}")
            return False, f"添加失败: {str(e)}"
    
    def remove_stock(self, stock_code: str, reason: str = "手动移除") -> Tuple[bool, str]:
        """从监控列表移除股票"""
        try:
            existing = self.db['low_price_monitored_stocks'].find_one({
                "stock_code": stock_code,
                "status": "holding"
            })
            
            if not existing:
                return False, f"股票 {stock_code} 不在监控列表中"
            
            # 删除 removed 的历史记录（防止重新加入或索引冲突）
            self.db['low_price_monitored_stocks'].delete_many({
                "stock_code": stock_code,
                "status": "removed"
            })
            
            # 更新当前持仓为 removed
            self.db['low_price_monitored_stocks'].update_one(
                {"stock_code": stock_code, "status": "holding"},
                {"$set": {
                    "status": "removed",
                    "remove_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "remove_reason": reason
                }}
            )
            
            self.logger.info(f"移除股票: {stock_code}, 原因: {reason}")
            return True, f"成功移除 {stock_code}"
            
        except Exception as e:
            self.logger.error(f"移除股票失败: {e}")
            return False, f"移除失败: {str(e)}"
    
    def get_monitored_stocks(self) -> List[Dict]:
        """获取所有监控中的股票"""
        try:
            cursor = self.db['low_price_monitored_stocks'].find({"status": "holding"}).sort("add_time", pymongo.DESCENDING)
            return [self._format_doc(doc) for doc in cursor]
        except Exception as e:
            self.logger.error(f"获取监控列表失败: {e}")
            return []
    
    def update_holding_days(self):
        """更新所有股票的持有天数"""
        try:
            stocks = self.get_monitored_stocks()
            today = datetime.now().date()
            
            for stock in stocks:
                stock_code = stock['stock_code']
                buy_date = stock['buy_date']
                
                try:
                    buy_date_obj = datetime.strptime(buy_date, "%Y-%m-%d").date()
                    holding_days = (today - buy_date_obj).days
                    
                    self.db['low_price_monitored_stocks'].update_one(
                        {"stock_code": stock_code, "status": "holding"},
                        {"$set": {"holding_days": holding_days}}
                    )
                except Exception as inner_e:
                    self.logger.error(f"更新股票 {stock_code} 持有天数失败: {inner_e}")
            
            self.logger.info("持有天数更新完成")
            
        except Exception as e:
            self.logger.error(f"更新持有天数失败: {e}")
    
    def add_sell_alert(self, stock_code: str, stock_name: str, alert_type: str,
                      alert_reason: str, current_price: float = None,
                      ma5: float = None, ma20: float = None,
                      holding_days: int = None) -> bool:
        """添加卖出提醒"""
        try:
            existing = self.db['low_price_sell_alerts'].find_one({
                "stock_code": stock_code,
                "alert_type": alert_type,
                "is_sent": 0
            })
            
            if existing:
                return False
            
            doc = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "alert_type": alert_type,
                "alert_reason": alert_reason,
                "current_price": current_price,
                "ma5": ma5,
                "ma20": ma20,
                "holding_days": holding_days,
                "alert_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_sent": 0
            }
            
            self.db['low_price_sell_alerts'].insert_one(doc)
            self.logger.info(f"添加卖出提醒: {stock_code} - {alert_reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加卖出提醒失败: {e}")
            return False
    
    def get_pending_alerts(self) -> List[Dict]:
        """获取待发送的提醒"""
        try:
            cursor = self.db['low_price_sell_alerts'].find({"is_sent": 0}).sort("alert_time", pymongo.DESCENDING)
            return [self._format_doc(doc) for doc in cursor]
        except Exception as e:
            self.logger.error(f"获取提醒失败: {e}")
            return []
    
    def mark_alert_sent(self, alert_id: str):
        """标记提醒已发送"""
        try:
            self.db['low_price_sell_alerts'].update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": {"is_sent": 1}}
            )
        except Exception as e:
            self.logger.error(f"标记提醒失败: {e}")
    
    def get_history_alerts(self, limit: int = 50) -> List[Dict]:
        """获取历史提醒记录"""
        try:
            cursor = self.db['low_price_sell_alerts'].find().sort("alert_time", pymongo.DESCENDING).limit(limit)
            return [self._format_doc(doc) for doc in cursor]
        except Exception as e:
            self.logger.error(f"获取历史提醒失败: {e}")
            return []
    
    def clear_old_alerts(self, days: int = 30):
        """清理旧的提醒记录"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            result = self.db['low_price_sell_alerts'].delete_many({
                "alert_time": {"$lt": cutoff_date},
                "is_sent": 1
            })
            self.logger.info(f"清理了 {result.deleted_count} 条旧提醒记录")
        except Exception as e:
            self.logger.error(f"清理旧提醒失败: {e}")

# 全局监控器实例
low_price_bull_monitor = LowPriceBullMonitor()
