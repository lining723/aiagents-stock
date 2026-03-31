"""
智能盯盘 - 数据库模块 (MongoDB 版)
记录AI决策、交易记录、监控配置等
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import pymongo
from bson import ObjectId

from utils.mongo_client import mongo_client


class SmartMonitorDB:
    """智能盯盘数据库 (MongoDB 版)"""
    
    def __init__(self):
        """
        初始化数据库
        """
        self.db = mongo_client.db
        self.logger = logging.getLogger(__name__)
        if self.db is not None:
            self._init_database()
        else:
            self.logger.error("MongoDB 连接未初始化，SmartMonitorDB 无法正常工作")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            # 1. 监控任务表
            self.db['monitor_tasks'].create_index([("stock_code", pymongo.ASCENDING)], unique=True)
            self.db['monitor_tasks'].create_index([("enabled", pymongo.ASCENDING)])
            
            # 2. AI决策记录表
            self.db['ai_decisions'].create_index([("stock_code", pymongo.ASCENDING)])
            self.db['ai_decisions'].create_index([("decision_time", pymongo.DESCENDING)])
            
            # 3. 交易记录表
            self.db['trade_records'].create_index([("stock_code", pymongo.ASCENDING)])
            self.db['trade_records'].create_index([("trade_time", pymongo.DESCENDING)])
            
            # 4. 持仓监控表
            self.db['position_monitor'].create_index([("stock_code", pymongo.ASCENDING)], unique=True)
            self.db['position_monitor'].create_index([("status", pymongo.ASCENDING)])
            
            # 5. 通知记录表
            self.db['smart_notifications'].create_index([("stock_code", pymongo.ASCENDING)])
            self.db['smart_notifications'].create_index([("created_at", pymongo.DESCENDING)])
            
            # 6. 系统日志表
            self.db['system_logs'].create_index([("created_at", pymongo.DESCENDING)])
            
            self.logger.info("数据库初始化完成 (MongoDB)")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            
    def _format_doc(self, doc: dict) -> dict:
        """格式化 MongoDB 文档，将 _id 转换为 id 字符串"""
        if not doc:
            return None
        formatted = doc.copy()
        if '_id' in formatted:
            formatted['id'] = str(formatted.pop('_id'))
        if 'ai_decision_id' in formatted and isinstance(formatted['ai_decision_id'], ObjectId):
            formatted['ai_decision_id'] = str(formatted['ai_decision_id'])
        return formatted
    
    # ========== 监控任务管理 ==========
    
    def add_monitor_task(self, task_data: Dict) -> str:
        """添加监控任务"""
        doc = {
            "task_name": task_data.get('task_name'),
            "stock_code": task_data.get('stock_code'),
            "stock_name": task_data.get('stock_name'),
            "enabled": task_data.get('enabled', 1),
            "check_interval": task_data.get('check_interval', 300),
            "auto_trade": task_data.get('auto_trade', 0),
            "trading_hours_only": task_data.get('trading_hours_only', 1),
            "position_size_pct": task_data.get('position_size_pct', 20),
            "stop_loss_pct": task_data.get('stop_loss_pct', 5),
            "take_profit_pct": task_data.get('take_profit_pct', 10),
            "qmt_account_id": task_data.get('qmt_account_id'),
            "notify_email": task_data.get('notify_email'),
            "notify_webhook": task_data.get('notify_webhook'),
            "has_position": task_data.get('has_position', 0),
            "position_cost": task_data.get('position_cost', 0),
            "position_quantity": task_data.get('position_quantity', 0),
            "position_date": task_data.get('position_date'),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        try:
            result = self.db['monitor_tasks'].insert_one(doc)
            task_id = str(result.inserted_id)
            
            position_info = f"（持仓: {task_data.get('position_quantity')}股 @ {task_data.get('position_cost')}元）" if task_data.get('has_position') else ""
            self.logger.info(f"添加监控任务: {task_data.get('stock_code')} - {task_data.get('task_name')} {position_info}")
            return task_id
        except pymongo.errors.DuplicateKeyError:
            self.logger.warning(f"监控任务已存在: {task_data.get('stock_code')}")
            existing = self.db['monitor_tasks'].find_one({"stock_code": task_data.get('stock_code')})
            return str(existing['_id'])
    
    def get_monitor_tasks(self, enabled_only: bool = True) -> List[Dict]:
        """获取监控任务列表"""
        query = {"enabled": 1} if enabled_only else {}
        cursor = self.db['monitor_tasks'].find(query).sort("_id", pymongo.DESCENDING)
        return [self._format_doc(doc) for doc in cursor]
    
    def update_monitor_task(self, stock_code: str, task_data: Dict):
        """更新监控任务"""
        updates = task_data.copy()
        # Remove fields that shouldn't be blindly updated if they exist
        updates.pop('stock_code', None)
        updates['updated_at'] = datetime.now()
        
        self.db['monitor_tasks'].update_one(
            {"stock_code": stock_code},
            {"$set": updates}
        )
        self.logger.info(f"更新监控任务: {stock_code}")
        
    def update_monitor_task_by_id(self, task_id: str, updates: Dict):
        """通过 ID 更新监控任务"""
        upd = updates.copy()
        upd['updated_at'] = datetime.now()
        self.db['monitor_tasks'].update_one(
            {"_id": ObjectId(task_id)},
            {"$set": upd}
        )
    
    def delete_monitor_task(self, task_id: str):
        """删除监控任务"""
        self.db['monitor_tasks'].delete_one({"_id": ObjectId(task_id)})
    
    # ========== AI决策记录 ==========
    
    def save_ai_decision(self, decision_data: Dict) -> str:
        """保存AI决策"""
        doc = {
            "stock_code": decision_data.get('stock_code'),
            "stock_name": decision_data.get('stock_name'),
            "decision_time": decision_data.get('decision_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "trading_session": decision_data.get('trading_session'),
            "action": decision_data.get('action'),
            "confidence": decision_data.get('confidence'),
            "reasoning": decision_data.get('reasoning'),
            "position_size_pct": decision_data.get('position_size_pct'),
            "stop_loss_pct": decision_data.get('stop_loss_pct'),
            "take_profit_pct": decision_data.get('take_profit_pct'),
            "risk_level": decision_data.get('risk_level'),
            "key_price_levels": decision_data.get('key_price_levels', {}),
            "market_data": decision_data.get('market_data', {}),
            "account_info": decision_data.get('account_info', {}),
            "executed": 0,
            "execution_result": None,
            "created_at": datetime.now()
        }
        
        result = self.db['ai_decisions'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_ai_decisions(self, stock_code: str = None, limit: int = 100) -> List[Dict]:
        """获取AI决策历史"""
        query = {"stock_code": stock_code} if stock_code else {}
        cursor = self.db['ai_decisions'].find(query).sort("decision_time", pymongo.DESCENDING).limit(limit)
        return [self._format_doc(doc) for doc in cursor]
    
    def update_decision_execution(self, decision_id: str, executed: bool, result: str):
        """更新决策执行状态"""
        self.db['ai_decisions'].update_one(
            {"_id": ObjectId(decision_id)},
            {"$set": {"executed": 1 if executed else 0, "execution_result": result}}
        )
    
    # ========== 交易记录 ==========
    
    def save_trade_record(self, trade_data: Dict) -> str:
        """保存交易记录"""
        doc = {
            "stock_code": trade_data.get('stock_code'),
            "stock_name": trade_data.get('stock_name'),
            "trade_type": trade_data.get('trade_type'),
            "quantity": trade_data.get('quantity'),
            "price": trade_data.get('price'),
            "amount": trade_data.get('amount'),
            "order_id": trade_data.get('order_id'),
            "order_status": trade_data.get('order_status'),
            "ai_decision_id": str(trade_data.get('ai_decision_id')) if trade_data.get('ai_decision_id') else None,
            "trade_time": trade_data.get('trade_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "commission": trade_data.get('commission', 0),
            "tax": trade_data.get('tax', 0),
            "profit_loss": trade_data.get('profit_loss', 0),
            "created_at": datetime.now()
        }
        
        result = self.db['trade_records'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_trade_records(self, stock_code: str = None, limit: int = 100) -> List[Dict]:
        """获取交易记录"""
        query = {"stock_code": stock_code} if stock_code else {}
        cursor = self.db['trade_records'].find(query).sort("trade_time", pymongo.DESCENDING).limit(limit)
        return [self._format_doc(doc) for doc in cursor]
    
    # ========== 持仓监控 ==========
    
    def save_position(self, position_data: Dict):
        """保存/更新持仓信息"""
        updates = {
            "stock_name": position_data.get('stock_name'),
            "quantity": position_data.get('quantity'),
            "cost_price": position_data.get('cost_price'),
            "current_price": position_data.get('current_price'),
            "profit_loss": position_data.get('profit_loss'),
            "profit_loss_pct": position_data.get('profit_loss_pct'),
            "holding_days": position_data.get('holding_days'),
            "buy_date": position_data.get('buy_date'),
            "stop_loss_price": position_data.get('stop_loss_price'),
            "take_profit_price": position_data.get('take_profit_price'),
            "last_check_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "status": 'holding',
            "updated_at": datetime.now()
        }
        
        self.db['position_monitor'].update_one(
            {"stock_code": position_data.get('stock_code')},
            {"$set": updates, "$setOnInsert": {"created_at": datetime.now()}},
            upsert=True
        )
    
    def get_positions(self) -> List[Dict]:
        """获取所有持仓"""
        cursor = self.db['position_monitor'].find({"status": "holding"}).sort("_id", pymongo.DESCENDING)
        return [self._format_doc(doc) for doc in cursor]
    
    def close_position(self, stock_code: str):
        """关闭持仓记录"""
        self.db['position_monitor'].update_one(
            {"stock_code": stock_code},
            {"$set": {"status": "closed", "updated_at": datetime.now()}}
        )
    
    # ========== 通知记录 ==========
    
    def save_notification(self, notify_data: Dict) -> str:
        """保存通知记录"""
        doc = {
            "stock_code": notify_data.get('stock_code'),
            "notify_type": notify_data.get('notify_type'),
            "notify_target": notify_data.get('notify_target'),
            "subject": notify_data.get('subject'),
            "content": notify_data.get('content'),
            "status": notify_data.get('status', 'pending'),
            "error_msg": None,
            "sent_at": None,
            "created_at": datetime.now()
        }
        
        result = self.db['smart_notifications'].insert_one(doc)
        return str(result.inserted_id)
    
    def update_notification_status(self, notify_id: str, status: str, error_msg: str = None):
        """更新通知状态"""
        self.db['smart_notifications'].update_one(
            {"_id": ObjectId(notify_id)},
            {"$set": {
                "status": status,
                "error_msg": error_msg,
                "sent_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }}
        )
    
    # ========== 系统日志 ==========
    
    def log_system_event(self, level: str, module: str, message: str, details: str = None):
        """记录系统日志"""
        self.db['system_logs'].insert_one({
            "log_level": level,
            "module": module,
            "message": message,
            "details": details,
            "created_at": datetime.now()
        })


if __name__ == '__main__':
    # 测试数据库
    logging.basicConfig(level=logging.INFO)
    
    db = SmartMonitorDB()
    
    # 测试添加监控任务
    task_id = db.add_monitor_task({
        'task_name': '茅台盯盘',
        'stock_code': '600519',
        'stock_name': '贵州茅台',
        'auto_trade': 1,
        'notify_email': 'test@example.com'
    })
    
    print(f"创建监控任务 ID: {task_id}")
    
    # 获取任务列表
    tasks = db.get_monitor_tasks()
    print(f"\n监控任务列表: {len(tasks)}个")
    for task in tasks:
        print(f"  - {task['stock_code']} {task['stock_name']}")

