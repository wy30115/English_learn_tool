import os
import random
from datetime import datetime, timedelta
from ..data.database import Database
import pandas as pd


class VocabularyManager:
    """词汇管理类，提供词汇管理相关功能"""
    
    def __init__(self, db=None):
        """初始化词汇管理器
        
        Args:
            db: 数据库连接，默认为None，会创建新的连接
        """
        self.db = db if db else Database()
    
    def get_daily_words(self, count=10, difficulty_min=1, difficulty_max=3):
        """获取每日随机单词
        
        Args:
            count: 单词数量
            difficulty_min: 最小难度
            difficulty_max: 最大难度
            
        Returns:
            words: 单词列表
        """
        # 确保数据库连接
        if not self.db.conn:
            self.db.connect()
        
        # 获取随机单词
        words = self.db.get_random_words(
            count=count,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            exclude_learned=True
        )
        
        # 如果获取的单词数量不足，则放宽条件重新获取
        if len(words) < count:
            # 包含已学习的单词
            words = self.db.get_random_words(
                count=count,
                difficulty_min=difficulty_min,
                difficulty_max=difficulty_max,
                exclude_learned=False
            )
        
        # 记录学习记录
        for word in words:
            self.db.record_learning(word['id'])
        
        return words
    
    def mark_favorite(self, word_id):
        """标记为重点词汇
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        return self.db.mark_as_favorite(word_id)
    
    def unmark_favorite(self, word_id):
        """取消重点标记
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        return self.db.unmark_favorite(word_id)
    
    def is_favorite(self, word_id):
        """检查单词是否为重点词汇
        
        Args:
            word_id: 单词ID
            
        Returns:
            is_favorite: 是否为重点词汇
        """
        if not self.db.conn:
            self.db.connect()
        
        self.db.cursor.execute(
            "SELECT id FROM favorite WHERE word_id = ?", 
            (word_id,)
        )
        return self.db.cursor.fetchone() is not None
    
    def get_favorites(self, limit=100, offset=0):
        """获取重点词汇列表
        
        Args:
            limit: 数量限制
            offset: 偏移量
            
        Returns:
            words: 单词列表
        """
        return self.db.get_favorite_words(limit, offset)
    
    def search_vocabulary(self, keyword, limit=50):
        """搜索词汇
        
        Args:
            keyword: 搜索关键词
            limit: 数量限制
            
        Returns:
            words: 单词列表
        """
        if not self.db.conn:
            self.db.connect()
        
        query = '''
        SELECT * FROM vocabulary
        WHERE word LIKE ? OR definition LIKE ?
        ORDER BY frequency DESC
        LIMIT ?
        '''
        
        search_term = f"%{keyword}%"
        self.db.cursor.execute(query, (search_term, search_term, limit))
        return self.db.cursor.fetchall()
    
    def get_word_by_id(self, word_id):
        """根据ID获取单词信息
        
        Args:
            word_id: 单词ID
            
        Returns:
            word: 单词信息，如果不存在则返回None
        """
        if not self.db.conn:
            self.db.connect()
        
        self.db.cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
        return self.db.cursor.fetchone()
    
    def get_review_words(self, days=7, limit=50):
        """获取需要复习的单词
        
        根据记忆曲线算法，获取需要复习的单词
        
        Args:
            days: 时间范围（天）
            limit: 数量限制
            
        Returns:
            words: 单词列表
        """
        if not self.db.conn:
            self.db.connect()
        
        # 记忆曲线间隔 (1, 2, 4, 7, 15, 30天)
        review_intervals = [1, 2, 4, 7, 15, 30]
        
        # 计算日期范围
        today = datetime.now().date()
        date_range = []
        
        # 计算需要复习的日期
        for interval in review_intervals:
            if interval <= days:
                target_date = today - timedelta(days=interval)
                date_range.append(target_date.strftime('%Y-%m-%d'))
        
        if not date_range:
            return []
        
        # 构建查询条件
        date_condition = ','.join(['?'] * len(date_range))
        
        query = f'''
        SELECT v.*, lr.learn_date 
        FROM vocabulary v
        JOIN learning_record lr ON v.id = lr.word_id
        WHERE lr.learn_date IN ({date_condition})
        ORDER BY lr.learn_date ASC
        LIMIT ?
        '''
        
        # 执行查询
        params = date_range + [limit]
        self.db.cursor.execute(query, params)
        return self.db.cursor.fetchall()
    
    def record_review(self, word_id):
        """记录单词复习
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        return self.db.record_review(word_id)
    
    def get_learning_statistics(self):
        """获取学习统计信息
        
        Returns:
            stats: 统计信息字典
        """
        if not self.db.conn:
            self.db.connect()
        
        stats = {}
        
        # 获取总词汇量
        self.db.cursor.execute("SELECT COUNT(*) as count FROM vocabulary")
        result = self.db.cursor.fetchone()
        stats['total_words'] = result['count'] if result else 0
        
        # 获取重点词汇数量
        self.db.cursor.execute("SELECT COUNT(*) as count FROM favorite")
        result = self.db.cursor.fetchone()
        stats['favorite_words'] = result['count'] if result else 0
        
        # 获取已学习单词数量
        self.db.cursor.execute("SELECT COUNT(DISTINCT word_id) as count FROM learning_record")
        result = self.db.cursor.fetchone()
        stats['learned_words'] = result['count'] if result else 0
        
        # 获取今日学习单词数量
        today = datetime.now().strftime('%Y-%m-%d')
        self.db.cursor.execute(
            "SELECT COUNT(*) as count FROM learning_record WHERE learn_date = ?", 
            (today,)
        )
        result = self.db.cursor.fetchone()
        stats['today_words'] = result['count'] if result else 0
        
        # 获取连续学习天数
        self.db.cursor.execute("""
        SELECT COUNT(*) as days FROM (
            SELECT DISTINCT learn_date FROM learning_record
            ORDER BY learn_date DESC
        )
        """)
        result = self.db.cursor.fetchone()
        stats['streak_days'] = result['days'] if result else 0
        
        return stats
    
    def import_from_csv(self, csv_path, mode='update'):
        """从CSV文件导入词汇
        
        Args:
            csv_path: CSV文件路径
            mode: 导入模式，可选值:
                  - 'new_only': 仅导入新单词，忽略已存在的单词
                  - 'update': 更新现有单词，导入新单词（默认）
                  - 'overwrite': 覆盖所有单词，不检查是否存在
                  
        Returns:
            result: 包含导入结果的字典
        """
        # 先验证CSV文件格式
        validation_result = self.validate_csv_format(csv_path)
        if not validation_result['valid']:
            return validation_result
        
        return self.db.import_vocabulary_from_csv(csv_path, mode)
    
    def validate_csv_format(self, csv_path):
        """验证CSV文件格式
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            result: 包含验证结果的字典
                   {
                       'valid': 是否有效,
                       'message': 错误信息,
                       'new': 0,
                       'updated': 0,
                       'skipped': 0
                   }
        """
        result = {
            'valid': False,
            'message': '',
            'new': 0,
            'updated': 0,
            'skipped': 0
        }
        
        try:
            # 检查文件是否存在
            if not os.path.exists(csv_path):
                result['message'] = f"文件不存在: {csv_path}"
                return result
            
            # 检查文件扩展名
            if not csv_path.lower().endswith('.csv'):
                result['message'] = "文件必须是CSV格式"
                return result
            
            # 尝试读取CSV
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                result['message'] = f"无法读取CSV文件: {str(e)}"
                return result
            
            # 检查必要的列
            required_columns = ['word', 'definition']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                result['message'] = f"CSV文件缺少必要的列: {', '.join(missing_columns)}"
                return result
            
            # 检查数据有效性
            if df.empty:
                result['message'] = "CSV文件不包含任何数据"
                return result
            
            # 检查word列是否有空值
            if df['word'].isnull().any():
                result['message'] = "CSV文件中'word'列包含空值"
                return result
            
            # 检查definition列是否有空值
            if df['definition'].isnull().any():
                result['message'] = "CSV文件中'definition'列包含空值"
                return result
            
            # 文件格式有效
            result['valid'] = True
            
        except Exception as e:
            result['message'] = f"验证CSV文件格式时出错: {str(e)}"
        
        return result
    
    def add_word(self, word, definition, phonetic='', pos='', example='', frequency=0, difficulty=1):
        """添加单词
        
        Args:
            word: 单词
            definition: 释义
            phonetic: 音标
            pos: 词性
            example: 例句
            frequency: 使用频率
            difficulty: 难度等级
            
        Returns:
            success: 操作是否成功
        """
        try:
            if not self.db.conn:
                self.db.connect()
            
            # 检查单词是否已存在
            self.db.cursor.execute("SELECT id FROM vocabulary WHERE word = ?", (word,))
            result = self.db.cursor.fetchone()
            
            if result:
                # 更新现有单词
                self.db.cursor.execute('''
                UPDATE vocabulary 
                SET phonetic = ?, pos = ?, definition = ?, example = ?, 
                    frequency = ?, difficulty = ?
                WHERE word = ?
                ''', (phonetic, pos, definition, example, frequency, difficulty, word))
            else:
                # 插入新单词
                self.db.cursor.execute('''
                INSERT INTO vocabulary 
                (word, phonetic, pos, definition, example, frequency, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (word, phonetic, pos, definition, example, frequency, difficulty))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"添加单词时出错: {e}")
            return False 