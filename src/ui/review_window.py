import os
import sys
import random
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QStackedWidget, QTabWidget,
                            QGridLayout, QListWidget, QListWidgetItem,
                            QMessageBox, QRadioButton, QButtonGroup,
                            QScrollArea, QGroupBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

from ..core.vocabulary import VocabularyManager
from ..core.review import ReviewManager


class ReviewWindow(QWidget):
    """复习窗口"""
    
    # 自定义信号
    review_completed = pyqtSignal()  # 复习完成信号
    
    def __init__(self, vocab_manager, learning_manager, review_manager, parent=None):
        """初始化复习窗口
        
        Args:
            vocab_manager: 词汇管理器
            learning_manager: 学习管理器
            review_manager: 复习管理器
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 保存管理器实例
        self.vocab_manager = vocab_manager
        self.learning_manager = learning_manager
        self.review_manager = review_manager
        
        # 初始化复习数据
        self.review_words = []
        self.current_index = 0
        self.correct_count = 0
        self.review_mode = 'flashcard'
        self.correct_option_index = 0
        
        # 设置窗口属性
        self.setWindowTitle("单词复习")
        self.setMinimumSize(800, 600)
        
        # 初始化界面
        self.init_ui()
        
        # 连接信号和槽
        self.connect_signals()
        
        # 加载复习单词
        self.load_review_words()
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("单词复习")
        font = QFont("微软雅黑", 16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 复习模式选择
        self.create_mode_selector(main_layout)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        
        # 创建各个模式的界面
        self.create_flashcard_mode()
        self.create_quiz_mode()
        self.create_typing_mode()
        
        main_layout.addWidget(self.content_stack, 1)
        
    def create_mode_selector(self, parent_layout):
        """创建模式选择器
        
        Args:
            parent_layout: 父布局
        """
        mode_frame = QFrame()
        mode_frame.setObjectName("modeFrame")
        mode_frame.setStyleSheet("""
            QFrame#modeFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        mode_layout.setSpacing(10)
        
        # 模式按钮组
        self.mode_group = QButtonGroup(self)
        
        # 闪卡模式
        self.flashcard_radio = QRadioButton("闪卡模式")
        self.flashcard_radio.setFont(QFont("微软雅黑", 10))
        self.flashcard_radio.setChecked(True)
        self.flashcard_radio.clicked.connect(lambda: self.change_mode('flashcard'))
        self.mode_group.addButton(self.flashcard_radio)
        mode_layout.addWidget(self.flashcard_radio)
        
        # 竖线分隔符
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("background-color: #e0e0e0;")
        mode_layout.addWidget(separator1)
        
        # 测验模式
        self.quiz_radio = QRadioButton("测验模式")
        self.quiz_radio.setFont(QFont("微软雅黑", 10))
        self.quiz_radio.clicked.connect(lambda: self.change_mode('quiz'))
        self.mode_group.addButton(self.quiz_radio)
        mode_layout.addWidget(self.quiz_radio)
        
        # 竖线分隔符
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #e0e0e0;")
        mode_layout.addWidget(separator2)
        
        # 拼写模式
        self.typing_radio = QRadioButton("拼写模式")
        self.typing_radio.setFont(QFont("微软雅黑", 10))
        self.typing_radio.clicked.connect(lambda: self.change_mode('typing'))
        self.mode_group.addButton(self.typing_radio)
        mode_layout.addWidget(self.typing_radio)
        
        parent_layout.addWidget(mode_frame)
    
    def create_flashcard_mode(self):
        """创建闪卡模式界面"""
        flashcard_widget = QWidget()
        flashcard_layout = QVBoxLayout(flashcard_widget)
        flashcard_layout.setContentsMargins(0, 0, 0, 0)
        flashcard_layout.setSpacing(15)
        
        # 卡片区域
        card_frame = QFrame()
        card_frame.setObjectName("cardFrame")
        card_frame.setStyleSheet("""
            QFrame#cardFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_frame.setMinimumHeight(300)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)
        
        # 单词显示
        self.fc_word_label = QLabel()
        font = QFont("Arial", 24)
        font.setBold(True)
        self.fc_word_label.setFont(font)
        self.fc_word_label.setAlignment(Qt.AlignCenter)
        self.fc_word_label.setWordWrap(True)
        card_layout.addWidget(self.fc_word_label)
        
        # 音标显示
        self.fc_phonetic_label = QLabel()
        self.fc_phonetic_label.setFont(QFont("Arial", 14))
        self.fc_phonetic_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.fc_phonetic_label)
        
        # 词性显示
        self.fc_pos_label = QLabel()
        self.fc_pos_label.setFont(QFont("微软雅黑", 12))
        self.fc_pos_label.setAlignment(Qt.AlignCenter)
        self.fc_pos_label.setStyleSheet("color: #7f8c8d;")
        card_layout.addWidget(self.fc_pos_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        card_layout.addWidget(separator)
        
        # 卡片翻转部分
        self.fc_content_stack = QStackedWidget()
        
        # 正面（提示点击翻转）
        front_widget = QWidget()
        front_layout = QVBoxLayout(front_widget)
        front_layout.setContentsMargins(0, 0, 0, 0)
        
        front_label = QLabel("点击查看释义")
        front_label.setFont(QFont("微软雅黑", 14))
        front_label.setAlignment(Qt.AlignCenter)
        front_label.setStyleSheet("color: #3498db;")
        front_layout.addWidget(front_label)
        
        self.fc_content_stack.addWidget(front_widget)
        
        # 背面（释义和例句）
        back_widget = QWidget()
        back_layout = QVBoxLayout(back_widget)
        back_layout.setContentsMargins(0, 0, 0, 0)
        back_layout.setSpacing(15)
        
        # 释义
        self.fc_definition_label = QLabel()
        self.fc_definition_label.setFont(QFont("微软雅黑", 14))
        self.fc_definition_label.setAlignment(Qt.AlignCenter)
        self.fc_definition_label.setWordWrap(True)
        back_layout.addWidget(self.fc_definition_label)
        
        # 例句
        self.fc_example_label = QLabel()
        font = QFont("微软雅黑", 12)
        font.setItalic(True)
        self.fc_example_label.setFont(font)
        self.fc_example_label.setAlignment(Qt.AlignCenter)
        self.fc_example_label.setWordWrap(True)
        self.fc_example_label.setStyleSheet("color: #7f8c8d;")
        back_layout.addWidget(self.fc_example_label)
        
        self.fc_content_stack.addWidget(back_widget)
        
        card_layout.addWidget(self.fc_content_stack)
        
        # 点击卡片翻转
        card_frame.mousePressEvent = self.flip_flashcard
        
        flashcard_layout.addWidget(card_frame)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # 收藏按钮
        self.fc_favorite_button = QPushButton("收藏")
        self.fc_favorite_button.setFont(QFont("微软雅黑", 10))
        self.fc_favorite_button.setMinimumSize(100, 35)
        self.fc_favorite_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.fc_favorite_button.clicked.connect(self.toggle_favorite)
        buttons_layout.addWidget(self.fc_favorite_button)
        
        # 发音按钮
        self.fc_pronounce_button = QPushButton("发音")
        self.fc_pronounce_button.setFont(QFont("微软雅黑", 10))
        self.fc_pronounce_button.setMinimumSize(100, 35)
        self.fc_pronounce_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.fc_pronounce_button.clicked.connect(self.pronounce_word)
        buttons_layout.addWidget(self.fc_pronounce_button)
        
        # 记住按钮
        self.fc_remember_button = QPushButton("记住了")
        self.fc_remember_button.setFont(QFont("微软雅黑", 10))
        self.fc_remember_button.setMinimumSize(100, 35)
        self.fc_remember_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.fc_remember_button.clicked.connect(lambda: self.next_word(True))
        buttons_layout.addWidget(self.fc_remember_button)
        
        # 忘记按钮
        self.fc_forget_button = QPushButton("忘记了")
        self.fc_forget_button.setFont(QFont("微软雅黑", 10))
        self.fc_forget_button.setMinimumSize(100, 35)
        self.fc_forget_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.fc_forget_button.clicked.connect(lambda: self.next_word(False))
        buttons_layout.addWidget(self.fc_forget_button)
        
        flashcard_layout.addLayout(buttons_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        
        self.fc_progress_label = QLabel("进度:")
        progress_layout.addWidget(self.fc_progress_label)
        
        self.fc_progress_bar = QProgressBar()
        self.fc_progress_bar.setMinimum(0)
        self.fc_progress_bar.setMaximum(100)
        self.fc_progress_bar.setValue(0)
        self.fc_progress_bar.setTextVisible(True)
        self.fc_progress_bar.setFormat("%v% (%p/100)")
        progress_layout.addWidget(self.fc_progress_bar, 1)
        
        self.fc_counter_label = QLabel()
        progress_layout.addWidget(self.fc_counter_label)
        
        flashcard_layout.addLayout(progress_layout)
        
        self.content_stack.addWidget(flashcard_widget)
        
    def connect_signals(self):
        """连接信号和槽函数"""
        # 模式选择信号
        self.flashcard_radio.toggled.connect(lambda checked: checked and self.change_mode('flashcard'))
        self.quiz_radio.toggled.connect(lambda checked: checked and self.change_mode('quiz'))
        self.typing_radio.toggled.connect(lambda checked: checked and self.change_mode('typing'))
        
        # 闪卡模式信号
        self.fc_content_stack.mousePressEvent = self.flip_flashcard
        self.fc_favorite_button.clicked.connect(self.toggle_favorite)
        self.fc_pronounce_button.clicked.connect(self.pronounce_word)
        self.fc_remember_button.clicked.connect(lambda: self.next_word(True))
        self.fc_forget_button.clicked.connect(lambda: self.next_word(False))
        
        # 测验模式信号
        self.qz_favorite_button.clicked.connect(self.toggle_favorite)
        self.qz_pronounce_button.clicked.connect(self.pronounce_word)
        self.qz_confirm_button.clicked.connect(self.check_quiz_answer)
        
        # 拼写模式信号
        self.tp_favorite_button.clicked.connect(self.toggle_favorite)
        self.tp_hint_button.clicked.connect(self.give_typing_hint)
        self.tp_skip_button.clicked.connect(lambda: self.next_word(False))
        self.tp_confirm_button.clicked.connect(self.check_typing_answer)
        self.tp_input.returnPressed.connect(self.check_typing_answer)
    
    def flip_flashcard(self, event):
        """翻转闪卡"""
        # 获取当前索引
        current_index = self.fc_content_stack.currentIndex()
        
        # 切换到另一面
        next_index = 1 if current_index == 0 else 0
        self.fc_content_stack.setCurrentIndex(next_index)
    
    def create_quiz_mode(self):
        """创建测验模式界面"""
        quiz_widget = QWidget()
        quiz_layout = QVBoxLayout(quiz_widget)
        quiz_layout.setContentsMargins(0, 0, 0, 0)
        quiz_layout.setSpacing(15)
        
        # 题目区域
        question_frame = QFrame()
        question_frame.setObjectName("questionFrame")
        question_frame.setStyleSheet("""
            QFrame#questionFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        question_layout = QVBoxLayout(question_frame)
        question_layout.setContentsMargins(20, 20, 20, 20)
        question_layout.setSpacing(10)
        
        # 单词显示
        self.qz_word_label = QLabel()
        font = QFont("Arial", 20)
        font.setBold(True)
        self.qz_word_label.setFont(font)
        self.qz_word_label.setAlignment(Qt.AlignCenter)
        self.qz_word_label.setWordWrap(True)
        question_layout.addWidget(self.qz_word_label)
        
        # 音标显示
        self.qz_phonetic_label = QLabel()
        font = QFont("Arial", 12)
        self.qz_phonetic_label.setFont(font)
        self.qz_phonetic_label.setAlignment(Qt.AlignCenter)
        question_layout.addWidget(self.qz_phonetic_label)
        
        # 选项区域
        self.qz_options_group = QButtonGroup(self)
        self.qz_options_layout = QVBoxLayout()
        self.qz_options_layout.setSpacing(10)
        
        # 创建4个选项按钮
        self.qz_option_buttons = []
        for i in range(4):
            option_button = QRadioButton()
            option_button.setFont(QFont("微软雅黑", 12))
            option_button.setStyleSheet("""
                QRadioButton {
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #f5f5f5;
                }
                QRadioButton:hover {
                    background-color: #e0e0e0;
                }
                QRadioButton:checked {
                    background-color: #d0f0d0;
                }
            """)
            self.qz_options_group.addButton(option_button, i)
            self.qz_option_buttons.append(option_button)
            self.qz_options_layout.addWidget(option_button)
        
        question_layout.addLayout(self.qz_options_layout)
        quiz_layout.addWidget(question_frame)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # 收藏按钮
        self.qz_favorite_button = QPushButton("收藏")
        self.qz_favorite_button.setFont(QFont("微软雅黑", 10))
        self.qz_favorite_button.setMinimumSize(100, 35)
        self.qz_favorite_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.qz_favorite_button.clicked.connect(self.toggle_favorite)
        buttons_layout.addWidget(self.qz_favorite_button)
        
        # 发音按钮
        self.qz_pronounce_button = QPushButton("发音")
        self.qz_pronounce_button.setFont(QFont("微软雅黑", 10))
        self.qz_pronounce_button.setMinimumSize(100, 35)
        self.qz_pronounce_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.qz_pronounce_button.clicked.connect(self.pronounce_word)
        buttons_layout.addWidget(self.qz_pronounce_button)
        
        # 确认按钮
        self.qz_confirm_button = QPushButton("确认答案")
        self.qz_confirm_button.setFont(QFont("微软雅黑", 10))
        self.qz_confirm_button.setMinimumSize(100, 35)
        self.qz_confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.qz_confirm_button.clicked.connect(self.check_quiz_answer)
        buttons_layout.addWidget(self.qz_confirm_button)
        
        quiz_layout.addLayout(buttons_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        
        self.qz_progress_label = QLabel("进度:")
        progress_layout.addWidget(self.qz_progress_label)
        
        self.qz_progress_bar = QProgressBar()
        self.qz_progress_bar.setMinimum(0)
        self.qz_progress_bar.setMaximum(100)
        self.qz_progress_bar.setValue(0)
        self.qz_progress_bar.setTextVisible(True)
        self.qz_progress_bar.setFormat("%v% (%p/100)")
        progress_layout.addWidget(self.qz_progress_bar, 1)
        
        self.qz_counter_label = QLabel()
        progress_layout.addWidget(self.qz_counter_label)
        
        self.qz_result_label = QLabel()
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        self.qz_result_label.setFont(font)
        self.qz_result_label.setAlignment(Qt.AlignRight)
        progress_layout.addWidget(self.qz_result_label)
        
        quiz_layout.addLayout(progress_layout)
        
        self.content_stack.addWidget(quiz_widget)
    
    def create_typing_mode(self):
        """创建拼写模式界面"""
        typing_widget = QWidget()
        typing_layout = QVBoxLayout(typing_widget)
        typing_layout.setContentsMargins(0, 0, 0, 0)
        typing_layout.setSpacing(15)
        
        # 题目区域
        question_frame = QFrame()
        question_frame.setObjectName("typingFrame")
        question_frame.setStyleSheet("""
            QFrame#typingFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        question_layout = QVBoxLayout(question_frame)
        question_layout.setContentsMargins(20, 20, 20, 20)
        question_layout.setSpacing(15)
        
        # 释义显示
        self.tp_definition_label = QLabel()
        self.tp_definition_label.setFont(QFont("微软雅黑", 16))
        self.tp_definition_label.setAlignment(Qt.AlignCenter)
        self.tp_definition_label.setWordWrap(True)
        question_layout.addWidget(self.tp_definition_label)
        
        # 词性显示
        self.tp_pos_label = QLabel()
        self.tp_pos_label.setFont(QFont("微软雅黑", 12))
        self.tp_pos_label.setAlignment(Qt.AlignCenter)
        self.tp_pos_label.setStyleSheet("color: #7f8c8d;")
        question_layout.addWidget(self.tp_pos_label)
        
        # 提示区域
        hint_layout = QHBoxLayout()
        
        hint_layout.addWidget(QLabel("提示: "))
        
        self.tp_hint_label = QLabel()
        self.tp_hint_label.setFont(QFont("微软雅黑", 12))
        self.tp_hint_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tp_hint_label.setStyleSheet("color: #3498db;")
        hint_layout.addWidget(self.tp_hint_label)
        
        hint_layout.addStretch()
        
        question_layout.addLayout(hint_layout)
        
        # 输入区域
        from PyQt5.QtWidgets import QLineEdit
        
        self.tp_input = QLineEdit()
        self.tp_input.setFont(QFont("Arial", 16))
        self.tp_input.setMinimumHeight(40)
        self.tp_input.setPlaceholderText("请输入单词...")
        self.tp_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        self.tp_input.returnPressed.connect(self.check_typing_answer)
        question_layout.addWidget(self.tp_input)
        
        # 结果显示
        self.tp_result_label = QLabel()
        font = QFont("微软雅黑", 12)
        font.setBold(True)
        self.tp_result_label.setFont(font)
        self.tp_result_label.setAlignment(Qt.AlignCenter)
        self.tp_result_label.setWordWrap(True)
        self.tp_result_label.setMinimumHeight(30)
        question_layout.addWidget(self.tp_result_label)
        
        typing_layout.addWidget(question_frame)
        
        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # 提示按钮
        self.tp_hint_button = QPushButton("提示")
        self.tp_hint_button.setFont(QFont("微软雅黑", 10))
        self.tp_hint_button.setMinimumSize(100, 35)
        self.tp_hint_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.tp_hint_button.clicked.connect(self.give_typing_hint)
        buttons_layout.addWidget(self.tp_hint_button)
        
        # 收藏按钮
        self.tp_favorite_button = QPushButton("收藏")
        self.tp_favorite_button.setFont(QFont("微软雅黑", 10))
        self.tp_favorite_button.setMinimumSize(100, 35)
        self.tp_favorite_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.tp_favorite_button.clicked.connect(self.toggle_favorite)
        buttons_layout.addWidget(self.tp_favorite_button)
        
        # 跳过按钮
        self.tp_skip_button = QPushButton("跳过")
        self.tp_skip_button.setFont(QFont("微软雅黑", 10))
        self.tp_skip_button.setMinimumSize(100, 35)
        self.tp_skip_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.tp_skip_button.clicked.connect(lambda: self.next_word(False))
        buttons_layout.addWidget(self.tp_skip_button)
        
        # 确认按钮
        self.tp_confirm_button = QPushButton("确认")
        self.tp_confirm_button.setFont(QFont("微软雅黑", 10))
        self.tp_confirm_button.setMinimumSize(100, 35)
        self.tp_confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.tp_confirm_button.clicked.connect(self.check_typing_answer)
        buttons_layout.addWidget(self.tp_confirm_button)
        
        typing_layout.addLayout(buttons_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        
        self.tp_progress_label = QLabel("进度:")
        progress_layout.addWidget(self.tp_progress_label)
        
        self.tp_progress_bar = QProgressBar()
        self.tp_progress_bar.setMinimum(0)
        self.tp_progress_bar.setMaximum(100)
        self.tp_progress_bar.setValue(0)
        self.tp_progress_bar.setTextVisible(True)
        self.tp_progress_bar.setFormat("%v% (%p/100)")
        progress_layout.addWidget(self.tp_progress_bar, 1)
        
        self.tp_counter_label = QLabel()
        progress_layout.addWidget(self.tp_counter_label)
        
        typing_layout.addLayout(progress_layout)
        
        self.content_stack.addWidget(typing_widget) 

    def load_review_words(self):
        """加载复习单词"""
        try:
            # 获取需要复习的单词
            words = self.review_manager.get_review_words(days=7, limit=20)
            
            # 如果没有需要复习的单词，则获取重点词汇
            if not words:
                words = self.review_manager.get_favorite_words_for_review(limit=20)
            
            # 如果仍然没有单词，则随机获取词汇库中的单词
            if not words:
                words = self.review_manager.generate_review_quiz(count=20)
            
            # 保存单词列表
            self.review_words = words
            self.current_index = 0
            self.correct_count = 0
            
            # 更新单词显示
            self.update_word_display()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载复习单词失败: {e}")
    
    def change_mode(self, mode):
        """切换复习模式
        
        Args:
            mode: 模式名称
        """
        # 保存当前模式
        self.review_mode = mode
        
        # 切换界面
        if mode == 'flashcard':
            self.content_stack.setCurrentIndex(0)
        elif mode == 'quiz':
            self.content_stack.setCurrentIndex(1)
            self.prepare_quiz_options()
        elif mode == 'typing':
            self.content_stack.setCurrentIndex(2)
            self.tp_input.clear()
            self.tp_hint_label.clear()
            self.tp_result_label.clear()
        
        # 更新单词显示
        self.update_word_display()
    
    def update_word_display(self):
        """更新单词显示"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        # 获取当前单词
        word = self.review_words[self.current_index]
        
        # 根据当前模式更新显示
        if self.review_mode == 'flashcard':
            self.update_flashcard_display(word)
        elif self.review_mode == 'quiz':
            self.update_quiz_display(word)
        elif self.review_mode == 'typing':
            self.update_typing_display(word)
        
        # 更新进度
        self.update_progress()
    
    def update_progress(self):
        """更新进度显示"""
        if not self.review_words:
            return
        
        total = len(self.review_words)
        current = self.current_index + 1
        progress = int(current * 100 / total)
        
        # 根据当前模式更新对应的进度条
        if self.review_mode == 'flashcard':
            self.fc_progress_bar.setValue(progress)
            self.fc_counter_label.setText(f"{current}/{total}")
        elif self.review_mode == 'quiz':
            self.qz_progress_bar.setValue(progress)
            self.qz_counter_label.setText(f"{current}/{total}")
        elif self.review_mode == 'typing':
            self.tp_progress_bar.setValue(progress)
            self.tp_counter_label.setText(f"{current}/{total}")
    
    def update_flashcard_display(self, word):
        """更新闪卡模式显示
        
        Args:
            word: 单词信息
        """
        # 更新单词信息
        self.fc_word_label.setText(word['word'])
        self.fc_phonetic_label.setText(word['phonetic'] if word['phonetic'] else "")
        self.fc_pos_label.setText(word['pos'] if word['pos'] else "")
        self.fc_definition_label.setText(word['definition'])
        self.fc_example_label.setText(word['example'] if word['example'] else "")
        
        # 重置卡片状态到正面
        self.fc_content_stack.setCurrentIndex(0)
        
        # 更新收藏按钮状态
        self.update_favorite_button(word['id'])
    
    def update_quiz_display(self, word):
        """更新测验模式显示
        
        Args:
            word: 单词信息
        """
        # 更新单词信息
        self.qz_word_label.setText(word['word'])
        self.qz_phonetic_label.setText(word['phonetic'] if word['phonetic'] else "")
        
        # 准备选项
        self.prepare_quiz_options()
        
        # 更新收藏按钮状态
        self.update_favorite_button(word['id'])
        
        # 清除结果显示
        self.qz_result_label.clear()
        
        # 取消所有选项选中状态
        for button in self.qz_option_buttons:
            button.setChecked(False)
            button.setStyleSheet("""
                QRadioButton {
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #f5f5f5;
                }
                QRadioButton:hover {
                    background-color: #e0e0e0;
                }
                QRadioButton:checked {
                    background-color: #d0f0d0;
                }
            """)
    
    def update_typing_display(self, word):
        """更新拼写模式显示
        
        Args:
            word: 单词信息
        """
        # 更新信息
        self.tp_definition_label.setText(word['definition'])
        self.tp_pos_label.setText(word['pos'] if word['pos'] else "")
        
        # 清空输入框和提示
        self.tp_input.clear()
        self.tp_hint_label.clear()
        self.tp_result_label.clear()
        
        # 设置焦点到输入框
        self.tp_input.setFocus()
        
        # 更新收藏按钮状态
        self.update_favorite_button(word['id'])
    
    def update_favorite_button(self, word_id):
        """更新收藏按钮状态
        
        Args:
            word_id: 单词ID
        """
        is_favorite = self.vocab_manager.is_favorite(word_id)
        
        # 设置按钮文本和样式
        favorite_text = "取消收藏" if is_favorite else "收藏"
        favorite_style = """
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """ if is_favorite else """
            QPushButton {
                background-color: #e67e22;
                color: white;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """
        
        # 根据当前模式更新对应的按钮
        if self.review_mode == 'flashcard':
            self.fc_favorite_button.setText(favorite_text)
            self.fc_favorite_button.setStyleSheet(favorite_style)
        elif self.review_mode == 'quiz':
            self.qz_favorite_button.setText(favorite_text)
            self.qz_favorite_button.setStyleSheet(favorite_style)
        elif self.review_mode == 'typing':
            self.tp_favorite_button.setText(favorite_text)
            self.tp_favorite_button.setStyleSheet(favorite_style)
    
    def toggle_favorite(self):
        """切换收藏状态"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        word = self.review_words[self.current_index]
        word_id = word['id']
        
        if self.vocab_manager.is_favorite(word_id):
            # 取消收藏
            self.vocab_manager.unmark_favorite(word_id)
        else:
            # 添加收藏
            self.vocab_manager.mark_favorite(word_id)
        
        # 更新按钮状态
        self.update_favorite_button(word_id)
    
    def pronounce_word(self):
        """播放单词发音"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        word = self.review_words[self.current_index]['word']
        
        # 这里可以接入TTS或音频播放功能
        # 暂时用简单提示替代
        QMessageBox.information(self, "发音", f"播放单词: {word}")
    
    def next_word(self, remembered=True):
        """显示下一个单词
        
        Args:
            remembered: 是否记住了单词
        """
        if not self.review_words:
            return
        
        # 记录单词复习
        current_word = self.review_words[self.current_index]
        self.review_manager.record_review(current_word['id'])
        
        # 增加正确数量
        if remembered:
            self.correct_count += 1
        
        # 移动到下一个单词
        self.current_index += 1
        
        # 检查是否完成复习
        if self.current_index >= len(self.review_words):
            self.show_review_result()
            return
        
        # 更新单词显示
        self.update_word_display()
    
    def show_review_result(self):
        """显示复习结果"""
        total = len(self.review_words)
        correct = self.correct_count
        percentage = int(correct * 100 / total)
        
        QMessageBox.information(
            self,
            "复习完成",
            f"恭喜你完成了本次复习！\n\n"
            f"共复习 {total} 个单词\n"
            f"正确记忆 {correct} 个\n"
            f"正确率 {percentage}%"
        )
        
        # 发送复习完成信号
        self.review_completed.emit()
        
        # 关闭复习窗口
        self.close()
    
    def prepare_quiz_options(self):
        """准备测验选项"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        # 获取当前单词
        current_word = self.review_words[self.current_index]
        correct_definition = current_word['definition']
        
        # 获取干扰选项
        options = [correct_definition]
        other_words = [w for w in self.review_words if w['id'] != current_word['id']]
        
        # 如果没有足够的干扰选项，从之前的单词中获取
        if len(other_words) < 3:
            # 随机获取更多单词
            more_words = self.review_manager.get_review_words(
                days=30, limit=10, shuffle=True
            )
            other_words.extend(more_words)
        
        # 随机选择3个干扰选项
        if len(other_words) >= 3:
            random_words = random.sample(other_words, 3)
            for word in random_words:
                options.append(word['definition'])
        else:
            # 如果仍然没有足够的选项，使用固定的备用选项
            backup_options = [
                "这是一个备用选项1",
                "这是一个备用选项2",
                "这是一个备用选项3"
            ]
            options.extend(backup_options[:3 - len(other_words)])
        
        # 打乱选项顺序
        random.shuffle(options)
        
        # 记录正确答案的索引
        self.correct_option_index = options.index(correct_definition)
        
        # 更新选项按钮
        for i, option in enumerate(options):
            self.qz_option_buttons[i].setText(option)
    
    def check_quiz_answer(self):
        """检查测验答案"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        # 获取用户选择的选项
        selected_option = self.qz_options_group.checkedId()
        
        if selected_option == -1:
            # 没有选择任何选项
            QMessageBox.warning(self, "提示", "请选择一个选项")
            return
        
        # 检查答案是否正确
        is_correct = (selected_option == self.correct_option_index)
        
        # 设置结果显示
        if is_correct:
            self.qz_result_label.setText("✓ 回答正确！")
            self.qz_result_label.setStyleSheet("color: #2ecc71;")
            
            # 高亮正确选项
            self.qz_option_buttons[selected_option].setStyleSheet("""
                QRadioButton {
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #d0f0d0;
                }
                QRadioButton:checked {
                    background-color: #2ecc71;
                    color: white;
                }
            """)
        else:
            self.qz_result_label.setText("✗ 回答错误！")
            self.qz_result_label.setStyleSheet("color: #e74c3c;")
            
            # 高亮错误选项和正确选项
            self.qz_option_buttons[selected_option].setStyleSheet("""
                QRadioButton {
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #f0d0d0;
                }
                QRadioButton:checked {
                    background-color: #e74c3c;
                    color: white;
                }
            """)
            
            self.qz_option_buttons[self.correct_option_index].setStyleSheet("""
                QRadioButton {
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #d0f0d0;
                }
            """)
        
        # 延时进入下一个单词
        QTimer.singleShot(1500, lambda: self.next_word(is_correct))
    
    def check_typing_answer(self):
        """检查拼写答案"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        # 获取用户输入
        user_input = self.tp_input.text().strip().lower()
        
        if not user_input:
            # 输入为空
            QMessageBox.warning(self, "提示", "请输入单词")
            return
        
        # 获取正确答案
        correct_word = self.review_words[self.current_index]['word'].lower()
        
        # 检查答案是否正确
        is_correct = (user_input == correct_word)
        
        # 设置结果显示
        if is_correct:
            self.tp_result_label.setText("✓ 拼写正确！")
            self.tp_result_label.setStyleSheet("color: #2ecc71;")
        else:
            self.tp_result_label.setText(f"✗ 拼写错误！正确答案：{correct_word}")
            self.tp_result_label.setStyleSheet("color: #e74c3c;")
        
        # 延时进入下一个单词
        QTimer.singleShot(1500, lambda: self.next_word(is_correct))
    
    def give_typing_hint(self):
        """提供拼写提示"""
        if not self.review_words or self.current_index >= len(self.review_words):
            return
        
        # 获取正确单词
        correct_word = self.review_words[self.current_index]['word']
        
        # 生成提示（显示第一个字母和单词长度）
        hint = f"{correct_word[0]}{'_' * (len(correct_word) - 1)} ({len(correct_word)}个字母)"
        
        # 更新提示标签
        self.tp_hint_label.setText(hint) 