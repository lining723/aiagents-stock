import json
from datetime import datetime
import os
from utils.mongo_client import mongo_client
from bson.objectid import ObjectId

class StockAnalysisDatabase:
    def __init__(self, db_path="db/stock_analysis.db"):
        """初始化数据库连接（为了兼容旧代码保留了 db_path 参数）"""
        self.db = mongo_client.db
        if self.db is not None:
            self.collection = self.db.analysis_records
            self.init_database()
    
    def init_database(self):
        """初始化数据库表结构（创建索引）"""
        if self.db is not None:
            import pymongo
            self.collection.create_index([("created_at", pymongo.DESCENDING)])
    
    def save_analysis(self, symbol, stock_name, period, stock_info, agents_results, discussion_result, final_decision):
        """保存分析记录到数据库"""
        if self.db is None:
            return None

        # 准备数据
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created_at = datetime.now().isoformat()
        
        document = {
            "symbol": symbol,
            "stock_name": stock_name,
            "analysis_date": analysis_date,
            "period": period,
            "stock_info": stock_info,
            "agents_results": agents_results,
            "discussion_result": discussion_result,
            "final_decision": final_decision,
            "created_at": created_at
        }
        
        result = self.collection.insert_one(document)
        return str(result.inserted_id)
    
    def get_all_records(self):
        """获取所有分析记录"""
        if self.db is None:
            return []

        import pymongo
        cursor = self.collection.find({}, {
            "symbol": 1, 
            "stock_name": 1, 
            "analysis_date": 1, 
            "period": 1, 
            "final_decision": 1, 
            "created_at": 1
        }).sort("created_at", pymongo.DESCENDING)
        
        result = []
        for doc in cursor:
            # 解析final_decision获取评级
            final_decision = doc.get("final_decision", {})
            rating = final_decision.get('rating', '未知') if isinstance(final_decision, dict) else '未知'
            
            result.append({
                'id': str(doc["_id"]),
                'symbol': doc.get("symbol"),
                'stock_name': doc.get("stock_name"),
                'analysis_date': doc.get("analysis_date"),
                'period': doc.get("period"),
                'rating': rating,
                'created_at': doc.get("created_at")
            })
        
        return result
    
    def get_record_count(self):
        """获取记录总数"""
        if self.db is None:
            return 0
        return self.collection.count_documents({})
    
    def get_record_by_id(self, record_id):
        """根据ID获取详细分析记录"""
        if self.db is None:
            return None

        try:
            doc = self.collection.find_one({"_id": ObjectId(record_id)})
            if not doc:
                return None
            
            doc['id'] = str(doc.pop("_id"))
            return doc
        except Exception:
            return None
    
    def delete_record(self, record_id):
        """删除指定记录"""
        if self.db is None:
            return False

        try:
            result = self.collection.delete_one({"_id": ObjectId(record_id)})
            return result.deleted_count > 0
        except Exception:
            return False

# 全局数据库实例
db = StockAnalysisDatabase()