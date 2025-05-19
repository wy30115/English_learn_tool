import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QProgressBar, 
                            QFrame, QGridLayout, QSizePolicy, QSpacerItem,
                            QMessageBox, QAction, QMenu, QSystemTrayIcon,
                            QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap, QCursor, QColor, QLinearGradient, QPalette

from ..core.vocabulary import VocabularyManager
from ..core.learning import LearningManager
from ..core.review import ReviewManager
from ..data.database import Database
from ..data.config import Config
from .float_window import FloatWindow
from .settings_window import SettingsWindow
from .review_window import ReviewWindow


class MainWindow(QMainWindow):
    """应用主窗口"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化数据管理器
        self.db = Database()
        self.db.connect()
        self.db.create_tables()  # 确保数据表已创建
        
        self.config = Config()
        self.vocab_manager = VocabularyManager(self.db)
        self.learning_manager = LearningManager(self.db, self.config)
        self.review_manager = ReviewManager(self.db, self.config)
        
        # 子窗口
        self.float_window = None
        self.settings_window = None
        self.review_window = None
        
        # 设置应用名称和图标
        self.setWindowTitle("每日单词 - 英语学习工具")
        self.resize(850, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f7f9fc;
            }
            QLabel {
                color: #2c3e50;
            }
            QPushButton {
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        
        # 居中显示
        self.center_window()
        
        # 初始化界面
        self.init_ui()
        
        # 设置系统托盘
        self.init_tray_icon()
        
        # 更新学习统计
        self.update_statistics()
        
        # 定时更新统计信息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_statistics)
        self.timer.start(60000)  # 每分钟更新一次
        
        # 检查是否首次启动
        self.check_first_launch()
    
    def check_first_launch(self):
        """检查是否是首次启动，如果是则显示欢迎对话框"""
        # 安全地获取first_launch配置
        is_first_launch = False
        
        try:
            startup_config = self.config.get("startup")
            if isinstance(startup_config, dict):
                is_first_launch = startup_config.get("first_launch", True)
        except Exception as e:
            # 默认为首次启动
            is_first_launch = True
            print(f"获取首次启动设置时出错: {e}")
        
        if is_first_launch:
            welcome_msg = QMessageBox(self)
            welcome_msg.setWindowTitle("欢迎使用每日单词")
            welcome_msg.setIcon(QMessageBox.Information)
            welcome_msg.setText("欢迎使用每日单词学习工具！")
            welcome_msg.setInformativeText(
                "这是一款帮助您高效学习英语单词的应用。\n\n"
                "• 每日学习：设定目标，坚持每天学习\n"
                "• 科学复习：基于记忆曲线，提高记忆效率\n"
                "• 悬浮窗模式：随时随地学习单词\n\n"
                "准备好开始您的英语学习之旅了吗？"
            )
            welcome_msg.setStandardButtons(QMessageBox.Ok)
            welcome_msg.button(QMessageBox.Ok).setText("开始使用")
            welcome_msg.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                    color: #2c3e50;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            
            welcome_msg.exec_()
            
            # 更新配置，下次不再显示
            self.config.set("startup", "first_launch", False)
    
    def center_window(self):
        """将窗口居中显示"""
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央窗口
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 顶部标题和欢迎语
        self.create_header(main_layout)
        
        # 学习统计面板
        self.create_stats_panel(main_layout)
        
        # 快捷功能按钮
        self.create_action_buttons(main_layout)
        
        # 底部状态栏
        self.statusBar().showMessage("准备就绪")
        self.statusBar().setStyleSheet("background-color: #34495e; color: white; padding: 3px;")
    
    def create_header(self, parent_layout):
        """创建顶部标题区域
        
        Args:
            parent_layout: 父布局
        """
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet("""
            QFrame#headerFrame { 
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                color: white;
            }
            QLabel { color: white; }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        header_frame.setGraphicsEffect(shadow)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # 应用Logo
        logo_label = QLabel()
        # 可以在这里设置一个图标
        logo_label.setPixmap(QPixmap("assets/logo.png").scaled(64, 64, Qt.KeepAspectRatio))
        logo_label.setText("📚")  # 临时使用emoji代替
        logo_label.setFont(QFont("Arial", 36))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setMinimumSize(80, 80)
        header_layout.addWidget(logo_label)
        
        # 标题和欢迎语
        title_layout = QVBoxLayout()
        
        title_label = QLabel("每日单词")
        font = QFont("微软雅黑", 22)
        font.setBold(True)
        title_label.setFont(font)
        title_layout.addWidget(title_label)
        
        welcome_label = QLabel("欢迎使用每日单词，坚持每天学习，提高英语水平！")
        welcome_label.setFont(QFont("微软雅黑", 11))
        title_layout.addWidget(welcome_label)
        
        header_layout.addLayout(title_layout, 1)
        parent_layout.addWidget(header_frame)
    
    def create_stats_panel(self, parent_layout):
        """创建学习统计面板
        
        Args:
            parent_layout: 父布局
        """
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_frame.setStyleSheet("""
            QFrame#statsFrame { 
                background-color: white; 
                border-radius: 10px; 
                border: 1px solid #e0e0e0; 
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        stats_frame.setGraphicsEffect(shadow)
        
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(15)
        
        # 统计标题
        stats_title = QLabel("学习统计")
        font = QFont("微软雅黑", 14)
        font.setBold(True)
        stats_title.setFont(font)
        stats_title.setAlignment(Qt.AlignCenter)
        stats_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        stats_layout.addWidget(stats_title)
        
        # 今日进度
        progress_layout = QHBoxLayout()
        
        progress_label = QLabel("今日学习进度:")
        progress_label.setFont(QFont("微软雅黑", 10))
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v% (%p/100)")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar, 1)
        
        stats_layout.addLayout(progress_layout)
        
        # 详细统计面板
        stats_detail_frame = QFrame()
        stats_detail_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 5px;
            }
            QLabel {
                padding: 5px;
            }
        """)
        stats_grid = QGridLayout(stats_detail_frame)
        stats_grid.setContentsMargins(15, 15, 15, 15)
        stats_grid.setSpacing(15)
        stats_grid.setColumnStretch(1, 1)
        stats_grid.setColumnStretch(3, 1)
        
        # 统计项样式
        label_style = "font-weight: bold; color: #34495e;"
        value_style = "color: #2980b9; font-weight: bold;"
        
        # 第一行
        today_title = QLabel("今日学习:")
        today_title.setStyleSheet(label_style)
        stats_grid.addWidget(today_title, 0, 0)
        
        self.today_label = QLabel("0 个单词")
        self.today_label.setStyleSheet(value_style)
        stats_grid.addWidget(self.today_label, 0, 1)
        
        target_title = QLabel("学习目标:")
        target_title.setStyleSheet(label_style)
        stats_grid.addWidget(target_title, 0, 2)
        
        self.target_label = QLabel("10 个单词/天")
        self.target_label.setStyleSheet(value_style)
        stats_grid.addWidget(self.target_label, 0, 3)
        
        # 第二行
        total_title = QLabel("累计学习:")
        total_title.setStyleSheet(label_style)
        stats_grid.addWidget(total_title, 1, 0)
        
        self.total_label = QLabel("0 个单词")
        self.total_label.setStyleSheet(value_style)
        stats_grid.addWidget(self.total_label, 1, 1)
        
        favorites_title = QLabel("重点词汇:")
        favorites_title.setStyleSheet(label_style)
        stats_grid.addWidget(favorites_title, 1, 2)
        
        self.favorites_label = QLabel("0 个单词")
        self.favorites_label.setStyleSheet(value_style)
        stats_grid.addWidget(self.favorites_label, 1, 3)
        
        # 第三行
        streak_title = QLabel("连续学习:")
        streak_title.setStyleSheet(label_style)
        stats_grid.addWidget(streak_title, 2, 0)
        
        self.streak_label = QLabel("0 天")
        self.streak_label.setStyleSheet(value_style)
        stats_grid.addWidget(self.streak_label, 2, 1)
        
        review_title = QLabel("待复习:")
        review_title.setStyleSheet(label_style)
        stats_grid.addWidget(review_title, 2, 2)
        
        self.review_label = QLabel("0 个单词")
        self.review_label.setStyleSheet(value_style)
        stats_grid.addWidget(self.review_label, 2, 3)
        
        stats_layout.addWidget(stats_detail_frame)
        parent_layout.addWidget(stats_frame)
    
    def create_action_buttons(self, parent_layout):
        """创建操作按钮区域
        
        Args:
            parent_layout: 父布局
        """
        buttons_frame = QFrame()
        buttons_frame.setObjectName("buttonsFrame")
        buttons_frame.setStyleSheet("""
            QFrame#buttonsFrame { 
                background-color: white; 
                border-radius: 10px; 
                border: 1px solid #e0e0e0; 
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        buttons_frame.setGraphicsEffect(shadow)
        
        buttons_layout = QVBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(20, 20, 20, 20)
        buttons_layout.setSpacing(15)
        
        # 按钮标题
        buttons_title = QLabel("快捷功能")
        font = QFont("微软雅黑", 14)
        font.setBold(True)
        buttons_title.setFont(font)
        buttons_title.setAlignment(Qt.AlignCenter)
        buttons_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        buttons_layout.addWidget(buttons_title)
        
        # 功能按钮
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        # 开始学习按钮
        self.start_button = self.create_feature_button(
            "开始学习", 
            "🔤", 
            "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2980b9)",
            self.start_learning
        )
        grid_layout.addWidget(self.start_button, 0, 0)
        
        # 单词复习按钮
        self.review_button = self.create_feature_button(
            "单词复习", 
            "🔄", 
            "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #d35400)",
            self.start_review
        )
        grid_layout.addWidget(self.review_button, 0, 1)
        
        # 设置按钮
        self.settings_button = self.create_feature_button(
            "应用设置", 
            "⚙️", 
            "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60)",
            self.open_settings
        )
        grid_layout.addWidget(self.settings_button, 1, 0)
        
        # 退出按钮
        self.exit_button = self.create_feature_button(
            "退出应用", 
            "🚪", 
            "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b)",
            self.close_app
        )
        grid_layout.addWidget(self.exit_button, 1, 1)
        
        buttons_layout.addLayout(grid_layout)
        parent_layout.addWidget(buttons_frame)
    
    def create_feature_button(self, text, icon, color, callback):
        """创建特色功能按钮
        
        Args:
            text: 按钮文本
            icon: 按钮图标(Emoji)
            color: 按钮颜色
            callback: 点击回调函数
            
        Returns:
            button: 按钮对象
        """
        button = QPushButton()
        button.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 垂直布局
        button_layout = QVBoxLayout(button)
        button_layout.setContentsMargins(10, 15, 10, 15)
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignCenter)
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(icon_label)
        
        # 文本
        text_label = QLabel(text)
        font = QFont("微软雅黑", 12)
        font.setBold(True)
        text_label.setFont(font)
        text_label.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(text_label)
        
        # 样式
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                border: none;
                padding: 15px 10px;
                min-height: 100px;
            }}
            QPushButton:hover {{
                background-color: {color};
                border: 2px solid white;
            }}
            QPushButton:pressed {{
                background-color: {color};
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        button.setGraphicsEffect(shadow)
        
        # 连接信号
        button.clicked.connect(callback)
        
        return button
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 创建托盘图标菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        start_action = QAction("开始学习", self)
        start_action.triggered.connect(self.start_learning)
        tray_menu.addAction(start_action)
        
        review_action = QAction("单词复习", self)
        review_action.triggered.connect(self.start_review)
        tray_menu.addAction(review_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_app)
        tray_menu.addAction(exit_action)
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("每日单词")
        
        # 设置图标 - 尝试从assets目录加载图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets', 'logo.png')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 如果图标文件不存在，使用应用默认图标
            self.tray_icon.setIcon(self.windowIcon())
            
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """托盘图标激活响应
        
        Args:
            reason: 激活原因
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def update_statistics(self):
        """更新学习统计信息"""
        try:
            # 获取学习状态
            learning_status = self.learning_manager.get_learning_status()
            
            # 更新进度条
            self.progress_bar.setValue(learning_status['completion_percentage'])
            
            # 获取学习统计
            vocab_stats = self.vocab_manager.get_learning_statistics()
            review_stats = self.review_manager.get_review_statistics()
            
            # 更新统计标签
            self.today_label.setText(f"{learning_status['today_learned']} 个单词")
            self.target_label.setText(f"{learning_status['daily_target']} 个单词/天")
            self.total_label.setText(f"{vocab_stats['learned_words']} 个单词")
            self.favorites_label.setText(f"{vocab_stats['favorite_words']} 个单词")
            self.streak_label.setText(f"{vocab_stats['streak_days']} 天")
            self.review_label.setText(f"{review_stats['need_review_count']} 个单词")
            
            # 如果今日学习完成且进度条为0，重置为100%
            if learning_status['is_completed'] and self.progress_bar.value() == 0:
                self.progress_bar.setValue(100)
                
        except Exception as e:
            self.statusBar().showMessage(f"更新统计出错: {e}")
    
    def start_learning(self):
        """开始学习，打开悬浮窗"""
        # 如果悬浮窗已存在，则激活
        if self.float_window and self.float_window.isVisible():
            self.float_window.activateWindow()
            return
        
        try:
            # 获取学习计划
            study_plan = self.learning_manager.get_daily_plan()
            
            # 获取每日单词
            daily_words = self.vocab_manager.get_daily_words(
                count=study_plan['daily_words'],
                difficulty_min=study_plan['difficulty_range'][0],
                difficulty_max=study_plan['difficulty_range'][1]
            )
            
            if not daily_words:
                QMessageBox.information(self, "提示", "词汇库为空或无可学习的单词，请先导入词汇。")
                return
            
            # 创建并显示悬浮窗
            self.float_window = FloatWindow(
                self.vocab_manager, 
                self.learning_manager,
                daily_words
            )
            self.float_window.closed.connect(self.update_statistics)
            self.float_window.show()
            
            # 最小化主窗口
            self.setWindowState(Qt.WindowMinimized)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动学习模式失败: {e}")
    
    def start_review(self):
        """开始复习单词"""
        try:
            # 创建并显示复习窗口
            self.review_window = ReviewWindow(
                self.vocab_manager, 
                self.learning_manager,
                self.review_manager
            )
            self.review_window.review_completed.connect(self.update_statistics)
            self.review_window.show()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动复习模式失败: {e}")
    
    def open_settings(self):
        """打开设置窗口"""
        # 如果设置窗口已存在，则激活
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.activateWindow()
            return
            
        try:
            # 创建并显示设置窗口
            self.settings_window = SettingsWindow(
                self.config, 
                self.vocab_manager, 
                self.learning_manager
            )
            self.settings_window.settings_updated.connect(self.update_statistics)
            self.settings_window.show()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开设置失败: {e}")
    
    def close_app(self):
        """关闭应用程序"""
        reply = QMessageBox.question(
            self, 
            "确认退出", 
            "确定要退出应用吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 关闭数据库连接
            if hasattr(self, 'db') and self.db:
                self.db.close()
                
            # 关闭定时器
            if hasattr(self, 'timer') and self.timer:
                self.timer.stop()
                
            # 关闭子窗口
            if self.float_window:
                self.float_window.close()
                
            if self.settings_window:
                self.settings_window.close()
                
            if self.review_window:
                self.review_window.close()
                
            # 移除托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
                
            # 退出应用
            QApplication.quit()
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        Args:
            event: 关闭事件
        """
        # 如果是系统托盘模式，则最小化到托盘
        # 改用更明确的方式获取配置
        minimize_to_tray = True  # 默认值
        
        try:
            startup_config = self.config.get('startup')
            if isinstance(startup_config, dict):
                minimize_to_tray = startup_config.get('minimize_to_tray', True)
        except Exception as e:
            print(f"获取托盘设置时出错: {e}")
            # 使用默认值
        
        if minimize_to_tray:
            event.ignore()
            self.hide()
            
            # 显示托盘消息，更明确地告知用户应用在系统托盘中
            self.tray_icon.showMessage(
                "每日单词 - 已最小化到系统托盘",
                "应用正在后台运行。\n请查看屏幕右下角的系统托盘区域，双击图标可重新打开窗口。",
                QSystemTrayIcon.Information,
                5000  # 显示5秒
            )
        else:
            self.close_app()
            event.accept() 