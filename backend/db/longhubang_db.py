"""
智瞰龙虎数据库模块
用于存储龙虎榜历史数据和分析报告
"""

from datetime import datetime
import json
import pandas as pd
from utils.logger import get_logger
from utils.mongo_client import mongo_client
from bson.objectid import ObjectId

class LonghubangDatabase:
    """龙虎榜数据库管理类"""
    
    def __init__(self, db_path='db/longhubang.db'):
        """
        初始化数据库 (保留db_path以兼容旧接口)
        """
        self.logger = get_logger(__name__)
        self.db = mongo_client.db
        if self.db is not None:
            self.records_collection = self.db.longhubang_records
            self.analysis_collection = self.db.longhubang_analysis
            self.tracking_collection = self.db.stock_tracking
            self.init_database()
    
    def get_connection(self):
        """兼容旧接口"""
        return None
    
    def init_database(self):
        """初始化数据库索引"""
        if self.db is not None:
            import pymongo
            self.records_collection.create_index([("date", pymongo.DESCENDING)])
            self.records_collection.create_index([("stock_code", pymongo.ASCENDING)])
            self.records_collection.create_index([("youzi_name", pymongo.ASCENDING)])
            self.records_collection.create_index([("net_inflow", pymongo.DESCENDING)])
            self.records_collection.create_index(
                [("date", pymongo.ASCENDING), ("stock_code", pymongo.ASCENDING), ("youzi_name", pymongo.ASCENDING), ("yingye_bu", pymongo.ASCENDING)],
                unique=True
            )
            self.logger.info("[智瞰龙虎] MongoDB 索引初始化完成")
    
    def save_longhubang_data(self, data_list):
        """
        保存龙虎榜数据
        """
        if not data_list or self.db is None:
            return 0
        
        saved_count = 0
        for record in data_list:
            try:
                date = record.get('rq') or record.get('日期')
                stock_code = record.get('gpdm') or record.get('股票代码')
                youzi_name = record.get('yzmc') or record.get('游资名称')
                yingye_bu = record.get('yyb') or record.get('营业部')
                
                doc = {
                    "date": date,
                    "stock_code": stock_code,
                    "stock_name": record.get('gpmc') or record.get('股票名称'),
                    "youzi_name": youzi_name,
                    "yingye_bu": yingye_bu,
                    "list_type": record.get('sblx') or record.get('榜单类型'),
                    "buy_amount": float(record.get('mrje') or record.get('买入金额') or 0),
                    "sell_amount": float(record.get('mcje') or record.get('卖出金额') or 0),
                    "net_inflow": float(record.get('jlrje') or record.get('净流入金额') or 0),
                    "concepts": record.get('gl') or record.get('概念'),
                    "created_at": datetime.now().isoformat()
                }
                
                # Update or insert based on unique keys
                self.records_collection.update_one(
                    {
                        "date": date, 
                        "stock_code": stock_code, 
                        "youzi_name": youzi_name, 
                        "yingye_bu": yingye_bu
                    },
                    {"$set": doc},
                    upsert=True
                )
                saved_count += 1
            except Exception as e:
                self.logger.exception(f"保存记录失败: {e}", exc_info=True)
                continue
        
        self.logger.info(f"[智瞰龙虎] 成功保存 {saved_count} 条龙虎榜记录")
        return saved_count
    
    def get_longhubang_data(self, start_date=None, end_date=None, stock_code=None):
        """
        查询龙虎榜数据
        """
        if self.db is None:
            return pd.DataFrame()

        query = {}
        if start_date and end_date:
            query["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["date"] = {"$gte": start_date}
        elif end_date:
            query["date"] = {"$lte": end_date}
            
        if stock_code:
            query["stock_code"] = stock_code
            
        import pymongo
        cursor = self.records_collection.find(query).sort([("date", pymongo.DESCENDING), ("net_inflow", pymongo.DESCENDING)])
        
        df = pd.DataFrame(list(cursor))
        if not df.empty and '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
            df.rename(columns={'_id': 'id'}, inplace=True)
            
        return df
    
    def get_top_youzi(self, start_date=None, end_date=None, limit=20):
        """
        获取活跃游资排名
        """
        if self.db is None:
            return pd.DataFrame()

        match_stage = {}
        if start_date and end_date:
            match_stage["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            match_stage["date"] = {"$gte": start_date}
        elif end_date:
            match_stage["date"] = {"$lte": end_date}

        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.extend([
            {
                "$group": {
                    "_id": "$youzi_name",
                    "trade_count": {"$sum": 1},
                    "total_buy": {"$sum": "$buy_amount"},
                    "total_sell": {"$sum": "$sell_amount"},
                    "total_net_inflow": {"$sum": "$net_inflow"}
                }
            },
            {
                "$project": {
                    "youzi_name": "$_id",
                    "trade_count": 1,
                    "total_buy": 1,
                    "total_sell": 1,
                    "total_net_inflow": 1,
                    "_id": 0
                }
            },
            {"$sort": {"total_net_inflow": -1}},
            {"$limit": limit}
        ])

        cursor = self.records_collection.aggregate(pipeline)
        return pd.DataFrame(list(cursor))
    
    def get_top_stocks(self, start_date=None, end_date=None, limit=20):
        """
        获取热门股票排名
        """
        if self.db is None:
            return pd.DataFrame()

        match_stage = {}
        if start_date and end_date:
            match_stage["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            match_stage["date"] = {"$gte": start_date}
        elif end_date:
            match_stage["date"] = {"$lte": end_date}

        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "stock_code": "$stock_code",
                        "stock_name": "$stock_name"
                    },
                    "unique_youzi": {"$addToSet": "$youzi_name"},
                    "total_buy": {"$sum": "$buy_amount"},
                    "total_sell": {"$sum": "$sell_amount"},
                    "total_net_inflow": {"$sum": "$net_inflow"},
                    "concepts_set": {"$addToSet": "$concepts"}
                }
            },
            {
                "$project": {
                    "stock_code": "$_id.stock_code",
                    "stock_name": "$_id.stock_name",
                    "youzi_count": {"$size": "$unique_youzi"},
                    "total_buy": 1,
                    "total_sell": 1,
                    "total_net_inflow": 1,
                    "all_concepts": {
                        "$reduce": {
                            "input": "$concepts_set",
                            "initialValue": "",
                            "in": {
                                "$cond": [
                                    {"$eq": ["$$value", ""]},
                                    "$$this",
                                    {"$concat": ["$$value", ",", "$$this"]}
                                ]
                            }
                        }
                    },
                    "_id": 0
                }
            },
            {"$sort": {"total_net_inflow": -1}},
            {"$limit": limit}
        ])

        cursor = self.records_collection.aggregate(pipeline)
        return pd.DataFrame(list(cursor))
    
    def save_analysis_report(self, data_date_range, analysis_content, 
                           recommended_stocks, summary, full_result=None):
        """
        保存AI分析报告
        """
        if self.db is None:
            return None

        if isinstance(analysis_content, dict):
            analysis_content = json.dumps(analysis_content, ensure_ascii=False, indent=2)
        
        doc = {
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_date_range": data_date_range,
            "analysis_content": analysis_content,
            "recommended_stocks": json.dumps(recommended_stocks, ensure_ascii=False),
            "summary": summary,
            "created_at": datetime.now().isoformat()
        }
        
        result = self.analysis_collection.insert_one(doc)
        report_id = str(result.inserted_id)
        self.logger.info(f"[智瞰龙虎] 分析报告已保存 (ID: {report_id})")
        return report_id
    
    def get_analysis_reports(self, limit=10):
        """
        获取历史分析报告
        """
        if self.db is None:
            return pd.DataFrame()

        import pymongo
        cursor = self.analysis_collection.find().sort("created_at", pymongo.DESCENDING).limit(limit)
        df = pd.DataFrame(list(cursor))
        if not df.empty and '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
            df.rename(columns={'_id': 'id'}, inplace=True)
        return df
    
    def get_analysis_report(self, report_id):
        """
        获取单个分析报告详情
        """
        if self.db is None:
            return None

        try:
            report = self.analysis_collection.find_one({"_id": ObjectId(report_id)})
            if report:
                report['id'] = str(report.pop('_id'))
                
                if report.get('recommended_stocks'):
                    try:
                        report['recommended_stocks'] = json.loads(report['recommended_stocks'])
                    except Exception as e:
                        self.logger.warning(f"推荐股票JSON解析失败: {e}")
                
                if report.get('analysis_content'):
                    try:
                        report['analysis_content_parsed'] = json.loads(report['analysis_content'])
                    except json.JSONDecodeError as e:
                        report['analysis_content_parsed'] = None
                    except Exception as e:
                        report['analysis_content_parsed'] = None
                        
                return report
        except Exception:
            pass
        return None
    
    def delete_analysis_report(self, report_id):
        """
        删除分析报告
        """
        if self.db is None:
            return False

        try:
            self.tracking_collection.delete_many({"analysis_id": str(report_id)})
            result = self.analysis_collection.delete_one({"_id": ObjectId(report_id)})
            
            if result.deleted_count > 0:
                self.logger.info(f"[智瞰龙虎] 成功删除分析报告 (ID: {report_id})")
                return True
            else:
                self.logger.warning(f"[智瞰龙虎] 未找到要删除的分析报告 (ID: {report_id})")
                return False
        except Exception as e:
            self.logger.error(f"[智瞰龙虎] 删除分析报告失败: {e}")
            return False
    
    def update_stock_tracking(self, analysis_id, stock_code, current_price, status, notes=None):
        """
        更新股票追踪信息
        """
        if self.db is None:
            return

        self.tracking_collection.update_one(
            {
                "analysis_id": str(analysis_id),
                "stock_code": stock_code
            },
            {
                "$set": {
                    "current_price": current_price,
                    "status": status,
                    "notes": notes,
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            upsert=True
        )
    
    def get_statistics(self):
        """
        获取数据库统计信息
        """
        if self.db is None:
            return {}

        stats = {
            'total_records': self.records_collection.count_documents({}),
            'total_stocks': len(self.records_collection.distinct("stock_code")),
            'total_youzi': len(self.records_collection.distinct("youzi_name")),
            'total_reports': self.analysis_collection.count_documents({})
        }
        
        import pymongo
        first_doc = self.records_collection.find_one({}, sort=[("date", pymongo.ASCENDING)])
        last_doc = self.records_collection.find_one({}, sort=[("date", pymongo.DESCENDING)])
        
        stats['date_range'] = {
            'start': first_doc['date'] if first_doc else None,
            'end': last_doc['date'] if last_doc else None
        }
        
        return stats


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("测试智瞰龙虎数据库模块")
    print("=" * 60)
    
    db = LonghubangDatabase('test_longhubang.db')
    
    # 测试数据
    test_data = [
        {
            'rq': '2023-03-22',
            'gpdm': '001337',
            'gpmc': '四川黄金',
            'yzmc': '92科比',
            'yyb': '兴业证券股份有限公司南京天元东路证券营业部',
            'sblx': '1',
            'mrje': 14470401,
            'mcje': 15080,
            'jlrje': 14455321,
            'gl': '贵金属,四川板块,昨日连板_含一字,昨日涨停_含一字,黄金概念,次新股'
        }
    ]
    
    # 测试保存
    db.save_longhubang_data(test_data)
    
    # 测试查询
    df = db.get_longhubang_data()
    print(f"\n查询到 {len(df)} 条记录")
    
    # 获取统计信息
    stats = db.get_statistics()
    print(f"\n数据库统计: {stats}")

