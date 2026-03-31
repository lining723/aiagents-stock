"""
新闻流量数据库模块 (MongoDB 版)
用于存储和管理新闻流量监测数据
包含：快照、新闻、情绪、预警、AI分析、定时任务日志
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import pymongo
from bson import ObjectId

from utils.logger import get_logger
from utils.mongo_client import mongo_client

logger = get_logger(__name__)


class NewsFlowDatabase:
    """新闻流量数据库管理类"""
    
    def __init__(self):
        self.db = mongo_client.db
        if self.db is not None:
            self.init_database()
        else:
            logger.error("MongoDB 连接未初始化，NewsFlowDatabase 无法正常工作")
    
    def init_database(self):
        """初始化数据库索引和默认配置"""
        try:
            # 创建各集合索引
            self.db['flow_snapshots'].create_index([("created_at", pymongo.DESCENDING)])
            self.db['platform_news'].create_index([("snapshot_id", pymongo.ASCENDING)])
            self.db['stock_related_news'].create_index([("snapshot_id", pymongo.ASCENDING)])
            self.db['stock_related_news'].create_index([("title", "text"), ("content", "text")])
            self.db['hot_topics'].create_index([("snapshot_id", pymongo.ASCENDING)])
            self.db['flow_statistics'].create_index([("date", pymongo.DESCENDING)], unique=True)
            self.db['sentiment_records'].create_index([("snapshot_id", pymongo.ASCENDING)])
            self.db['flow_alerts'].create_index([("created_at", pymongo.DESCENDING)])
            self.db['ai_analysis'].create_index([("snapshot_id", pymongo.ASCENDING)])
            self.db['scheduler_logs'].create_index([("executed_at", pymongo.DESCENDING)])
            self.db['alert_config'].create_index([("config_key", pymongo.ASCENDING)], unique=True)
            
            # 初始化预警配置默认值
            default_configs = [
                ('heat_threshold', '800', '热度飙升阈值'),
                ('rank_change_threshold', '10', '排名变化阈值'),
                ('sentiment_high_threshold', '90', '情绪高位阈值'),
                ('sentiment_low_threshold', '20', '情绪低位阈值'),
                ('viral_k_threshold', '1.5', 'K值阈值'),
                ('alert_enabled', 'true', '预警开关'),
                ('notification_enabled', 'true', '通知开关'),
            ]
            
            for key, value, desc in default_configs:
                self.db['alert_config'].update_one(
                    {"config_key": key},
                    {"$setOnInsert": {
                        "config_key": key,
                        "config_value": value,
                        "description": desc,
                        "updated_at": datetime.now()
                    }},
                    upsert=True
                )
                
            logger.info("✅ 新闻流量数据库初始化完成 (MongoDB)")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            
    def _format_doc(self, doc: dict) -> dict:
        """格式化 MongoDB 文档，将 _id 转换为 id 字符串"""
        if not doc:
            return None
        formatted = doc.copy()
        if '_id' in formatted:
            formatted['id'] = str(formatted.pop('_id'))
        if 'snapshot_id' in formatted and isinstance(formatted['snapshot_id'], ObjectId):
            formatted['snapshot_id'] = str(formatted['snapshot_id'])
        return formatted

    # ==================== 快照相关方法 ====================
    
    def save_flow_snapshot(self, flow_data: Dict, platforms_data: List[Dict], 
                           stock_news: List[Dict], hot_topics: List[Dict]) -> str:
        """保存完整的流量快照"""
        try:
            # 1. 保存快照主表
            snapshot_doc = {
                "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_platforms": len(platforms_data),
                "success_count": sum(1 for p in platforms_data if p.get('success')),
                "total_score": flow_data['total_score'],
                "flow_level": flow_data['level'],
                "social_score": flow_data.get('social_score', 0),
                "news_score": flow_data.get('news_score', 0),
                "finance_score": flow_data.get('finance_score', 0),
                "tech_score": flow_data.get('tech_score', 0),
                "analysis": flow_data.get('analysis', ''),
                "created_at": datetime.now()
            }
            
            result = self.db['flow_snapshots'].insert_one(snapshot_doc)
            snapshot_id = str(result.inserted_id)
            
            # 2. 保存平台新闻
            platform_news_docs = []
            for platform_data in platforms_data:
                if not platform_data.get('success'):
                    continue
                for news in platform_data.get('data', []):
                    platform_news_docs.append({
                        "snapshot_id": snapshot_id,
                        "platform": platform_data['platform'],
                        "platform_name": platform_data['platform_name'],
                        "category": platform_data['category'],
                        "weight": platform_data['weight'],
                        "title": news.get('title') or '',
                        "content": news.get('content') or '',
                        "url": news.get('url') or '',
                        "source": news.get('source') or '',
                        "publish_time": news.get('publish_time') or '',
                        "rank": news.get('rank', 0),
                        "created_at": datetime.now()
                    })
            if platform_news_docs:
                self.db['platform_news'].insert_many(platform_news_docs)
            
            # 3. 保存股票相关新闻
            stock_news_docs = []
            for news in stock_news:
                stock_news_docs.append({
                    "snapshot_id": snapshot_id,
                    "platform": news['platform'],
                    "platform_name": news['platform_name'],
                    "category": news['category'],
                    "weight": news['weight'],
                    "title": news['title'],
                    "content": news.get('content') or '',
                    "url": news.get('url') or '',
                    "source": news.get('source') or '',
                    "publish_time": news.get('publish_time') or '',
                    "matched_keywords": news.get('matched_keywords', []),
                    "keyword_count": news.get('keyword_count', 0),
                    "score": news.get('score', 0),
                    "created_at": datetime.now()
                })
            if stock_news_docs:
                self.db['stock_related_news'].insert_many(stock_news_docs)
            
            # 4. 保存热门话题
            hot_topic_docs = []
            for topic in hot_topics:
                hot_topic_docs.append({
                    "snapshot_id": snapshot_id,
                    "topic": topic['topic'],
                    "count": topic['count'],
                    "heat": topic['heat'],
                    "cross_platform": topic.get('cross_platform', 0),
                    "sources": topic.get('sources', []),
                    "created_at": datetime.now()
                })
            if hot_topic_docs:
                self.db['hot_topics'].insert_many(hot_topic_docs)
            
            # 5. 更新每日统计
            self._update_daily_statistics(flow_data['total_score'], hot_topics)
            
            logger.info(f"✅ 保存流量快照成功，ID: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"❌ 保存流量快照失败: {e}")
            raise
    
    def _update_daily_statistics(self, score: int, hot_topics: List[Dict]):
        """更新每日统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        stat = self.db['flow_statistics'].find_one({"date": today})
        
        if stat:
            old_avg = stat.get('avg_score', 0)
            old_count = stat.get('snapshot_count', 0)
            new_avg = int((old_avg * old_count + score) / (old_count + 1))
            new_max = max(stat.get('max_score', 0), score)
            new_min = min(stat.get('min_score', 999999), score)
            
            old_topics = stat.get('top_topics', [])
            new_topics = old_topics + [t['topic'] for t in hot_topics[:10]]
            topic_counter = Counter(new_topics)
            top_topics = [topic for topic, _ in topic_counter.most_common(20)]
            
            self.db['flow_statistics'].update_one(
                {"date": today},
                {"$set": {
                    "avg_score": new_avg,
                    "max_score": new_max,
                    "min_score": new_min,
                    "snapshot_count": old_count + 1,
                    "top_topics": top_topics
                }}
            )
        else:
            top_topics = [t['topic'] for t in hot_topics[:20]]
            self.db['flow_statistics'].insert_one({
                "date": today,
                "avg_score": score,
                "max_score": score,
                "min_score": score,
                "snapshot_count": 1,
                "top_topics": top_topics,
                "created_at": datetime.now()
            })
    
    def get_latest_snapshot(self) -> Optional[Dict]:
        """获取最新的流量快照"""
        doc = self.db['flow_snapshots'].find_one(sort=[("created_at", pymongo.DESCENDING)])
        return self._format_doc(doc)
    
    def get_recent_snapshots(self, limit: int = 10) -> List[Dict]:
        """获取最近的流量快照列表"""
        cursor = self.db['flow_snapshots'].find().sort("created_at", pymongo.DESCENDING).limit(limit)
        return [self._format_doc(doc) for doc in cursor]
    
    def get_snapshot_detail(self, snapshot_id: str) -> Dict:
        """获取快照详细信息"""
        try:
            snapshot = self.db['flow_snapshots'].find_one({"_id": ObjectId(snapshot_id)})
            if not snapshot:
                return {}
            
            stock_news = list(self.db['stock_related_news'].find(
                {"snapshot_id": str(snapshot_id)}
            ).sort([("score", pymongo.DESCENDING), ("weight", pymongo.DESCENDING)]))
            
            hot_topics = list(self.db['hot_topics'].find(
                {"snapshot_id": str(snapshot_id)}
            ).sort("heat", pymongo.DESCENDING))
            
            sentiment = self.db['sentiment_records'].find_one(
                {"snapshot_id": str(snapshot_id)},
                sort=[("created_at", pymongo.DESCENDING)]
            )
            
            ai_analysis = self.db['ai_analysis'].find_one(
                {"snapshot_id": str(snapshot_id)},
                sort=[("created_at", pymongo.DESCENDING)]
            )
            
            return {
                'snapshot': self._format_doc(snapshot),
                'stock_news': [self._format_doc(d) for d in stock_news],
                'hot_topics': [self._format_doc(d) for d in hot_topics],
                'sentiment': self._format_doc(sentiment),
                'ai_analysis': self._format_doc(ai_analysis),
            }
        except Exception as e:
            logger.error(f"获取快照详情失败: {e}")
            return {}
    
    def get_history_snapshots(self, limit: int = 50) -> List[Dict]:
        """获取历史快照列表"""
        cursor = self.db['flow_snapshots'].find(
            projection={"id": 1, "fetch_time": 1, "total_score": 1, "flow_level": 1, 
                        "success_count": 1, "total_platforms": 1, "analysis": 1}
        ).sort("created_at", pymongo.DESCENDING).limit(limit)
        return [self._format_doc(doc) for doc in cursor]
    
    def get_daily_statistics(self, days: int = 7) -> List[Dict]:
        """获取每日统计数据"""
        cursor = self.db['flow_statistics'].find().sort("date", pymongo.DESCENDING).limit(days)
        return [self._format_doc(doc) for doc in cursor]
    
    def get_recent_scores(self, hours: int = 24) -> List[Dict]:
        """获取最近N小时的得分记录"""
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        cursor = self.db['flow_snapshots'].find(
            {"fetch_time": {"$gte": since}},
            projection={"id": 1, "fetch_time": 1, "total_score": 1, "flow_level": 1}
        ).sort("fetch_time", pymongo.ASCENDING)
        return [self._format_doc(doc) for doc in cursor]
    
    def search_stock_news(self, keyword: str, limit: int = 50) -> List[Dict]:
        """搜索股票相关新闻"""
        query = {
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"content": {"$regex": keyword, "$options": "i"}}
            ]
        }
        cursor = self.db['stock_related_news'].find(query).sort("created_at", pymongo.DESCENDING).limit(limit)
        
        results = []
        for doc in cursor:
            news = self._format_doc(doc)
            # Fetch related snapshot info
            snapshot = self.db['flow_snapshots'].find_one({"_id": ObjectId(news['snapshot_id'])})
            if snapshot:
                news['fetch_time'] = snapshot.get('fetch_time')
                news['flow_level'] = snapshot.get('flow_level')
            results.append(news)
        return results
    
    # ==================== 情绪记录相关方法 ====================
    
    def save_sentiment_record(self, snapshot_id: str, sentiment_data: Dict) -> str:
        """保存情绪记录"""
        doc = {
            "snapshot_id": str(snapshot_id),
            "sentiment_index": sentiment_data.get('sentiment_index', 50),
            "sentiment_class": sentiment_data.get('sentiment_class', '中性'),
            "flow_stage": sentiment_data.get('flow_stage', '未知'),
            "momentum": sentiment_data.get('momentum', 0),
            "viral_k": sentiment_data.get('viral_k', 1.0),
            "flow_type": sentiment_data.get('flow_type', '未知'),
            "stage_analysis": sentiment_data.get('stage_analysis', ''),
            "created_at": datetime.now()
        }
        result = self.db['sentiment_records'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_sentiment_history(self, limit: int = 50) -> List[Dict]:
        """获取情绪历史记录"""
        cursor = self.db['sentiment_records'].find().sort("created_at", pymongo.DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            record = self._format_doc(doc)
            snapshot = self.db['flow_snapshots'].find_one({"_id": ObjectId(record['snapshot_id'])})
            if snapshot:
                record['fetch_time'] = snapshot.get('fetch_time')
                record['total_score'] = snapshot.get('total_score')
            results.append(record)
        return results
    
    def get_latest_sentiment(self) -> Optional[Dict]:
        """获取最新情绪记录"""
        doc = self.db['sentiment_records'].find_one(sort=[("created_at", pymongo.DESCENDING)])
        if doc:
            record = self._format_doc(doc)
            snapshot = self.db['flow_snapshots'].find_one({"_id": ObjectId(record['snapshot_id'])})
            if snapshot:
                record['fetch_time'] = snapshot.get('fetch_time')
                record['total_score'] = snapshot.get('total_score')
                record['flow_level'] = snapshot.get('flow_level')
            return record
        return None
    
    # ==================== 预警相关方法 ====================
    
    def save_alert(self, alert_data: Dict) -> str:
        """保存预警记录"""
        doc = {
            "alert_type": alert_data['alert_type'],
            "alert_level": alert_data.get('alert_level', 'info'),
            "title": alert_data['title'],
            "content": alert_data.get('content', ''),
            "related_topics": alert_data.get('related_topics', []),
            "trigger_value": str(alert_data.get('trigger_value', '')),
            "threshold_value": str(alert_data.get('threshold_value', '')),
            "is_notified": 1 if alert_data.get('is_notified') else 0,
            "snapshot_id": str(alert_data.get('snapshot_id')) if alert_data.get('snapshot_id') else None,
            "created_at": datetime.now()
        }
        result = self.db['flow_alerts'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_alerts(self, days: int = 7, alert_type: str = None) -> List[Dict]:
        """获取预警记录"""
        since = datetime.now() - timedelta(days=days)
        query = {"created_at": {"$gte": since}}
        if alert_type:
            query["alert_type"] = alert_type
            
        cursor = self.db['flow_alerts'].find(query).sort("created_at", pymongo.DESCENDING)
        return [self._format_doc(doc) for doc in cursor]
    
    def get_unnotified_alerts(self) -> List[Dict]:
        """获取未通知的预警"""
        cursor = self.db['flow_alerts'].find({"is_notified": 0}).sort("created_at", pymongo.DESCENDING)
        return [self._format_doc(doc) for doc in cursor]
    
    def mark_alert_notified(self, alert_id: str):
        """标记预警为已通知"""
        self.db['flow_alerts'].update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"is_notified": 1}}
        )
    
    # ==================== AI分析相关方法 ====================
    
    def save_ai_analysis(self, snapshot_id: str, analysis_data: Dict) -> str:
        """保存AI分析结果"""
        doc = {
            "snapshot_id": str(snapshot_id),
            "affected_sectors": analysis_data.get('affected_sectors', []),
            "recommended_stocks": analysis_data.get('recommended_stocks', []),
            "risk_level": analysis_data.get('risk_level', '未知'),
            "risk_factors": analysis_data.get('risk_factors', []),
            "advice": analysis_data.get('advice', '观望'),
            "confidence": analysis_data.get('confidence', 50),
            "summary": analysis_data.get('summary', ''),
            "raw_response": analysis_data.get('raw_response', ''),
            "model_used": analysis_data.get('model_used', 'unknown'),
            "analysis_time": analysis_data.get('analysis_time', 0),
            "created_at": datetime.now()
        }
        result = self.db['ai_analysis'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_latest_ai_analysis(self) -> Optional[Dict]:
        """获取最新AI分析结果"""
        doc = self.db['ai_analysis'].find_one(sort=[("created_at", pymongo.DESCENDING)])
        if doc:
            analysis = self._format_doc(doc)
            snapshot = self.db['flow_snapshots'].find_one({"_id": ObjectId(analysis['snapshot_id'])})
            if snapshot:
                analysis['fetch_time'] = snapshot.get('fetch_time')
                analysis['total_score'] = snapshot.get('total_score')
                analysis['flow_level'] = snapshot.get('flow_level')
            return analysis
        return None
    
    def get_ai_analysis_history(self, limit: int = 20) -> List[Dict]:
        """获取AI分析历史"""
        cursor = self.db['ai_analysis'].find().sort("created_at", pymongo.DESCENDING).limit(limit)
        results = []
        for doc in cursor:
            analysis = self._format_doc(doc)
            snapshot = self.db['flow_snapshots'].find_one({"_id": ObjectId(analysis['snapshot_id'])})
            if snapshot:
                analysis['fetch_time'] = snapshot.get('fetch_time')
                analysis['total_score'] = snapshot.get('total_score')
                analysis['flow_level'] = snapshot.get('flow_level')
            results.append(analysis)
        return results
    
    # ==================== 定时任务日志相关方法 ====================
    
    def save_scheduler_log(self, task_name: str, task_type: str, 
                           status: str, message: str = '', 
                           duration: float = 0, snapshot_id: str = None) -> str:
        """保存定时任务日志"""
        doc = {
            "task_name": task_name,
            "task_type": task_type,
            "status": status,
            "message": message,
            "duration": duration,
            "snapshot_id": str(snapshot_id) if snapshot_id else None,
            "executed_at": datetime.now()
        }
        result = self.db['scheduler_logs'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_scheduler_logs(self, days: int = 7, task_type: str = None) -> List[Dict]:
        """获取定时任务日志"""
        since = datetime.now() - timedelta(days=days)
        query = {"executed_at": {"$gte": since}}
        if task_type:
            query["task_type"] = task_type
            
        cursor = self.db['scheduler_logs'].find(query).sort("executed_at", pymongo.DESCENDING)
        return [self._format_doc(doc) for doc in cursor]
    
    # ==================== 预警配置相关方法 ====================
    
    def get_alert_config(self, key: str) -> Optional[str]:
        """获取预警配置"""
        doc = self.db['alert_config'].find_one({"config_key": key})
        return doc['config_value'] if doc else None
    
    def set_alert_config(self, key: str, value: str, description: str = None):
        """设置预警配置"""
        self.db['alert_config'].update_one(
            {"config_key": key},
            {"$set": {
                "config_value": value,
                "description": description,
                "updated_at": datetime.now()
            }},
            upsert=True
        )
    
    def get_all_alert_configs(self) -> Dict[str, str]:
        """获取所有预警配置"""
        cursor = self.db['alert_config'].find()
        return {doc['config_key']: doc['config_value'] for doc in cursor}


# 全局数据库实例
news_flow_db = NewsFlowDatabase()


# 测试代码
if __name__ == "__main__":
    print("=== 测试新闻流量数据库 (MongoDB) ===")
    
    # 测试保存快照
    flow_data = {
        'total_score': 650,
        'social_score': 200,
        'news_score': 180,
        'finance_score': 220,
        'tech_score': 50,
        'level': '高',
        'analysis': '流量较高，市场活跃'
    }
    
    platforms_data = [{
        'success': True,
        'platform': 'weibo',
        'platform_name': '微博热搜',
        'category': 'social',
        'weight': 10,
        'data': [
            {'title': '某某股票大涨', 'content': '今日涨停', 'url': 'http://example.com', 
             'source': '微博', 'publish_time': '2026-01-25 10:00:00', 'rank': 1}
        ]
    }]
    
    stock_news = [{
        'platform': 'weibo',
        'platform_name': '微博热搜',
        'category': 'social',
        'weight': 10,
        'title': '某某股票大涨',
        'content': '今日涨停',
        'url': 'http://example.com',
        'source': '微博',
        'publish_time': '2026-01-25 10:00:00',
        'matched_keywords': ['股票', '涨停'],
        'keyword_count': 2,
        'score': 100
    }]
    
    hot_topics = [
        {'topic': 'AI', 'count': 50, 'heat': 95, 'cross_platform': 5, 'sources': ['微博', '抖音']},
        {'topic': '新能源', 'count': 30, 'heat': 80, 'cross_platform': 3, 'sources': ['微博']}
    ]
    
    snapshot_id = news_flow_db.save_flow_snapshot(flow_data, platforms_data, stock_news, hot_topics)
    print(f"✅ 保存快照成功，ID: {snapshot_id}")
    
    # 测试保存情绪记录
    sentiment_data = {
        'sentiment_index': 75,
        'sentiment_class': '乐观',
        'flow_stage': '加速',
        'momentum': 1.5,
        'viral_k': 1.2,
        'flow_type': '增量流量型',
        'stage_analysis': '流量正在快速上升'
    }
    sentiment_id = news_flow_db.save_sentiment_record(snapshot_id, sentiment_data)
    print(f"✅ 保存情绪记录成功，ID: {sentiment_id}")
    
    # 测试保存预警
    alert_data = {
        'alert_type': 'heat_surge',
        'alert_level': 'warning',
        'title': '热度飙升预警',
        'content': '当前流量得分650，超过阈值500',
        'related_topics': ['AI', '新能源'],
        'trigger_value': 650,
        'threshold_value': 500,
        'snapshot_id': snapshot_id
    }
    alert_id = news_flow_db.save_alert(alert_data)
    print(f"✅ 保存预警成功，ID: {alert_id}")
    
    # 测试保存AI分析
    ai_data = {
        'affected_sectors': [{'name': 'AI', 'impact': '利好', 'reason': '政策支持'}],
        'recommended_stocks': [{'code': '000001', 'name': '平安银行', 'reason': '龙头'}],
        'risk_level': '中等',
        'risk_factors': ['追高风险', '流动性风险'],
        'advice': '观望',
        'confidence': 75,
        'summary': '当前市场热度较高，建议观望',
        'model_used': 'deepseek-chat',
        'analysis_time': 2.5
    }
    ai_id = news_flow_db.save_ai_analysis(snapshot_id, ai_data)
    print(f"✅ 保存AI分析成功，ID: {ai_id}")
    
    # 测试保存任务日志
    log_id = news_flow_db.save_scheduler_log(
        '热点同步', 'sync_hotspots', 'success', 
        '成功同步22个平台', 5.2, snapshot_id
    )
    print(f"✅ 保存任务日志成功，ID: {log_id}")
    
    # 测试获取详情
    detail = news_flow_db.get_snapshot_detail(snapshot_id)
    print(f"\n快照详情:")
    print(f"  流量得分: {detail['snapshot']['total_score']}")
    print(f"  情绪指数: {detail['sentiment']['sentiment_index'] if detail['sentiment'] else 'N/A'}")
    print(f"  AI建议: {detail['ai_analysis']['advice'] if detail['ai_analysis'] else 'N/A'}")

