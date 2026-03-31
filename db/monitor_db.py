import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import pymongo
from bson import ObjectId

from utils.mongo_client import mongo_client

class StockMonitorDatabase:
    """股票监测数据库管理类 (MongoDB 版)"""
    
    def __init__(self):
        self.db = mongo_client.db
        if self.db is not None:
            self.init_database()
        else:
            print("MongoDB 连接未初始化，StockMonitorDatabase 无法正常工作")
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            self.db['monitored_stocks'].create_index([("symbol", pymongo.ASCENDING)], unique=True)
            self.db['price_history'].create_index([("stock_id", pymongo.ASCENDING)])
            self.db['price_history'].create_index([("timestamp", pymongo.DESCENDING)])
            self.db['notifications'].create_index([("stock_id", pymongo.ASCENDING)])
            self.db['notifications'].create_index([("triggered_at", pymongo.DESCENDING)])
            print("✅ MongoDB monitor_db 索引初始化成功")
        except Exception as e:
            print(f"✅ 数据库初始化错误: {e}")

    def _format_doc(self, doc: dict) -> dict:
        """格式化 MongoDB 文档，将 _id 转换为 id 字符串"""
        if not doc:
            return None
        formatted = doc.copy()
        if '_id' in formatted:
            formatted['id'] = str(formatted.pop('_id'))
        if 'stock_id' in formatted and isinstance(formatted['stock_id'], ObjectId):
            formatted['stock_id'] = str(formatted['stock_id'])
        return formatted

    def add_monitored_stock(self, symbol: str, name: str, rating: str, 
                           entry_range: Dict, take_profit: float, 
                           stop_loss: float, check_interval: int = 30, 
                           notification_enabled: bool = True,
                           trading_hours_only: bool = True,
                           quant_enabled: bool = False,
                           quant_config: Dict = None) -> str:
        """添加监测股票"""
        doc = {
            "symbol": symbol,
            "name": name,
            "rating": rating,
            "entry_range": entry_range,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "current_price": None,
            "last_checked": None,
            "check_interval": check_interval,
            "notification_enabled": notification_enabled,
            "trading_hours_only": trading_hours_only,
            "quant_enabled": quant_enabled,
            "quant_config": quant_config,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        try:
            result = self.db['monitored_stocks'].insert_one(doc)
            return str(result.inserted_id)
        except pymongo.errors.DuplicateKeyError:
            # 如果存在则返回已存在的id
            existing = self.db['monitored_stocks'].find_one({"symbol": symbol})
            return str(existing['_id'])
    
    def get_monitored_stocks(self) -> List[Dict]:
        """获取所有监测股票"""
        cursor = self.db['monitored_stocks'].find().sort("created_at", pymongo.DESCENDING)
        stocks = []
        for doc in cursor:
            stocks.append(self._format_doc(doc))
        return stocks
    
    def update_stock_price(self, stock_id: str, price: float):
        """更新股票价格"""
        now = datetime.now()
        self.db['monitored_stocks'].update_one(
            {"_id": ObjectId(stock_id)},
            {"$set": {"current_price": price, "last_checked": now}}
        )
        
        self.db['price_history'].insert_one({
            "stock_id": str(stock_id),
            "price": price,
            "timestamp": now
        })
    
    def update_last_checked(self, stock_id: str):
        """仅更新最后检查时间（用于获取失败的情况）"""
        self.db['monitored_stocks'].update_one(
            {"_id": ObjectId(stock_id)},
            {"$set": {"last_checked": datetime.now()}}
        )
    
    def has_recent_notification(self, stock_id: str, notification_type: str, minutes: int = 60) -> bool:
        """检查是否在最近X分钟内已有相同类型的通知"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        count = self.db['notifications'].count_documents({
            "stock_id": str(stock_id),
            "type": notification_type,
            "triggered_at": {"$gt": cutoff}
        })
        return count > 0
    
    def add_notification(self, stock_id: str, notification_type: str, message: str):
        """添加提醒记录"""
        self.db['notifications'].insert_one({
            "stock_id": str(stock_id),
            "type": notification_type,
            "message": message,
            "triggered_at": datetime.now(),
            "sent": False
        })
    
    def get_pending_notifications(self) -> List[Dict]:
        """获取待发送的提醒"""
        cursor = self.db['notifications'].find({"sent": False}).sort("triggered_at", pymongo.ASCENDING)
        notifications = []
        for doc in cursor:
            stock = self.db['monitored_stocks'].find_one({"_id": ObjectId(doc['stock_id'])})
            if stock:
                notif = self._format_doc(doc)
                notif['symbol'] = stock.get('symbol')
                notif['name'] = stock.get('name')
                notifications.append(notif)
        return notifications
    
    def get_all_recent_notifications(self, limit: int = 10) -> List[Dict]:
        """获取最近的所有通知（包括已发送和未发送的）"""
        cursor = self.db['notifications'].find().sort("triggered_at", pymongo.DESCENDING).limit(limit)
        notifications = []
        for doc in cursor:
            stock = self.db['monitored_stocks'].find_one({"_id": ObjectId(doc['stock_id'])})
            if stock:
                notif = self._format_doc(doc)
                notif['symbol'] = stock.get('symbol')
                notif['name'] = stock.get('name')
                notifications.append(notif)
        return notifications
    
    def mark_notification_sent(self, notification_id: str):
        """标记提醒已发送"""
        self.db['notifications'].update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"sent": True}}
        )
    
    def mark_all_notifications_sent(self):
        """标记所有通知为已读"""
        result = self.db['notifications'].update_many(
            {"sent": False},
            {"$set": {"sent": True}}
        )
        return result.modified_count
    
    def clear_all_notifications(self):
        """清空所有通知"""
        result = self.db['notifications'].delete_many({})
        return result.deleted_count
    
    def remove_monitored_stock(self, stock_id: str):
        """移除监测股票"""
        try:
            self.db['price_history'].delete_many({"stock_id": str(stock_id)})
            self.db['notifications'].delete_many({"stock_id": str(stock_id)})
            result = self.db['monitored_stocks'].delete_one({"_id": ObjectId(stock_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"删除股票失败: {e}")
            return False
    
    def update_monitored_stock(self, stock_id: str, rating: str, entry_range: Dict, 
                              take_profit: float, stop_loss: float, 
                              check_interval: int, notification_enabled: bool,
                              trading_hours_only: bool = None,
                              quant_enabled: bool = None,
                              quant_config: Dict = None):
        """更新监测股票"""
        updates = {
            "rating": rating,
            "entry_range": entry_range,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "check_interval": check_interval,
            "notification_enabled": notification_enabled,
            "updated_at": datetime.now()
        }
        if trading_hours_only is not None:
            updates["trading_hours_only"] = trading_hours_only
        if quant_enabled is not None:
            updates["quant_enabled"] = quant_enabled
        if quant_config is not None:
            updates["quant_config"] = quant_config
            
        result = self.db['monitored_stocks'].update_one(
            {"_id": ObjectId(stock_id)},
            {"$set": updates}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    def toggle_notification(self, stock_id: str, enabled: bool):
        """切换通知状态"""
        result = self.db['monitored_stocks'].update_one(
            {"_id": ObjectId(stock_id)},
            {"$set": {"notification_enabled": enabled, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    def get_stock_by_id(self, stock_id: str) -> Optional[Dict]:
        """根据ID获取股票信息"""
        doc = self.db['monitored_stocks'].find_one({"_id": ObjectId(stock_id)})
        return self._format_doc(doc)
    
    def get_monitor_by_code(self, symbol: str) -> Optional[Dict]:
        """
        根据股票代码获取监测信息
        """
        doc = self.db['monitored_stocks'].find_one({"symbol": symbol})
        return self._format_doc(doc)
    
    def batch_add_or_update_monitors(self, monitors_data: List[Dict]) -> Dict[str, int]:
        """
        批量添加或更新监测股票
        """
        added = 0
        updated = 0
        failed = 0
        
        for data in monitors_data:
            try:
                symbol = data.get('code') or data.get('symbol')
                name = data.get('name', symbol)
                rating = data.get('rating', '持有')
                entry_min = data.get('entry_min')
                entry_max = data.get('entry_max')
                take_profit = data.get('take_profit')
                stop_loss = data.get('stop_loss')
                check_interval = data.get('check_interval', 60)
                notification_enabled = data.get('notification_enabled', True)
                trading_hours_only = data.get('trading_hours_only', True)
                
                if not symbol or not all([entry_min, entry_max, take_profit, stop_loss]):
                    print(f"[WARN] {symbol} 参数不完整，跳过")
                    failed += 1
                    continue
                
                entry_range = {"min": entry_min, "max": entry_max}
                
                existing = self.get_monitor_by_code(symbol)
                
                if existing:
                    self.update_monitored_stock(
                        existing['id'],
                        rating=rating,
                        entry_range=entry_range,
                        take_profit=take_profit,
                        stop_loss=stop_loss,
                        check_interval=check_interval,
                        notification_enabled=notification_enabled,
                        trading_hours_only=trading_hours_only
                    )
                    updated += 1
                    print(f"[OK] 更新监测: {symbol}")
                else:
                    self.add_monitored_stock(
                        symbol=symbol,
                        name=name,
                        rating=rating,
                        entry_range=entry_range,
                        take_profit=take_profit,
                        stop_loss=stop_loss,
                        check_interval=check_interval,
                        notification_enabled=notification_enabled,
                        trading_hours_only=trading_hours_only
                    )
                    added += 1
                    print(f"[OK] 添加监测: {symbol}")
                    
            except Exception as e:
                symbol_str = data.get('code') or data.get('symbol', 'Unknown')
                print(f"[ERROR] 处理监测失败 ({symbol_str}): {str(e)}")
                failed += 1
        
        result = {
            "added": added,
            "updated": updated,
            "failed": failed,
            "total": added + updated + failed
        }
        
        print(f"\n[OK] 批量同步完成: 新增{added}只, 更新{updated}只, 失败{failed}只")
        return result

# 全局数据库实例
monitor_db = StockMonitorDatabase()