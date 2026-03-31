import os
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MongoDBClient:
    """MongoDB连接单例"""
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        # 默认连接本地MongoDB，如果环境变量中没有配置
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "aiagents_stock")
        
        try:
            self._client = MongoClient(uri)
            # 测试连接
            self._client.admin.command('ping')
            self._db = self._client[db_name]
            print(f"✅ 成功连接到 MongoDB: {db_name}")
        except Exception as e:
            print(f"❌ MongoDB 连接失败: {e}")
            self._db = None

    @property
    def db(self):
        """获取数据库实例"""
        if self._db is None:
            self._init_connection()
        return self._db

    @property
    def client(self):
        """获取客户端实例"""
        if self._client is None:
            self._init_connection()
        return self._client

# 全局单例实例
mongo_client = MongoDBClient()
