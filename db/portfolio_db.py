"""
持仓股票数据库管理模块

提供持仓股票和分析历史的数据库操作接口 (MongoDB 版)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import pymongo
from bson import ObjectId

from utils.mongo_client import mongo_client


class PortfolioDB:
    """持仓股票数据库管理类"""
    
    def __init__(self):
        """
        初始化数据库连接
        """
        self.db = mongo_client.db
        if self.db is not None:
            self.stocks_coll = self.db['portfolio_stocks']
            self.history_coll = self.db['portfolio_analysis_history']
            self._init_database()
        else:
            print("[ERROR] MongoDB 连接未初始化，PortfolioDB 无法正常工作")
            self.stocks_coll = None
            self.history_coll = None
    
    def _init_database(self):
        """初始化数据库索引"""
        try:
            # 持仓股票代码唯一索引
            self.stocks_coll.create_index([("code", pymongo.ASCENDING)], unique=True)
            
            # 分析历史索引
            self.history_coll.create_index([("portfolio_stock_id", pymongo.ASCENDING)])
            self.history_coll.create_index([("analysis_time", pymongo.DESCENDING)])
            
            print("[OK] MongoDB portfolio_db 索引初始化成功")
        except Exception as e:
            print(f"[ERROR] 数据库索引初始化失败: {e}")
    
    def _format_doc(self, doc: dict) -> dict:
        """格式化 MongoDB 文档，将 _id 转换为 id 字符串"""
        if not doc:
            return None
        formatted = doc.copy()
        if '_id' in formatted:
            formatted['id'] = str(formatted.pop('_id'))
        if 'portfolio_stock_id' in formatted and isinstance(formatted['portfolio_stock_id'], ObjectId):
            formatted['portfolio_stock_id'] = str(formatted['portfolio_stock_id'])
        return formatted

    # ==================== 持仓股票CRUD操作 ====================
    
    def add_stock(self, code: str, name: str, cost_price: Optional[float] = None,
                  quantity: Optional[int] = None, note: str = "", 
                  auto_monitor: bool = True) -> str:
        """
        添加持仓股票
        """
        try:
            doc = {
                "code": code,
                "name": name,
                "cost_price": cost_price,
                "quantity": quantity,
                "note": note,
                "auto_monitor": auto_monitor,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            result = self.stocks_coll.insert_one(doc)
            stock_id = str(result.inserted_id)
            print(f"[OK] 添加持仓股票成功: {code} {name} (ID: {stock_id})")
            return stock_id
            
        except pymongo.errors.DuplicateKeyError as e:
            print(f"[ERROR] 股票代码已存在: {code}")
            raise ValueError(f"股票代码 {code} 已存在") from e
        except Exception as e:
            print(f"[ERROR] 添加持仓股票失败: {e}")
            raise
    
    def update_stock(self, stock_id: str, **kwargs) -> bool:
        """
        更新持仓股票信息
        """
        # 允许更新的字段
        allowed_fields = ['code', 'name', 'cost_price', 'quantity', 'note', 'auto_monitor']
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            print("[WARN] 没有需要更新的字段")
            return False
        
        update_fields['updated_at'] = datetime.now()
        
        try:
            result = self.stocks_coll.update_one(
                {"_id": ObjectId(stock_id)},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                print(f"[OK] 更新持仓股票成功: ID {stock_id}")
                return True
            else:
                print(f"[WARN] 未找到股票: ID {stock_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 更新持仓股票失败: {e}")
            raise
    
    def delete_stock(self, stock_id: str) -> bool:
        """
        删除持仓股票（级联删除其所有分析历史）
        """
        try:
            # 删除股票
            result = self.stocks_coll.delete_one({"_id": ObjectId(stock_id)})
            
            if result.deleted_count > 0:
                # 级联删除分析历史
                self.history_coll.delete_many({"portfolio_stock_id": str(stock_id)})
                print(f"[OK] 删除持仓股票成功: ID {stock_id}")
                return True
            else:
                print(f"[WARN] 未找到股票: ID {stock_id}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 删除持仓股票失败: {e}")
            raise
    
    def get_stock(self, stock_id: str) -> Optional[Dict]:
        """
        获取单只持仓股票信息
        """
        try:
            doc = self.stocks_coll.find_one({"_id": ObjectId(stock_id)})
            return self._format_doc(doc)
        except Exception as e:
            print(f"[ERROR] 获取持仓股票失败: {e}")
            return None
    
    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        """
        根据股票代码获取持仓股票信息
        """
        try:
            doc = self.stocks_coll.find_one({"code": code})
            return self._format_doc(doc)
        except Exception as e:
            print(f"[ERROR] 获取持仓股票失败: {e}")
            return None
    
    def get_all_stocks(self, auto_monitor_only: bool = False) -> List[Dict]:
        """
        获取所有持仓股票列表
        """
        try:
            query = {"auto_monitor": True} if auto_monitor_only else {}
            # SQLite 版本处理 bool 为 1 或 True
            # 为了兼容性，如果是 True/1，MongoDB 中通常存的是 bool
            if auto_monitor_only:
                query = {"auto_monitor": {"$in": [True, 1]}}
                
            cursor = self.stocks_coll.find(query).sort("created_at", pymongo.DESCENDING)
            return [self._format_doc(doc) for doc in cursor]
        except Exception as e:
            print(f"[ERROR] 获取持仓股票列表失败: {e}")
            return []
    
    def search_stocks(self, keyword: str) -> List[Dict]:
        """
        搜索持仓股票（按代码或名称）
        """
        try:
            query = {
                "$or": [
                    {"code": {"$regex": keyword, "$options": "i"}},
                    {"name": {"$regex": keyword, "$options": "i"}}
                ]
            }
            cursor = self.stocks_coll.find(query).sort("created_at", pymongo.DESCENDING)
            return [self._format_doc(doc) for doc in cursor]
        except Exception as e:
            print(f"[ERROR] 搜索持仓股票失败: {e}")
            return []
    
    def get_stock_count(self) -> int:
        """
        获取持仓股票总数
        """
        try:
            return self.stocks_coll.count_documents({})
        except Exception as e:
            print(f"[ERROR] 获取持仓股票数量失败: {e}")
            return 0
    
    # ==================== 分析历史记录操作 ====================
    
    def save_analysis(self, stock_id: str, rating: str, confidence: float,
                     current_price: float, target_price: Optional[float] = None,
                     entry_min: Optional[float] = None, entry_max: Optional[float] = None,
                     take_profit: Optional[float] = None, stop_loss: Optional[float] = None,
                     summary: str = "") -> str:
        """
        保存分析历史记录
        """
        try:
            doc = {
                "portfolio_stock_id": str(stock_id),
                "analysis_time": datetime.now(),
                "rating": rating,
                "confidence": confidence,
                "current_price": current_price,
                "target_price": target_price,
                "entry_min": entry_min,
                "entry_max": entry_max,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "summary": summary
            }
            
            result = self.history_coll.insert_one(doc)
            analysis_id = str(result.inserted_id)
            print(f"[OK] 保存分析历史成功: 股票ID {stock_id}, 评级 {rating}")
            return analysis_id
            
        except Exception as e:
            print(f"[ERROR] 保存分析历史失败: {e}")
            raise
    
    def get_analysis_history(self, stock_id: str, limit: int = 10) -> List[Dict]:
        """
        获取股票的分析历史记录
        """
        try:
            cursor = self.history_coll.find({"portfolio_stock_id": str(stock_id)}) \
                                      .sort("analysis_time", pymongo.DESCENDING) \
                                      .limit(limit)
            return [self._format_doc(doc) for doc in cursor]
        except Exception as e:
            print(f"[ERROR] 获取分析历史失败: {e}")
            return []
    
    def get_latest_analysis_history(self, stock_id: str, limit: int = 10) -> List[Dict]:
        """
        获取股票的最新分析历史记录（按时间倒序）
        """
        return self.get_analysis_history(stock_id, limit)
    
    def get_latest_analysis(self, stock_id: str) -> Optional[Dict]:
        """
        获取股票的最新一次分析记录
        """
        try:
            doc = self.history_coll.find_one(
                {"portfolio_stock_id": str(stock_id)},
                sort=[("analysis_time", pymongo.DESCENDING)]
            )
            return self._format_doc(doc)
        except Exception as e:
            print(f"[ERROR] 获取最新分析记录失败: {e}")
            return None
    
    def get_rating_changes(self, stock_id: str, days: int = 30) -> List[Tuple[Any, str, str]]:
        """
        获取股票在指定天数内的评级变化
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor = self.history_coll.find(
                {
                    "portfolio_stock_id": str(stock_id),
                    "analysis_time": {"$gte": cutoff_date}
                },
                {"analysis_time": 1, "rating": 1}
            ).sort("analysis_time", pymongo.ASCENDING)
            
            rows = list(cursor)
            changes = []
            
            for i in range(1, len(rows)):
                prev_rating = rows[i-1].get('rating')
                curr_rating = rows[i].get('rating')
                if prev_rating != curr_rating:
                    # 返回 datetime 字符串以兼容 sqlite 的 TIMESTAMP 返回格式，或直接返回 datetime
                    time_val = rows[i].get('analysis_time')
                    if isinstance(time_val, datetime):
                        time_val = time_val.strftime("%Y-%m-%d %H:%M:%S")
                    changes.append((
                        time_val,
                        prev_rating,
                        curr_rating
                    ))
            
            return changes
        except Exception as e:
            print(f"[ERROR] 获取评级变化失败: {e}")
            return []
    
    def delete_old_analysis(self, days: int = 90) -> int:
        """
        删除超过指定天数的分析历史记录
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            result = self.history_coll.delete_many({"analysis_time": {"$lt": cutoff_date}})
            deleted_count = result.deleted_count
            print(f"[OK] 清理历史分析记录: 删除 {deleted_count} 条记录")
            return deleted_count
        except Exception as e:
            print(f"[ERROR] 清理历史分析记录失败: {e}")
            raise
    
    def get_all_latest_analysis(self) -> List[Dict]:
        """
        获取所有持仓股票的最新分析记录
        """
        try:
            # 聚合查询：先获取所有股票
            stocks = list(self.stocks_coll.find().sort("created_at", pymongo.DESCENDING))
            
            # 为每个股票查找最新的分析记录
            result = []
            for stock in stocks:
                formatted_stock = self._format_doc(stock)
                
                latest_history = self.history_coll.find_one(
                    {"portfolio_stock_id": formatted_stock['id']},
                    sort=[("analysis_time", pymongo.DESCENDING)]
                )
                
                if latest_history:
                    # 合并字段
                    for k in ['rating', 'confidence', 'current_price', 'target_price',
                             'entry_min', 'entry_max', 'take_profit', 'stop_loss', 'analysis_time']:
                        formatted_stock[k] = latest_history.get(k)
                else:
                    for k in ['rating', 'confidence', 'current_price', 'target_price',
                             'entry_min', 'entry_max', 'take_profit', 'stop_loss', 'analysis_time']:
                        formatted_stock[k] = None
                        
                result.append(formatted_stock)
                
            return result
            
        except Exception as e:
            print(f"[ERROR] 获取所有最新分析记录失败: {e}")
            return []


# 创建全局数据库实例
portfolio_db = PortfolioDB()


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("持仓股票数据库测试 (MongoDB)")
    print("=" * 50)
    
    db = portfolio_db
    
    # 测试添加股票
    try:
        stock_id = db.add_stock("600519", "贵州茅台", 1650.5, 100, "长期持有")
        print(f"\n添加股票ID: {stock_id}")
    except ValueError as e:
        print(f"\n{e}")
        # 如果存在，获取它
        existing = db.get_stock_by_code("600519")
        stock_id = existing['id']
    
    # 测试查询所有股票
    print("\n所有持仓股票:")
    stocks = db.get_all_stocks()
    for stock in stocks:
        print(f"  {stock['code']} {stock['name']}")
    
    # 测试保存分析历史
    if stocks:
        test_stock_id = stocks[0]['id']
        analysis_id = db.save_analysis(
            test_stock_id, "买入", 8.5, 1700.0, 1850.0,
            1600.0, 1650.0, 1900.0, 1500.0,
            "技术面和基本面均良好"
        )
        print(f"\n保存分析记录ID: {analysis_id}")
        
        # 查询分析历史
        print(f"\n股票 {stocks[0]['code']} 的分析历史:")
        history = db.get_analysis_history(test_stock_id)
        for h in history:
            print(f"  {h['analysis_time']}: {h['rating']} (信心度: {h['confidence']})")
    
    print("\n[OK] 数据库测试完成")


