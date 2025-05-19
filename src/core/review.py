import random
from datetime import datetime, timedelta
from ..data.database import Database
from ..data.config import Config


class ReviewManager:
    """复习管理类，提供复习功能"""
    
    def __init__(self, db=None, config=None):
        """初始化复习管理器
        
        Args:
            db: 数据库连接，默认为None，会创建新的连接
            config: 配置管理器，默认为None，会创建新的配置管理器
        """
        self.db = db if db else Database()
        self.config = config if config else Config()
        
        # 确保数据库连接
        if not self.db.conn:
            self.db.connect()
        
        # 记忆曲线间隔 (1, 2, 4, 7, 15, 30天)
        self.review_intervals = [1, 2, 4, 7, 15, 30]
    
    def get_review_words_by_interval(self, interval, limit=50):
        """根据间隔获取需要复习的单词
        
        Args:
            interval: 复习间隔（天数）
            limit: 数量限制
            
        Returns:
            words: 单词列表
        """
        if not self.db.conn:
            self.db.connect()
        
        today = datetime.now().date()
        target_date = today - timedelta(days=interval)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # 获取该日期学习的单词
        query = '''
        SELECT v.*, lr.learn_date 
        FROM vocabulary v
        JOIN learning_record lr ON v.id = lr.word_id
        WHERE lr.learn_date = ?
        LIMIT ?
        '''
        
        self.db.cursor.execute(query, (date_str, limit))
        return self.db.cursor.fetchall()
    
    def get_review_words(self, days=7, limit=50, shuffle=True):
        """获取需要复习的单词
        
        根据记忆曲线算法，获取需要复习的单词
        
        Args:
            days: 时间范围（天）
            limit: 数量限制
            shuffle: 是否随机排序
            
        Returns:
            words: 单词列表
        """
        if not self.db.conn:
            self.db.connect()
        
        # 计算日期范围
        today = datetime.now().date()
        date_range = []
        
        # 计算需要复习的日期
        for interval in self.review_intervals:
            if interval <= days:
                target_date = today - timedelta(days=interval)
                date_range.append(target_date.strftime('%Y-%m-%d'))
        
        if not date_range:
            return []
        
        # 构建查询条件
        date_condition = ','.join(['?'] * len(date_range))
        
        # 查询需要复习的单词
        query = f'''
        SELECT v.*, lr.learn_date 
        FROM vocabulary v
        JOIN learning_record lr ON v.id = lr.word_id
        WHERE lr.learn_date IN ({date_condition})
        '''
        
        if shuffle:
            query += ' ORDER BY RANDOM()'
        else:
            query += ' ORDER BY lr.learn_date ASC'
            
        query += ' LIMIT ?'
        
        # 执行查询
        params = date_range + [limit]
        self.db.cursor.execute(query, params)
        return self.db.cursor.fetchall()
    
    def get_favorite_words_for_review(self, limit=50, shuffle=True):
        """获取重点词汇进行复习
        
        Args:
            limit: 数量限制
            shuffle: 是否随机排序
            
        Returns:
            words: 单词列表
        """
        if not self.db.conn:
            self.db.connect()
        
        query = '''
        SELECT v.*, f.marked_at, f.review_count, f.last_review 
        FROM vocabulary v
        JOIN favorite f ON v.id = f.word_id
        '''
        
        if shuffle:
            query += ' ORDER BY RANDOM()'
        else:
            # 优先复习复习次数少的单词
            query += ' ORDER BY f.review_count ASC, f.marked_at DESC'
            
        query += ' LIMIT ?'
        
        self.db.cursor.execute(query, (limit,))
        return self.db.cursor.fetchall()
    
    def get_daily_review_plan(self):
        """获取每日复习计划
        
        Returns:
            plan: 复习计划字典
        """
        plan = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'intervals': {},
            'favorites': []
        }
        
        # 获取各个间隔的复习单词
        for interval in self.review_intervals:
            words = self.get_review_words_by_interval(interval, 20)
            if words:
                plan['intervals'][interval] = [dict(word) for word in words]
        
        # 获取重点词汇
        favorites = self.get_favorite_words_for_review(20)
        if favorites:
            plan['favorites'] = [dict(word) for word in favorites]
        
        return plan
    
    def record_review(self, word_id):
        """记录单词复习
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        return self.db.record_review(word_id)
    
    def get_review_statistics(self):
        """获取复习统计信息
        
        Returns:
            stats: 统计信息字典
        """
        if not self.db.conn:
            self.db.connect()
        
        stats = {}
        
        # 获取今日复习单词数量
        today = datetime.now().strftime('%Y-%m-%d')
        self.db.cursor.execute(
            "SELECT COUNT(*) as count FROM learning_record WHERE learn_date = ? AND reviewed = 1", 
            (today,)
        )
        result = self.db.cursor.fetchone()
        stats['today_reviewed'] = result['count'] if result else 0
        
        # 获取总复习单词数量
        self.db.cursor.execute(
            "SELECT COUNT(*) as count FROM learning_record WHERE reviewed = 1"
        )
        result = self.db.cursor.fetchone()
        stats['total_reviewed'] = result['count'] if result else 0
        
        # 获取重点词汇数量
        self.db.cursor.execute("SELECT COUNT(*) as count FROM favorite")
        result = self.db.cursor.fetchone()
        stats['total_favorites'] = result['count'] if result else 0
        
        # 获取平均复习次数
        self.db.cursor.execute(
            "SELECT AVG(review_count) as avg FROM favorite"
        )
        result = self.db.cursor.fetchone()
        stats['avg_review_count'] = round(result['avg'], 1) if result and result['avg'] else 0
        
        # 获取待复习单词数量
        need_review_count = 0
        for interval in self.review_intervals:
            words = self.get_review_words_by_interval(interval)
            need_review_count += len(words)
            
        stats['need_review_count'] = need_review_count
        
        return stats
    
    def get_review_progress(self, word_id):
        """获取单词的复习进度
        
        Args:
            word_id: 单词ID
            
        Returns:
            progress: 复习进度字典
        """
        if not self.db.conn:
            self.db.connect()
        
        progress = {
            'word_id': word_id,
            'is_favorite': False,
            'review_count': 0,
            'last_review': None,
            'review_dates': []
        }
        
        # 检查是否为重点词汇
        self.db.cursor.execute(
            "SELECT id, review_count, last_review FROM favorite WHERE word_id = ?", 
            (word_id,)
        )
        result = self.db.cursor.fetchone()
        
        if result:
            progress['is_favorite'] = True
            progress['review_count'] = result['review_count']
            progress['last_review'] = result['last_review']
        
        # 获取学习日期
        self.db.cursor.execute(
            "SELECT learn_date, reviewed FROM learning_record WHERE word_id = ? ORDER BY learn_date",
            (word_id,)
        )
        records = self.db.cursor.fetchall()
        
        for record in records:
            progress['review_dates'].append({
                'date': record['learn_date'],
                'reviewed': bool(record['reviewed'])
            })
        
        return progress
    
    def generate_review_quiz(self, count=10, include_favorites=True):
        """生成复习测验
        
        Args:
            count: 测验题目数量
            include_favorites: 是否包含重点词汇
            
        Returns:
            quiz: 测验题目列表
        """
        # 获取需要复习的单词
        review_words = self.get_review_words(days=30, limit=count)
        
        # 如果数量不足且包含重点词汇，则添加重点词汇
        if len(review_words) < count and include_favorites:
            remaining = count - len(review_words)
            favorite_words = self.get_favorite_words_for_review(limit=remaining)
            review_words.extend(favorite_words)
        
        # 如果仍然不足，随机获取词汇库中的单词
        if len(review_words) < count:
            remaining = count - len(review_words)
            
            # 获取已有单词的ID
            existing_ids = [word['id'] for word in review_words]
            
            if not self.db.conn:
                self.db.connect()
                
            # 随机获取其他单词
            id_condition = ','.join(['?'] * len(existing_ids)) if existing_ids else '0'
            query = f'''
            SELECT * FROM vocabulary 
            WHERE id NOT IN ({id_condition})
            ORDER BY RANDOM()
            LIMIT ?
            '''
            
            params = existing_ids + [remaining]
            self.db.cursor.execute(query, params)
            random_words = self.db.cursor.fetchall()
            
            review_words.extend(random_words)
        
        # 随机打乱顺序
        random.shuffle(review_words)
        
        # 生成测验题目
        quiz = []
        for word in review_words:
            quiz_item = {
                'word_id': word['id'],
                'word': word['word'],
                'phonetic': word['phonetic'],
                'pos': word['pos'],
                'definition': word['definition'],
                'example': word['example']
            }
            quiz.append(quiz_item)
        
        return quiz 