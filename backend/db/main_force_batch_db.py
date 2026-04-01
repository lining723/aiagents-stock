#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股批量分析历史记录数据库模块 (MongoDB 版)
"""

import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import pymongo
from bson import ObjectId

from utils.mongo_client import mongo_client

class MainForceBatchDatabase:
    """主力选股批量分析历史数据库管理类 (MongoDB 版)"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.db = mongo_client.db
        if self.db is not None:
            self._init_database()
        else:
            print("MongoDB 连接未初始化，MainForceBatchDatabase 无法正常工作")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            self.db['batch_analysis_history'].create_index([("analysis_date", pymongo.DESCENDING)])
            self.db['batch_analysis_history'].create_index([("created_at", pymongo.DESCENDING)])
            print("✅ MongoDB main_force_batch_db 索引初始化成功")
        except Exception as e:
            print(f"✅ 数据库初始化错误: {e}")

    def _format_doc(self, doc: dict) -> dict:
        """格式化 MongoDB 文档，将 _id 转换为 id 字符串"""
        if not doc:
            return None
        formatted = doc.copy()
        if '_id' in formatted:
            formatted['id'] = str(formatted.pop('_id'))
        return formatted
    
    def _clean_results_for_json(self, results: List[Dict]) -> List[Dict]:
        """
        清理结果数据，确保可以JSON序列化
        
        Args:
            results: 原始结果列表
            
        Returns:
            清理后的结果列表
        """
        def clean_value(value):
            """递归清理值"""
            # 处理None
            if value is None:
                return None
            # 处理DataFrame - 只保留前100行避免数据过大
            elif isinstance(value, pd.DataFrame):
                if len(value) > 100:
                    return value.head(100).to_dict('records')
                return value.to_dict('records')
            # 处理Series
            elif isinstance(value, pd.Series):
                return value.to_dict()
            # 处理字典 - 递归清理
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            # 处理列表 - 递归清理
            elif isinstance(value, (list, tuple)):
                return [clean_value(v) for v in value]
            # 处理基本类型
            elif isinstance(value, (str, int, float, bool)):
                return value
            # 其他对象转为字符串
            else:
                try:
                    return str(value)
                except:
                    return "无法序列化"
        
        cleaned = []
        for result in results:
            try:
                cleaned_result = {}
                for key, value in result.items():
                    cleaned_result[key] = clean_value(value)
                cleaned.append(cleaned_result)
            except Exception as e:
                # 如果单个结果清理失败，记录错误
                cleaned.append({
                    "error": f"清理失败: {str(e)}",
                    "original_keys": list(result.keys()) if isinstance(result, dict) else []
                })
        return cleaned
    
    def save_batch_analysis(
        self,
        batch_count: int,
        analysis_mode: str,
        success_count: int,
        failed_count: int,
        total_time: float,
        results: List[Dict]
    ) -> str:
        """
        保存批量分析结果
        
        Args:
            batch_count: 分析股票数量
            analysis_mode: 分析模式（sequential/parallel）
            success_count: 成功数量
            failed_count: 失败数量
            total_time: 总耗时（秒）
            results: 分析结果列表
            
        Returns:
            记录ID
        """
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cleaned_results = self._clean_results_for_json(results)
        
        doc = {
            "analysis_date": analysis_date,
            "batch_count": batch_count,
            "analysis_mode": analysis_mode,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_time": total_time,
            "results": cleaned_results,
            "created_at": datetime.now()
        }
        
        result = self.db['batch_analysis_history'].insert_one(doc)
        return str(result.inserted_id)
    
    def get_all_history(self, limit: int = 50) -> List[Dict]:
        """
        获取所有历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            历史记录列表
        """
        cursor = self.db['batch_analysis_history'].find().sort("created_at", pymongo.DESCENDING).limit(limit)
        history = []
        for doc in cursor:
            history.append(self._format_doc(doc))
        return history
    
    def get_record_by_id(self, record_id: str) -> Optional[Dict]:
        """
        根据ID获取单条记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录详情
        """
        doc = self.db['batch_analysis_history'].find_one({"_id": ObjectId(record_id)})
        return self._format_doc(doc)
    
    def delete_record(self, record_id: str) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否删除成功
        """
        result = self.db['batch_analysis_history'].delete_one({"_id": ObjectId(record_id)})
        return result.deleted_count > 0
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_records": {"$sum": 1},
                    "total_stocks": {"$sum": "$batch_count"},
                    "total_success": {"$sum": "$success_count"},
                    "total_failed": {"$sum": "$failed_count"},
                    "avg_time": {"$avg": "$total_time"}
                }
            }
        ]
        
        result = list(self.db['batch_analysis_history'].aggregate(pipeline))
        
        if not result:
            return {
                'total_records': 0,
                'total_stocks_analyzed': 0,
                'total_success': 0,
                'total_failed': 0,
                'average_time': 0,
                'success_rate': 0
            }
            
        stats = result[0]
        total_stocks = stats.get('total_stocks', 0)
        total_success = stats.get('total_success', 0)
        
        return {
            'total_records': stats.get('total_records', 0),
            'total_stocks_analyzed': total_stocks,
            'total_success': total_success,
            'total_failed': stats.get('total_failed', 0),
            'average_time': round(stats.get('avg_time', 0), 2),
            'success_rate': round(total_success / total_stocks * 100, 2) if total_stocks > 0 else 0
        }


# 全局数据库实例
batch_db = MainForceBatchDatabase()

