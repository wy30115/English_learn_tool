import os
import sqlite3
import pandas as pd
from datetime import datetime

class Database:
    """数据库管理类，提供数据库连接和操作功能"""
    
    def __init__(self, db_path=None):
        """初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认为None，会使用默认路径
        """
        if db_path is None:
            # 获取应用数据目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, 'data')
            
            # 确保目录存在
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            self.db_path = os.path.join(data_dir, 'vocabulary.db')
        else:
            self.db_path = db_path
            
        # 初始化数据库连接
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """连接到数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        self.cursor = self.conn.cursor()
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def execute(self, query, params=None):
        """执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数，默认为None
            
        Returns:
            cursor: 查询游标
        """
        if not self.conn:
            self.connect()
            
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
            
        return self.cursor
    
    def commit(self):
        """提交事务"""
        if self.conn:
            self.conn.commit()
    
    def create_tables(self):
        """创建数据库表结构"""
        # 确保数据库连接存在
        if not self.conn:
            self.connect()
        
        # 创建词汇表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            phonetic TEXT,
            pos TEXT,
            definition TEXT NOT NULL,
            example TEXT,
            frequency INTEGER DEFAULT 0,
            difficulty INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建重点词汇表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            review_count INTEGER DEFAULT 0,
            last_review TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES vocabulary (id)
        )
        ''')
        
        # 创建学习记录表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_record (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            learn_date DATE DEFAULT CURRENT_DATE,
            reviewed BOOLEAN DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES vocabulary (id)
        )
        ''')
        
        # 创建设置表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        # 提交事务
        self.conn.commit()
    
    def import_vocabulary_from_csv(self, csv_path, mode='update'):
        """从CSV文件导入词汇
        
        Args:
            csv_path: CSV文件路径
            mode: 导入模式，可选值:
                  - 'new_only': 仅导入新单词，忽略已存在的单词
                  - 'update': 更新现有单词，导入新单词（默认）
                  - 'overwrite': 覆盖所有单词，不检查是否存在
              
        Returns:
            result: 包含导入结果的字典
                   {
                       'new': 新增单词数量,
                       'updated': 更新单词数量,
                       'skipped': 跳过单词数量,
                       'updated_words': 已更新单词列表,
                       'skipped_words': 已跳过单词列表
                   }
        """
        # 初始化统计结果
        result = {
            'new': 0,
            'updated': 0,
            'skipped': 0,
            'updated_words': [],
            'skipped_words': []
        }
        
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_path)
            
            # 确保必要的列存在
            required_columns = ['word', 'definition']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"CSV文件缺少必要的列: {col}")
            
            # 确保数据库连接
            if not self.conn:
                self.connect()
            
            # 准备导入数据
            for _, row in df.iterrows():
                try:
                    # 获取值，对缺失值使用默认值
                    word = row['word']
                    definition = row['definition']
                    phonetic = row.get('phonetic', '')
                    pos = row.get('pos', '')
                    example = row.get('example', '')
                    
                    # 确保 frequency 和 difficulty 是有效的数值
                    try:
                        frequency = int(row.get('frequency', 0))
                    except (ValueError, TypeError):
                        frequency = 0
                        
                    try:
                        difficulty = int(row.get('difficulty', 1))
                    except (ValueError, TypeError):
                        difficulty = 1
                    
                    # 检查单词是否已存在
                    self.cursor.execute("SELECT id FROM vocabulary WHERE word = ?", (word,))
                    existing = self.cursor.fetchone()
                    
                    if existing and mode == 'new_only':
                        # 如果单词已存在且模式为仅导入新单词，则跳过
                        result['skipped'] += 1
                        result['skipped_words'].append(word)
                        continue
                    
                    if existing and mode == 'update':
                        # 更新现有单词
                        self.cursor.execute('''
                        UPDATE vocabulary 
                        SET phonetic = ?, pos = ?, definition = ?, example = ?, 
                            frequency = ?, difficulty = ?
                        WHERE word = ?
                        ''', (phonetic, pos, definition, example, frequency, difficulty, word))
                        result['updated'] += 1
                        result['updated_words'].append(word)
                    else:
                        # 插入新单词或覆盖现有单词
                        if existing and mode == 'overwrite':
                            # 如果是覆盖模式且单词存在，先删除
                            self.cursor.execute("DELETE FROM vocabulary WHERE word = ?", (word,))
                            # 更新统计（虽然技术上是先删除后新增，但从用户角度看是更新）
                            result['updated'] += 1
                            result['updated_words'].append(word)
                        else:
                            # 新增单词
                            result['new'] += 1
                        
                        # 插入单词
                        self.cursor.execute('''
                        INSERT INTO vocabulary 
                        (word, phonetic, pos, definition, example, frequency, difficulty)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (word, phonetic, pos, definition, example, frequency, difficulty))
                except Exception as row_error:
                    print(f"处理行时出错: {row_error}, 行数据: {row}")
                    # 记录跳过的单词但继续处理其他行
                    if 'word' in row:
                        result['skipped'] += 1
                        result['skipped_words'].append(str(row.get('word', 'Unknown')))
            
            # 提交事务
            self.conn.commit()
            return result
        
        except Exception as e:
            print(f"导入词汇时出错: {e}")
            # 回滚事务
            if self.conn:
                self.conn.rollback()
            
            # 添加错误信息到结果
            result['error'] = str(e)
            return result
    
    def get_random_words(self, count=10, difficulty_min=1, difficulty_max=5, exclude_learned=True):
        """获取随机单词
        
        Args:
            count: 要获取的单词数量
            difficulty_min: 最小难度
            difficulty_max: 最大难度
            exclude_learned: 是否排除今天已学习的单词
            
        Returns:
            words: 单词列表
        """
        query = '''
        SELECT * FROM vocabulary 
        WHERE difficulty BETWEEN ? AND ?
        '''
        
        params = [difficulty_min, difficulty_max]
        
        if exclude_learned:
            # 排除今天已学习的单词
            today = datetime.now().strftime('%Y-%m-%d')
            query += f''' 
            AND id NOT IN (
                SELECT word_id FROM learning_record 
                WHERE learn_date = '{today}'
            )'''
        
        # 随机排序并限制数量
        query += ' ORDER BY RANDOM() LIMIT ?'
        params.append(count)
        
        # 执行查询
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def mark_as_favorite(self, word_id):
        """将单词标记为重点词汇
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        try:
            # 检查是否已经是重点词汇
            self.cursor.execute("SELECT id FROM favorite WHERE word_id = ?", (word_id,))
            result = self.cursor.fetchone()
            
            if result:
                # 已经是重点词汇，返回True
                return True
            
            # 添加到重点词汇
            now = datetime.now()
            self.cursor.execute('''
            INSERT INTO favorite (word_id, marked_at)
            VALUES (?, ?)
            ''', (word_id, now))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"标记重点词汇时出错: {e}")
            return False
    
    def unmark_favorite(self, word_id):
        """取消单词的重点标记
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        try:
            self.cursor.execute("DELETE FROM favorite WHERE word_id = ?", (word_id,))
            self.conn.commit()
            return True
        
        except Exception as e:
            print(f"取消重点词汇标记时出错: {e}")
            return False
    
    def get_favorite_words(self, limit=100, offset=0):
        """获取重点词汇列表
        
        Args:
            limit: 限制返回数量
            offset: 结果偏移量
            
        Returns:
            words: 单词列表
        """
        query = '''
        SELECT v.*, f.marked_at, f.review_count, f.last_review 
        FROM vocabulary v
        JOIN favorite f ON v.id = f.word_id
        ORDER BY f.marked_at DESC
        LIMIT ? OFFSET ?
        '''
        
        self.cursor.execute(query, (limit, offset))
        return self.cursor.fetchall()
    
    def record_learning(self, word_id):
        """记录学习单词
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 检查是否已经有今天的学习记录
            self.cursor.execute('''
            SELECT id FROM learning_record 
            WHERE word_id = ? AND learn_date = ?
            ''', (word_id, today))
            
            result = self.cursor.fetchone()
            
            if not result:
                # 没有今天的学习记录，添加记录
                self.cursor.execute('''
                INSERT INTO learning_record (word_id, learn_date)
                VALUES (?, ?)
                ''', (word_id, today))
                
                self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"记录学习时出错: {e}")
            return False
    
    def record_review(self, word_id):
        """记录复习单词
        
        Args:
            word_id: 单词ID
            
        Returns:
            success: 操作是否成功
        """
        try:
            now = datetime.now()
            
            # 检查是否是重点词汇
            self.cursor.execute("SELECT id FROM favorite WHERE word_id = ?", (word_id,))
            favorite = self.cursor.fetchone()
            
            if favorite:
                # 更新重点词汇的复习信息
                self.cursor.execute('''
                UPDATE favorite 
                SET review_count = review_count + 1, last_review = ?
                WHERE word_id = ?
                ''', (now, word_id))
            
            # 标记学习记录为已复习
            today = now.strftime('%Y-%m-%d')
            self.cursor.execute('''
            UPDATE learning_record 
            SET reviewed = 1
            WHERE word_id = ? AND learn_date = ?
            ''', (word_id, today))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"记录复习时出错: {e}")
            return False
    
    def get_settings(self, key):
        """获取设置值
        
        Args:
            key: 设置键名
            
        Returns:
            value: 设置值，如果不存在则返回None
        """
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        
        if result:
            return result['value']
        return None
    
    def set_settings(self, key, value):
        """设置配置项
        
        Args:
            key: 设置键名
            value: 设置值
            
        Returns:
            success: 操作是否成功
        """
        try:
            # 检查设置是否已存在
            self.cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            
            if result:
                # 更新设置
                self.cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
            else:
                # 插入新设置
                self.cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"设置配置项时出错: {e}")
            return False 