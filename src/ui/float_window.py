import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QSizePolicy, QDesktopWidget,
                            QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QCursor

from ..core.vocabulary import VocabularyManager
from ..core.learning import LearningManager
from ..utils.audio import AudioManager


class FloatWindow(QWidget):
    """悬浮窗窗口"""
    
    # 自定义信号
    closed = pyqtSignal()  # 窗口关闭信号
    
    def __init__(self, vocab_manager, learning_manager, words=None):
        """初始化悬浮窗
        
        Args:
            vocab_manager: 词汇管理器
            learning_manager: 学习管理器
            words: 单词列表，默认为None
        """
        super().__init__()
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |  # 窗口置顶
            Qt.FramelessWindowHint |   # 无边框
            Qt.Tool                    # 工具窗口，不在任务栏显示
        )
        
        # 设置窗口透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化数据
        self.vocab_manager = vocab_manager
        self.learning_manager = learning_manager
        self.words = words or []
        self.current_index = 0
        
        # 创建音频管理器
        self.audio_manager = AudioManager()
        
        # 拖动相关变量
        self.draggable = True
        self.dragging = False
        self.drag_position = None
        
        # 窗口固定状态
        self.is_fixed = False
        
        # 初始化UI
        self.init_ui()
        
        # 更新单词显示
        if self.words:
            self.update_word_display()
        else:
            self.word_label.setText("词汇库为空")
            self.phonetic_label.setText("")
            self.pos_label.setText("")
            self.definition_label.setText("请先在\"应用设置\"->\"数据管理\"中导入词汇")
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置初始大小和位置
        self.resize(370, 270)
        self.center_on_screen()
        
        # 添加阴影效果
        self.apply_shadow()
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 标题栏
        self.create_title_bar(main_layout)
        
        # 内容区域
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("""
            QFrame#contentFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 内容区域阴影效果
        content_shadow = QGraphicsDropShadowEffect()
        content_shadow.setBlurRadius(20)
        content_shadow.setColor(QColor(0, 0, 0, 50))
        content_shadow.setOffset(0, 2)
        content_frame.setGraphicsEffect(content_shadow)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # 单词显示
        self.word_label = QLabel()
        font = QFont("Arial", 22)
        font.setBold(True)
        self.word_label.setFont(font)
        self.word_label.setAlignment(Qt.AlignCenter)
        self.word_label.setWordWrap(True)
        self.word_label.setStyleSheet("color: #2c3e50;")
        content_layout.addWidget(self.word_label)
        
        # 音标显示
        self.phonetic_label = QLabel()
        self.phonetic_label.setFont(QFont("Arial", 14))
        self.phonetic_label.setAlignment(Qt.AlignCenter)
        self.phonetic_label.setStyleSheet("color: #3498db; margin-bottom: 5px;")
        content_layout.addWidget(self.phonetic_label)
        
        # 词性显示
        self.pos_label = QLabel()
        self.pos_label.setFont(QFont("微软雅黑", 12))
        self.pos_label.setAlignment(Qt.AlignCenter)
        self.pos_label.setStyleSheet("color: #7f8c8d; margin-bottom: 5px;")
        content_layout.addWidget(self.pos_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #ecf0f1; margin: 5px 0;")
        content_layout.addWidget(separator)
        
        # 释义显示
        self.definition_label = QLabel()
        self.definition_label.setFont(QFont("微软雅黑", 13))
        self.definition_label.setAlignment(Qt.AlignCenter)
        self.definition_label.setWordWrap(True)
        self.definition_label.setStyleSheet("color: #34495e; margin: 5px 0;")
        content_layout.addWidget(self.definition_label)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # 收藏按钮
        self.favorite_button = QPushButton("收藏")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        self.favorite_button.setFont(font)
        self.favorite_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.favorite_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #d35400);
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #d35400, stop:1 #e67e22);
                border: 1px solid white;
            }
            QPushButton:pressed {
                padding-top: 9px;
                padding-left: 16px;
            }
        """)
        self.favorite_button.clicked.connect(self.toggle_favorite)
        buttons_layout.addWidget(self.favorite_button)
        
        # 发音按钮
        self.pronounce_button = QPushButton("发音")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        self.pronounce_button.setFont(font)
        self.pronounce_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.pronounce_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2980b9, stop:1 #3498db);
                border: 1px solid white;
            }
            QPushButton:pressed {
                padding-top: 9px;
                padding-left: 16px;
            }
        """)
        self.pronounce_button.clicked.connect(self.pronounce_word)
        buttons_layout.addWidget(self.pronounce_button)
        
        # 下一个按钮
        self.next_button = QPushButton("下一个")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        self.next_button.setFont(font)
        self.next_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #2ecc71);
                border: 1px solid white;
            }
            QPushButton:pressed {
                padding-top: 9px;
                padding-left: 16px;
            }
        """)
        self.next_button.clicked.connect(self.next_word)
        buttons_layout.addWidget(self.next_button)
        
        content_layout.addLayout(buttons_layout)
        
        # 计数器显示
        self.counter_label = QLabel()
        self.counter_label.setFont(QFont("Arial", 10))
        self.counter_label.setAlignment(Qt.AlignCenter)
        self.counter_label.setStyleSheet("color: #7f8c8d; margin-top: 5px;")
        content_layout.addWidget(self.counter_label)
        
        main_layout.addWidget(content_frame)
    
    def create_title_bar(self, parent_layout):
        """创建标题栏
        
        Args:
            parent_layout: 父布局
        """
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_frame.setStyleSheet("""
            QFrame#titleFrame {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9);
                border-radius: 12px;
                border: none;
            }
            QLabel { color: white; }
        """)
        
        # 标题栏阴影效果
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(15)
        title_shadow.setColor(QColor(0, 0, 0, 60))
        title_shadow.setOffset(0, 2)
        title_frame.setGraphicsEffect(title_shadow)
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 6, 10, 6)
        
        # 标题文本
        title_label = QLabel("每日单词")
        font = QFont("微软雅黑", 11)
        font.setBold(True)
        title_label.setFont(font)
        title_layout.addWidget(title_label)
        
        # 空白占位符
        title_layout.addStretch(1)
        
        # 固定按钮
        self.pin_button = QPushButton("📌")
        self.pin_button.setFont(QFont("Arial", 12))
        self.pin_button.setFixedSize(24, 24)
        self.pin_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.pin_button.setToolTip("固定/取消固定窗口")
        self.pin_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)
        self.pin_button.clicked.connect(self.toggle_fixed)
        title_layout.addWidget(self.pin_button)
        
        # 关闭按钮
        close_button = QPushButton("✖")
        close_button.setFont(QFont("Arial", 12))
        close_button.setFixedSize(24, 24)
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button.setToolTip("关闭窗口")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 12px;
            }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        parent_layout.addWidget(title_frame)
    
    def apply_shadow(self):
        """为整个窗口应用阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def center_on_screen(self):
        """将窗口居中显示"""
        screen_geometry = QDesktopWidget().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def update_word_display(self):
        """更新单词显示"""
        if not self.words or self.current_index >= len(self.words):
            return
        
        # 获取当前单词
        word = self.words[self.current_index]
        
        # 更新UI显示
        self.word_label.setText(word['word'])
        self.phonetic_label.setText(word['phonetic'] if word['phonetic'] else "")
        self.pos_label.setText(word['pos'] if word['pos'] else "")
        self.definition_label.setText(word['definition'])
        
        # 更新计数器
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.words)}")
        
        # 更新收藏按钮状态
        if self.vocab_manager.is_favorite(word['id']):
            self.favorite_button.setText("取消收藏")
            self.favorite_button.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
        else:
            self.favorite_button.setText("收藏")
            self.favorite_button.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
        
        # 记录学习
        self.learning_manager.record_learning(word['id'])
    
    def toggle_favorite(self):
        """切换收藏状态"""
        if not self.words or self.current_index >= len(self.words):
            return
        
        word = self.words[self.current_index]
        word_id = word['id']
        
        if self.vocab_manager.is_favorite(word_id):
            # 取消收藏
            self.vocab_manager.unmark_favorite(word_id)
            self.favorite_button.setText("收藏")
            self.favorite_button.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
        else:
            # 添加收藏
            self.vocab_manager.mark_favorite(word_id)
            self.favorite_button.setText("取消收藏")
            self.favorite_button.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
    
    def pronounce_word(self):
        """发音当前单词"""
        if not self.words or self.current_index >= len(self.words):
            return
        
        # 获取当前单词
        word = self.words[self.current_index]['word']
        
        # 使用音频管理器播放单词发音
        self.audio_manager.speak_text(word, lang='en')
    
    def next_word(self):
        """显示下一个单词"""
        if not self.words:
            return
        
        self.current_index = (self.current_index + 1) % len(self.words)
        self.update_word_display()
    
    def toggle_fixed(self):
        """切换窗口固定状态"""
        self.is_fixed = not self.is_fixed
        self.draggable = not self.is_fixed
        
        if self.is_fixed:
            self.pin_button.setText("📍")
            self.pin_button.setToolTip("解除固定")
        else:
            self.pin_button.setText("📌")
            self.pin_button.setToolTip("固定窗口位置")
    
    def mousePressEvent(self, event):
        """鼠标按下事件
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.LeftButton and self.draggable:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件
        
        Args:
            event: 鼠标事件
        """
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        Args:
            event: 关闭事件
        """
        # 发送窗口关闭信号
        self.closed.emit()
        event.accept() 