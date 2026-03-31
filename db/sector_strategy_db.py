"""
智策板块数据库模块
用于存储板块策略历史数据和分析报告
"""

from datetime import datetime
import json
import pandas as pd
from utils.logger import get_logger
from utils.mongo_client import mongo_client
from bson.objectid import ObjectId

logger = get_logger(__name__)

class SectorStrategyDatabase:
    """智策板块数据库管理类"""
    
    def __init__(self, db_path='db/sector_strategy.db'):
        """初始化数据库 (保留db_path以兼容)"""
        self.logger = logger
        self.db = mongo_client.db
        if self.db is not None:
            self.raw_data_collection = self.db.sector_raw_data
            self.news_data_collection = self.db.sector_news_data
            self.reports_collection = self.db.sector_analysis_reports
            self.tracking_collection = self.db.sector_tracking
            self.versions_collection = self.db.data_versions
            self.init_database()
    
    def get_connection(self):
        """兼容旧接口"""
        return None
    
    def init_database(self):
        """初始化数据库索引"""
        if self.db is not None:
            import pymongo
            self.raw_data_collection.create_index([("data_date", pymongo.DESCENDING)])
            self.raw_data_collection.create_index([("sector_code", pymongo.ASCENDING)])
            self.raw_data_collection.create_index([("data_type", pymongo.ASCENDING)])
            self.raw_data_collection.create_index([("data_version", pymongo.ASCENDING)])
            self.raw_data_collection.create_index(
                [("data_date", pymongo.ASCENDING), ("sector_code", pymongo.ASCENDING), ("data_type", pymongo.ASCENDING)],
                unique=True
            )
            
            self.news_data_collection.create_index([("news_date", pymongo.DESCENDING)])
            
            self.reports_collection.create_index([("created_at", pymongo.DESCENDING)])
            
            self.versions_collection.create_index(
                [("data_type", pymongo.ASCENDING), ("data_date", pymongo.ASCENDING), ("version", pymongo.ASCENDING)],
                unique=True
            )
            self.logger.info("[智策板块] MongoDB 索引初始化完成")
    
    def save_raw_data(self, data_date, data_type, data_df, version=None):
        """保存原始数据"""
        if self.db is None:
            return None

        try:
            if version is None:
                version = self._get_next_version(data_date, data_type)
            
            if data_type == 'sector_data':
                self._save_sector_data(data_date, data_df, version)
            elif data_type == 'news_data':
                self._save_news_data(data_date, data_df, version)
            
            # 记录版本信息
            self.versions_collection.update_one(
                {"data_type": data_type, "data_date": data_date, "version": version},
                {"$set": {
                    "status": "active",
                    "fetch_success": True,
                    "record_count": len(data_df),
                    "created_at": datetime.now().isoformat()
                }},
                upsert=True
            )
            
            self.logger.info(f"[智策板块] 保存{data_type}数据成功 (日期: {data_date}, 版本: {version}, 记录数: {len(data_df)})")
            return version
            
        except Exception as e:
            self.versions_collection.update_one(
                {"data_type": data_type, "data_date": data_date, "version": version or 1},
                {"$set": {
                    "status": "failed",
                    "fetch_success": False,
                    "error_message": str(e),
                    "record_count": 0,
                    "created_at": datetime.now().isoformat()
                }},
                upsert=True
            )
            self.logger.error(f"[智策板块] 保存{data_type}数据失败: {e}")
            raise
    
    def _save_sector_data(self, data_date, data_df, version):
        """保存板块数据"""
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "data_date": data_date,
                "sector_code": row.get('sector_code', ''),
                "sector_name": row.get('sector_name', ''),
                "price": float(row.get('price', 0) or 0),
                "change_pct": float(row.get('change_pct', 0) or 0),
                "volume": float(row.get('volume', 0) or 0),
                "turnover": float(row.get('turnover', 0) or 0),
                "market_cap": float(row.get('market_cap', 0) or 0),
                "pe_ratio": float(row.get('pe_ratio', 0) or 0),
                "pb_ratio": float(row.get('pb_ratio', 0) or 0),
                "data_type": "sector_data",
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.raw_data_collection.update_one(
                {"data_date": data_date, "sector_code": doc["sector_code"], "data_type": "sector_data"},
                {"$set": doc},
                upsert=True
            )
    
    def _save_news_data(self, data_date, data_df, version):
        """保存新闻数据"""
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "news_date": data_date,
                "title": row.get('title', ''),
                "content": row.get('content', ''),
                "source": row.get('source', ''),
                "url": row.get('url', ''),
                "related_sectors": json.dumps(row.get('related_sectors', []), ensure_ascii=False),
                "sentiment_score": float(row.get('sentiment_score', 0) or 0),
                "importance_score": float(row.get('importance_score', 0) or 0),
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.news_data_collection.insert_one(doc)
    
    def get_latest_data(self, data_type, data_date=None):
        """获取最新的成功数据"""
        if self.db is None:
            return pd.DataFrame()
        
        try:
            import pymongo
            query = {"data_type": data_type, "fetch_success": True}
            if data_date:
                query["data_date"] = data_date
                
            version_doc = self.versions_collection.find_one(
                query, 
                sort=[("data_date", pymongo.DESCENDING), ("version", pymongo.DESCENDING)]
            )
            
            if not version_doc:
                self.logger.warning(f"[智策板块] 未找到{data_type}的成功数据")
                return pd.DataFrame()
            
            target_date = version_doc['data_date']
            target_version = version_doc['version']
            
            if data_type == 'sector_data':
                cursor = self.raw_data_collection.find(
                    {"data_date": target_date, "data_version": target_version}
                ).sort("sector_code", pymongo.ASCENDING)
            elif data_type == 'news_data':
                cursor = self.news_data_collection.find(
                    {"news_date": target_date, "data_version": target_version}
                ).sort("importance_score", pymongo.DESCENDING)
            else:
                return pd.DataFrame()
            
            df = pd.DataFrame(list(cursor))
            if not df.empty and '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
                df.rename(columns={'_id': 'id'}, inplace=True)
            return df
            
        except Exception as e:
            self.logger.error(f"[智策板块] 获取{data_type}数据失败: {e}")
            return pd.DataFrame()
    
    def save_analysis_report(self, data_date_range, analysis_content, 
                           recommended_sectors, summary, confidence_score=None,
                           risk_level=None, investment_horizon=None, market_outlook=None):
        """保存AI分析报告"""
        if self.db is None:
            return None
        
        if isinstance(analysis_content, dict):
            analysis_content = json.dumps(analysis_content, ensure_ascii=False, indent=2)
        
        doc = {
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "data_date_range": data_date_range,
            "analysis_content": analysis_content,
            "recommended_sectors": json.dumps(recommended_sectors, ensure_ascii=False),
            "summary": summary,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "investment_horizon": investment_horizon,
            "market_outlook": market_outlook,
            "created_at": datetime.now().isoformat()
        }
        
        result = self.reports_collection.insert_one(doc)
        report_id = str(result.inserted_id)
        self.logger.info(f"[智策板块] 分析报告已保存 (ID: {report_id})")
        return report_id
    
    def get_analysis_reports(self, limit=10):
        """获取历史分析报告"""
        if self.db is None:
            return pd.DataFrame()
            
        import pymongo
        cursor = self.reports_collection.find().sort("created_at", pymongo.DESCENDING).limit(limit)
        df = pd.DataFrame(list(cursor))
        if not df.empty and '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
            df.rename(columns={'_id': 'id'}, inplace=True)
        return df
    
    def get_analysis_report(self, report_id):
        """获取单个分析报告详情"""
        if self.db is None:
            return None
            
        try:
            report = self.reports_collection.find_one({"_id": ObjectId(report_id)})
            if report:
                report['id'] = str(report.pop('_id'))
                try:
                    if report.get('analysis_content'):
                        report['analysis_content_parsed'] = json.loads(report['analysis_content'])
                    if report.get('recommended_sectors'):
                        report['recommended_sectors_parsed'] = json.loads(report['recommended_sectors'])
                except json.JSONDecodeError as e:
                    self.logger.warning(f"[智策板块] JSON解析失败: {e}")
                return report
        except Exception:
            pass
        return None
    
    def delete_analysis_report(self, report_id):
        """删除分析报告"""
        if self.db is None:
            return False
            
        try:
            self.tracking_collection.delete_many({"analysis_id": str(report_id)})
            result = self.reports_collection.delete_one({"_id": ObjectId(report_id)})
            
            if result.deleted_count > 0:
                self.logger.info(f"[智策板块] 报告删除成功 (ID: {report_id})")
                return True
            else:
                self.logger.warning(f"[智策板块] 未找到要删除的报告 (ID: {report_id})")
                return False
        except Exception as e:
            self.logger.error(f"[智策板块] 删除报告失败: {e}")
            return False
    
    def get_data_versions(self, data_type, limit=10):
        """获取数据版本历史"""
        if self.db is None:
            return pd.DataFrame()
            
        import pymongo
        cursor = self.versions_collection.find({"data_type": data_type}).sort(
            [("data_date", pymongo.DESCENDING), ("version", pymongo.DESCENDING)]
        ).limit(limit)
        
        df = pd.DataFrame(list(cursor))
        if not df.empty and '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
            df.rename(columns={'_id': 'id'}, inplace=True)
        return df
    
    def save_sector_raw_data(self, data_date, data_type, data_df):
        """保存板块原始数据"""
        if self.db is None: return
        
        is_empty = False
        if data_df is None:
            is_empty = True
        elif hasattr(data_df, 'empty'):
            is_empty = data_df.empty
        elif isinstance(data_df, (list, tuple, set, dict)):
            is_empty = len(data_df) == 0
            
        if is_empty:
            self.logger.warning(f"[智策板块] {data_type}数据为空，跳过保存")
            return
        
        try:
            version = self._get_next_version(data_date, data_type)
            
            if data_type in ['industry', 'concept']:
                self._save_sector_data_raw(data_date, data_df, data_type, version)
            elif data_type == 'fund_flow':
                self._save_fund_flow_data(data_date, data_df, version)
            elif data_type == 'market_overview':
                self._save_market_overview_data(data_date, data_df, version)
            elif data_type == 'north_fund':
                self._save_north_fund_data(data_date, data_df, version)
            elif data_type == 'news':
                self._save_news_data_raw(data_date, data_df, version)
            
            self.versions_collection.update_one(
                {"data_date": data_date, "data_type": data_type, "version": version},
                {"$set": {
                    "fetch_success": True,
                    "record_count": len(data_df),
                    "created_at": datetime.now().isoformat()
                }},
                upsert=True
            )
            
            self.logger.info(f"[智策板块] {data_type}数据保存成功 (日期: {data_date}, 版本: {version}, 记录数: {len(data_df)})")
            
        except Exception as e:
            self.logger.error(f"[智策板块] 保存{data_type}数据失败: {e}")
            raise
    
    def _save_sector_data_raw(self, data_date, data_df, data_type, version):
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "data_date": data_date,
                "sector_code": str(row.get('板块代码', row.get('sector_code', ''))),
                "sector_name": str(row.get('板块名称', row.get('sector_name', ''))),
                "price": float(row.get('最新价', row.get('price', 0))) if pd.notna(row.get('最新价', row.get('price', 0))) else 0,
                "change_pct": float(row.get('涨跌幅', row.get('change_pct', 0))) if pd.notna(row.get('涨跌幅', row.get('change_pct', 0))) else 0,
                "volume": float(row.get('成交量', row.get('volume', 0))) if pd.notna(row.get('成交量', row.get('volume', 0))) else 0,
                "turnover": float(row.get('成交额', row.get('turnover', 0))) if pd.notna(row.get('成交额', row.get('turnover', 0))) else 0,
                "market_cap": float(row.get('总市值', row.get('market_cap', 0))) if pd.notna(row.get('总市值', row.get('market_cap', 0))) else 0,
                "pe_ratio": float(row.get('市盈率', row.get('pe_ratio', 0))) if pd.notna(row.get('市盈率', row.get('pe_ratio', 0))) else 0,
                "pb_ratio": float(row.get('市净率', row.get('pb_ratio', 0))) if pd.notna(row.get('市净率', row.get('pb_ratio', 0))) else 0,
                "data_type": data_type,
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.raw_data_collection.update_one(
                {"data_date": data_date, "sector_code": doc["sector_code"], "data_type": data_type},
                {"$set": doc},
                upsert=True
            )
            
    def _save_fund_flow_data(self, data_date, data_df, version):
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "data_date": data_date,
                "sector_code": str(row.get('行业', '')),
                "sector_name": str(row.get('行业', '')),
                "price": float(row.get('主力净流入-净额', 0)) if pd.notna(row.get('主力净流入-净额', 0)) else 0,
                "change_pct": float(row.get('主力净流入-净占比', 0)) if pd.notna(row.get('主力净流入-净占比', 0)) else 0,
                "volume": float(row.get('超大单净流入-净额', 0)) if pd.notna(row.get('超大单净流入-净额', 0)) else 0,
                "turnover": float(row.get('超大单净流入-净占比', 0)) if pd.notna(row.get('超大单净流入-净占比', 0)) else 0,
                "market_cap": float(row.get('大单净流入-净额', 0)) if pd.notna(row.get('大单净流入-净额', 0)) else 0,
                "pe_ratio": float(row.get('大单净流入-净占比', 0)) if pd.notna(row.get('大单净流入-净占比', 0)) else 0,
                "pb_ratio": 0,
                "data_type": "fund_flow",
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.raw_data_collection.update_one(
                {"data_date": data_date, "sector_code": doc["sector_code"], "data_type": "fund_flow"},
                {"$set": doc},
                upsert=True
            )

    def _save_market_overview_data(self, data_date, data_df, version):
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "data_date": data_date,
                "sector_code": str(row.get('名称', '')),
                "sector_name": str(row.get('名称', '')),
                "price": float(row.get('最新价', 0)) if pd.notna(row.get('最新价', 0)) else 0,
                "change_pct": float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅', 0)) else 0,
                "volume": float(row.get('成交量', 0)) if pd.notna(row.get('成交量', 0)) else 0,
                "turnover": float(row.get('成交额', 0)) if pd.notna(row.get('成交额', 0)) else 0,
                "market_cap": 0, "pe_ratio": 0, "pb_ratio": 0,
                "data_type": "market_overview",
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.raw_data_collection.update_one(
                {"data_date": data_date, "sector_code": doc["sector_code"], "data_type": "market_overview"},
                {"$set": doc},
                upsert=True
            )

    def _save_north_fund_data(self, data_date, data_df, version):
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "data_date": data_date,
                "sector_code": str(row.get('代码', '')),
                "sector_name": str(row.get('名称', '')),
                "price": float(row.get('收盘价', 0)) if pd.notna(row.get('收盘价', 0)) else 0,
                "change_pct": float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅', 0)) else 0,
                "volume": float(row.get('持股数量', 0)) if pd.notna(row.get('持股数量', 0)) else 0,
                "turnover": float(row.get('持股市值', 0)) if pd.notna(row.get('持股市值', 0)) else 0,
                "market_cap": float(row.get('持股变化', 0)) if pd.notna(row.get('持股变化', 0)) else 0,
                "pe_ratio": 0, "pb_ratio": 0,
                "data_type": "north_fund",
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.raw_data_collection.update_one(
                {"data_date": data_date, "sector_code": doc["sector_code"], "data_type": "north_fund"},
                {"$set": doc},
                upsert=True
            )

    def _save_news_data_raw(self, data_date, data_df, version):
        if self.db is None: return
        for _, row in data_df.iterrows():
            doc = {
                "news_date": data_date,
                "title": str(row.get('新闻标题', row.get('title', ''))),
                "content": str(row.get('新闻内容', row.get('content', ''))),
                "source": str(row.get('新闻来源', row.get('source', ''))),
                "url": str(row.get('新闻链接', row.get('url', ''))),
                "related_sectors": json.dumps([], ensure_ascii=False),
                "sentiment_score": 0,
                "importance_score": 0,
                "data_version": version,
                "created_at": datetime.now().isoformat()
            }
            self.news_data_collection.insert_one(doc)

    def cleanup_old_data(self, data_type, keep_days=30):
        """清理旧数据"""
        if self.db is None: return 0
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=keep_days)).strftime('%Y-%m-%d')
            
            if data_type == 'sector_data':
                result = self.raw_data_collection.delete_many({"data_date": {"$lt": cutoff_date}})
            elif data_type == 'news_data':
                result = self.news_data_collection.delete_many({"news_date": {"$lt": cutoff_date}})
            else:
                return 0
                
            deleted_count = result.deleted_count
            self.versions_collection.delete_many({"data_type": data_type, "data_date": {"$lt": cutoff_date}})
            
            self.logger.info(f"[智策板块] 清理{data_type}旧数据完成，删除{deleted_count}条记录")
            return deleted_count
        except Exception as e:
            self.logger.error(f"[智策板块] 清理{data_type}旧数据失败: {e}")
            return 0

    def save_news_data(self, news_list, news_date, source="akshare"):
        """保存新闻列表（字典列表）"""
        if not news_list or self.db is None:
            self.logger.warning("[智策板块] 新闻列表为空或数据库未连接，跳过保存")
            return 0

        try:
            version = self._get_next_version(news_date, 'news')
            inserted = 0
            for item in news_list:
                doc = {
                    "news_date": str(news_date),
                    "title": str(item.get('title', '')),
                    "content": str(item.get('content', '')),
                    "source": str(item.get('source', source)),
                    "url": str(item.get('url', '')),
                    "related_sectors": json.dumps(item.get('related_sectors', []), ensure_ascii=False),
                    "sentiment_score": float(item.get('sentiment_score', 0) or 0),
                    "importance_score": float(item.get('importance_score', 0) or 0),
                    "data_version": version,
                    "created_at": datetime.now().isoformat()
                }
                self.news_data_collection.insert_one(doc)
                inserted += 1

            self.versions_collection.update_one(
                {"data_date": str(news_date), "data_type": "news", "version": version},
                {"$set": {
                    "fetch_success": True,
                    "record_count": inserted,
                    "created_at": datetime.now().isoformat()
                }},
                upsert=True
            )

            self.logger.info(f"[智策板块] 保存新闻数据成功 (日期: {news_date}, 版本: {version}, 记录数: {inserted})")
            return inserted
        except Exception as e:
            self.logger.error(f"[智策板块] 保存新闻数据失败: {e}")
            return 0

    def _get_next_version(self, data_date: str, data_type: str) -> int:
        """获取下一个版本号"""
        if self.db is None: return 1
        import pymongo
        doc = self.versions_collection.find_one(
            {"data_type": data_type, "data_date": data_date},
            sort=[("version", pymongo.DESCENDING)]
        )
        return int(doc['version']) + 1 if doc else 1

    def get_latest_raw_data(self, key: str, within_hours: int = 24):
        """获取最近within_hours小时内的原始数据"""
        if self.db is None: return None
        
        key_map = {
            'sectors': 'industry',
            'concepts': 'concept',
            'fund_flow': 'fund_flow',
            'market_overview': 'market_overview',
            'north_flow': 'north_fund'
        }
        data_type = key_map.get(key)
        if not data_type:
            return None

        try:
            cutoff = (pd.Timestamp.now() - pd.Timedelta(hours=within_hours)).isoformat()
            
            import pymongo
            version_doc = self.versions_collection.find_one(
                {
                    "data_type": data_type, 
                    "fetch_success": True,
                    "created_at": {"$gte": cutoff}
                },
                sort=[("data_date", pymongo.DESCENDING), ("version", pymongo.DESCENDING)]
            )

            if not version_doc:
                return None

            data_date = version_doc['data_date']
            version = int(version_doc['version'])

            cursor = self.raw_data_collection.find(
                {"data_type": data_type, "data_date": data_date, "data_version": version}
            )
            raw_df = pd.DataFrame(list(cursor))

            if raw_df.empty:
                return None

            if key in ['sectors', 'concepts']:
                result = {}
                for _, row in raw_df.iterrows():
                    name = str(row.get('sector_name', ''))
                    result[name] = {
                        'name': name,
                        'change_pct': float(row.get('change_pct', 0) or 0),
                        'price': float(row.get('price', 0) or 0),
                        'volume': float(row.get('volume', 0) or 0),
                        'turnover': float(row.get('turnover', 0) or 0),
                        'market_cap': float(row.get('market_cap', 0) or 0),
                        'pe_ratio': float(row.get('pe_ratio', 0) or 0),
                        'pb_ratio': float(row.get('pb_ratio', 0) or 0),
                    }
                return {'data_date': data_date, 'data_content': result}

            if key == 'fund_flow':
                today = []
                for _, row in raw_df.iterrows():
                    name = str(row.get('sector_name', ''))
                    today.append({
                        'sector': name,
                        'main_net_inflow': float(row.get('price', 0) or 0),
                        'main_net_inflow_pct': float(row.get('change_pct', 0) or 0),
                        'super_large_net_inflow': float(row.get('volume', 0) or 0),
                        'super_large_net_inflow_pct': float(row.get('turnover', 0) or 0),
                        'large_net_inflow': float(row.get('market_cap', 0) or 0),
                        'large_net_inflow_pct': float(row.get('pe_ratio', 0) or 0),
                        'medium_net_inflow': 0, 'small_net_inflow': 0
                    })
                return {'data_date': data_date, 'data_content': {'today': today}}

            if key == 'market_overview':
                overview = {}
                for _, row in raw_df.iterrows():
                    name = str(row.get('sector_name', ''))
                    entry = {
                        'price': float(row.get('price', 0) or 0),
                        'change_pct': float(row.get('change_pct', 0) or 0),
                        'turnover': float(row.get('turnover', 0) or 0),
                        'volume': float(row.get('volume', 0) or 0)
                    }
                    if '上证' in name or '沪指' in name or 'SH' in name:
                        overview['sh_index'] = entry
                    elif '深证' in name or 'SZ' in name:
                        overview['sz_index'] = entry
                    elif '创业' in name or 'CYB' in name:
                        overview['cyb_index'] = entry
                return {'data_date': data_date, 'data_content': overview}

            if key == 'north_flow':
                total_value = float(raw_df['turnover'].sum()) if not raw_df.empty else 0
                return {'data_date': data_date, 'data_content': {'north_total_amount': total_value, 'history': []}}

            return None
        except Exception as e:
            self.logger.error(f"[智策板块] 获取最近原始数据失败: {e}")
            return None

    def get_latest_news_data(self, within_hours: int = 24):
        """获取最近within_hours小时的新闻列表"""
        if self.db is None: return None
        try:
            cutoff = (pd.Timestamp.now() - pd.Timedelta(hours=within_hours)).isoformat()
            
            import pymongo
            cursor = self.news_data_collection.find(
                {"created_at": {"$gte": cutoff}}
            ).sort([("importance_score", pymongo.DESCENDING), ("created_at", pymongo.DESCENDING)])
            
            df = pd.DataFrame(list(cursor))
            if df.empty:
                return None
                
            news = []
            for _, row in df.iterrows():
                try:
                    related = json.loads(row.get('related_sectors', '[]'))
                except Exception:
                    related = []
                news.append({
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'source': row.get('source', ''),
                    'url': row.get('url', ''),
                    'related_sectors': related,
                    'sentiment_score': float(row.get('sentiment_score', 0) or 0),
                    'importance_score': float(row.get('importance_score', 0) or 0),
                    'news_date': row.get('news_date', '')
                })
            return {
                'data_date': df.iloc[0]['news_date'] if not df.empty else None,
                'data_content': news
            }
        except Exception as e:
            self.logger.error(f"[智策板块] 获取最近新闻数据失败: {e}")
            return None