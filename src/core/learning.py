import os
import json
from datetime import datetime, timedelta
from ..data.database import Database
from ..data.config import Config


class LearningManager:
    """学习计划管理类，提供学习计划和统计功能"""
    
    def __init__(self, db=None, config=None):
        """初始化学习管理器
        
        Args:
            db: 数据库连接，默认为None，会创建新的连接
            config: 配置管理器，默认为None，会创建新的配置管理器
        """
        self.db = db if db else Database()
        self.config = config if config else Config()
        
        # 确保数据库连接
        if not self.db.conn:
            self.db.connect()
    
    def get_daily_plan(self):
        """获取每日学习计划
        
        Returns:
            plan: 包含学习计划信息的字典
        """
        # 安全地获取study配置
        study_config = {}
        try:
            study_config = self.config.get('study')
            if not isinstance(study_config, dict):
                study_config = {}
        except Exception as e:
            print(f"获取学习计划配置时出错: {e}")
        
        # 使用默认值或从配置中获取的值
        return {
            'daily_words': study_config.get('daily_words', 10),
            'difficulty_range': study_config.get('difficulty_range', [1, 3]),
            'reminder_time': study_config.get('reminder_time', '08:00'),
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def update_daily_plan(self, daily_words=None, difficulty_min=None, difficulty_max=None, reminder_time=None):
        """更新每日学习计划
        
        Args:
            daily_words: 每日单词数量
            difficulty_min: 最小难度
            difficulty_max: 最大难度
            reminder_time: 提醒时间
            
        Returns:
            success: 操作是否成功
        """
        # 获取现有配置
        study_config = self.config.get('study', {})
        
        # 更新配置
        if daily_words is not None:
            study_config['daily_words'] = daily_words
            
        if difficulty_min is not None and difficulty_max is not None:
            study_config['difficulty_range'] = [difficulty_min, difficulty_max]
            
        if reminder_time is not None:
            study_config['reminder_time'] = reminder_time
        
        # 保存配置
        return self.config.set_section('study', study_config)
    
    def get_learning_status(self):
        """获取学习状态
        
        Returns:
            status: 学习状态字典
        """
        status = {}
        
        # 获取今日日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 获取今日学习的单词数量
        self.db.cursor.execute(
            "SELECT COUNT(*) as count FROM learning_record WHERE learn_date = ?", 
            (today,)
        )
        result = self.db.cursor.fetchone()
        
        if result:
            status['today_learned'] = result['count']
        else:
            status['today_learned'] = 0
        
        # 获取学习计划
        plan = self.get_daily_plan()
        status['daily_target'] = plan['daily_words']
        
        # 计算完成百分比
        if status['daily_target'] > 0:
            status['completion_percentage'] = min(100, int(status['today_learned'] * 100 / status['daily_target']))
        else:
            status['completion_percentage'] = 0
        
        # 检查是否完成今日学习
        status['is_completed'] = status['today_learned'] >= status['daily_target']
        
        return status
    
    def get_streak_days(self):
        """获取连续学习天数
        
        Returns:
            streak_days: 连续学习天数
        """
        if not self.db.conn:
            self.db.connect()
        
        # 获取所有学习日期，按日期降序排序
        self.db.cursor.execute(
            "SELECT DISTINCT learn_date FROM learning_record ORDER BY learn_date DESC"
        )
        dates = [row['learn_date'] for row in self.db.cursor.fetchall()]
        
        if not dates:
            return 0
        
        # 计算连续学习天数
        streak = 1
        today = datetime.now().date()
        
        for i in range(len(dates) - 1):
            current_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
            next_date = datetime.strptime(dates[i + 1], '%Y-%m-%d').date()
            
            # 检查日期是否连续
            if (current_date - next_date).days == 1:
                streak += 1
            else:
                break
        
        return streak
    
    def get_learning_statistics(self, days=30):
        """获取学习统计信息
        
        Args:
            days: 统计天数，默认为30天
            
        Returns:
            stats: 统计信息字典
        """
        if not self.db.conn:
            self.db.connect()
        
        stats = {}
        
        # 获取起始日期
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # 初始化日期数据
        date_range = []
        words_count = []
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_range.append(date_str)
            
            # 获取当日学习的单词数量
            self.db.cursor.execute(
                "SELECT COUNT(*) as count FROM learning_record WHERE learn_date = ?", 
                (date_str,)
            )
            result = self.db.cursor.fetchone()
            
            if result:
                words_count.append(result['count'])
            else:
                words_count.append(0)
            
            current_date += timedelta(days=1)
        
        # 设置统计数据
        stats['date_range'] = date_range
        stats['words_count'] = words_count
        
        # 计算总学习单词数
        stats['total_words'] = sum(words_count)
        
        # 计算平均每日学习单词数
        if len(words_count) > 0:
            stats['average_words'] = stats['total_words'] / len(words_count)
        else:
            stats['average_words'] = 0
        
        # 计算最大学习单词数
        stats['max_words'] = max(words_count) if words_count else 0
        
        # 计算有效学习天数（学习单词数大于0的天数）
        stats['effective_days'] = len([count for count in words_count if count > 0])
        
        # 计算连续学习天数
        stats['streak_days'] = self.get_streak_days()
        
        return stats
    
    def get_review_schedule(self):
        """获取复习计划
        
        根据记忆曲线生成复习计划
        
        Returns:
            schedule: 复习计划字典
        """
        if not self.db.conn:
            self.db.connect()
        
        # 记忆曲线间隔 (1, 2, 4, 7, 15, 30天)
        review_intervals = [1, 2, 4, 7, 15, 30]
        
        schedule = {}
        today = datetime.now().date()
        
        # 计算各个复习日期的单词列表
        for interval in review_intervals:
            target_date = today - timedelta(days=interval)
            date_str = target_date.strftime('%Y-%m-%d')
            
            # 获取该日期学习的单词
            self.db.cursor.execute('''
            SELECT v.id, v.word, v.definition 
            FROM vocabulary v
            JOIN learning_record lr ON v.id = lr.word_id
            WHERE lr.learn_date = ?
            ''', (date_str,))
            
            words = self.db.cursor.fetchall()
            
            if words:
                schedule[f'day_{interval}'] = {
                    'date': date_str,
                    'interval': interval,
                    'words': [dict(word) for word in words]
                }
        
        return schedule
    
    def record_learning(self, word_id):
        """记录学习单词
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        return self.db.record_learning(word_id)
    
    def record_review(self, word_id):
        """记录复习单词
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        return self.db.record_review(word_id) 