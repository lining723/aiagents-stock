import sqlite3
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class AnalysisHistoryDatabase:
    def __init__(self, db_path="db/stock_analysis.db"):
        """初始化数据库连接（可以与原有的分析记录在同一个DB文件，只是不同的表）"""
        # Ensure db_path uses absolute path relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(base_dir, db_path)
        
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化分析历史表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    ai_report TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化分析历史表失败: {str(e)}", exc_info=True)
    
    def save_history(self, symbol: str, name: str, ai_report: str) -> int:
        """保存一条 AI 分析历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            created_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO ai_analysis_history 
                (symbol, name, ai_report, created_at)
                VALUES (?, ?, ?, ?)
            ''', (symbol, name, ai_report, created_at))
            
            history_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return history_id
        except Exception as e:
            logger.error(f"保存分析历史失败: {str(e)}", exc_info=True)
            return -1
            
    def get_history_list(self, limit: int = 50, offset: int = 0):
        """获取分析历史列表（不包含完整的 ai_report，以减少传输体积）"""
        try:
            conn = sqlite3.connect(self.db_path)
            # 使用 row_factory 使得返回结果可以像字典一样访问
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, symbol, name, created_at
                FROM ai_analysis_history 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            records = cursor.fetchall()
            conn.close()
            
            return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"获取分析历史列表失败: {str(e)}", exc_info=True)
            return []
            
    def get_history_by_id(self, history_id: int):
        """根据 ID 获取完整的分析历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM ai_analysis_history WHERE id = ?
            ''', (history_id,))
            
            record = cursor.fetchone()
            conn.close()
            
            if record:
                return dict(record)
            return None
        except Exception as e:
            logger.error(f"获取单条分析历史失败: {str(e)}", exc_info=True)
            return None
            
    def delete_history(self, history_id: int) -> bool:
        """删除指定分析历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM ai_analysis_history WHERE id = ?', (history_id,))
            success = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return success
        except Exception as e:
            logger.error(f"删除分析历史失败: {str(e)}", exc_info=True)
            return False
            
    def clear_all_history(self) -> int:
        """清空所有历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM ai_analysis_history')
            count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"清空分析历史失败: {str(e)}", exc_info=True)
            return 0
