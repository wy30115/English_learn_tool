import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QTabWidget, QGridLayout, QSpinBox,
                            QComboBox, QTimeEdit, QCheckBox, QFileDialog,
                            QMessageBox, QSlider, QLineEdit, QGroupBox,
                            QGraphicsDropShadowEffect, QButtonGroup, QRadioButton,
                            QProgressDialog)
from PyQt5.QtCore import Qt, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QCursor
from PyQt5.QtWidgets import QApplication
import pandas as pd

from ..core.vocabulary import VocabularyManager
from ..core.learning import LearningManager
from ..data.config import Config


class SettingsWindow(QWidget):
    """设置窗口"""
    
    # 自定义信号
    settings_updated = pyqtSignal()  # 设置更新信号
    
    def __init__(self, config, vocab_manager, learning_manager):
        """初始化设置窗口
        
        Args:
            config: 配置管理器
            vocab_manager: 词汇管理器
            learning_manager: 学习管理器
        """
        super().__init__()
        
        # 初始化数据
        self.config = config
        self.vocab_manager = vocab_manager
        self.learning_manager = learning_manager
        
        # 设置窗口属性
        self.setWindowTitle("应用设置")
        self.resize(600, 450)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 初始化UI
        self.init_ui()
        
        # 加载设置
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f7f9fc;
                color: #2c3e50;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #7f8c8d;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #3498db;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d6eaf8;
                color: #2980b9;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 15px;
                background-color: white;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #34495e;
            }
            QSpinBox, QComboBox, QTimeEdit, QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QSpinBox:focus, QComboBox:focus, QTimeEdit:focus, QLineEdit:focus {
                border: 1px solid #3498db;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
        """)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setFont(QFont("微软雅黑", 11))
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        tab_widget.setGraphicsEffect(shadow)
        
        # 学习设置选项卡
        study_tab = self.create_study_tab()
        tab_widget.addTab(study_tab, "学习设置")
        
        # 显示设置选项卡
        display_tab = self.create_display_tab()
        tab_widget.addTab(display_tab, "显示设置")
        
        # 数据管理选项卡
        data_tab = self.create_data_tab()
        tab_widget.addTab(data_tab, "数据管理")
        
        # 添加选项卡到主布局
        main_layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # 重置按钮
        self.reset_button = QPushButton("重置设置")
        font = QFont("微软雅黑", 11)
        font.setBold(True)
        self.reset_button.setFont(font)
        self.reset_button.setMinimumSize(120, 40)
        self.reset_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #f39c12);
                border: 1px solid white;
            }
            QPushButton:pressed {
                padding-top: 1px;
                padding-left: 1px;
            }
        """)
        
        # 为按钮添加阴影
        reset_shadow = QGraphicsDropShadowEffect()
        reset_shadow.setBlurRadius(10)
        reset_shadow.setColor(QColor(0, 0, 0, 60))
        reset_shadow.setOffset(0, 2)
        self.reset_button.setGraphicsEffect(reset_shadow)
        
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)
        
        # 添加伸缩项
        button_layout.addStretch(1)
        
        # 保存按钮
        self.save_button = QPushButton("保存设置")
        font = QFont("微软雅黑", 11)
        font.setBold(True)
        self.save_button.setFont(font)
        self.save_button.setMinimumSize(120, 40)
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                color: white;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #2ecc71);
                border: 1px solid white;
            }
            QPushButton:pressed {
                padding-top: 1px;
                padding-left: 1px;
            }
        """)
        
        # 为按钮添加阴影
        save_shadow = QGraphicsDropShadowEffect()
        save_shadow.setBlurRadius(10)
        save_shadow.setColor(QColor(0, 0, 0, 60))
        save_shadow.setOffset(0, 2)
        self.save_button.setGraphicsEffect(save_shadow)
        
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        font = QFont("微软雅黑", 11)
        font.setBold(True)
        self.cancel_button.setFont(font)
        self.cancel_button.setMinimumSize(120, 40)
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #e74c3c);
                border: 1px solid white;
            }
            QPushButton:pressed {
                padding-top: 1px;
                padding-left: 1px;
            }
        """)
        
        # 为按钮添加阴影
        cancel_shadow = QGraphicsDropShadowEffect()
        cancel_shadow.setBlurRadius(10)
        cancel_shadow.setColor(QColor(0, 0, 0, 60))
        cancel_shadow.setOffset(0, 2)
        self.cancel_button.setGraphicsEffect(cancel_shadow)
        
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def create_study_tab(self):
        """创建学习设置选项卡
        
        Returns:
            widget: 学习设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 每日学习设置组
        daily_group = QGroupBox("每日学习设置")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        daily_group.setFont(font)
        daily_layout = QGridLayout(daily_group)
        daily_layout.setColumnStretch(1, 1)
        
        # 每日单词数量
        daily_layout.addWidget(QLabel("每日单词数量:"), 0, 0)
        self.daily_words_spin = QSpinBox()
        self.daily_words_spin.setRange(1, 100)
        self.daily_words_spin.setValue(10)
        self.daily_words_spin.setSingleStep(1)
        daily_layout.addWidget(self.daily_words_spin, 0, 1)
        
        # 单词难度范围
        daily_layout.addWidget(QLabel("单词难度范围:"), 1, 0)
        difficulty_layout = QHBoxLayout()
        
        self.min_difficulty_spin = QSpinBox()
        self.min_difficulty_spin.setRange(1, 5)
        self.min_difficulty_spin.setValue(1)
        difficulty_layout.addWidget(self.min_difficulty_spin)
        
        difficulty_layout.addWidget(QLabel(" - "))
        
        self.max_difficulty_spin = QSpinBox()
        self.max_difficulty_spin.setRange(1, 5)
        self.max_difficulty_spin.setValue(3)
        difficulty_layout.addWidget(self.max_difficulty_spin)
        
        difficulty_layout.addStretch()
        daily_layout.addLayout(difficulty_layout, 1, 1)
        
        # 提醒时间
        daily_layout.addWidget(QLabel("学习提醒时间:"), 2, 0)
        self.reminder_time_edit = QTimeEdit()
        self.reminder_time_edit.setTime(QTime(8, 0))
        self.reminder_time_edit.setDisplayFormat("HH:mm")
        daily_layout.addWidget(self.reminder_time_edit, 2, 1)
        
        layout.addWidget(daily_group)
        
        # 复习设置组
        review_group = QGroupBox("复习设置")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        review_group.setFont(font)
        review_layout = QGridLayout(review_group)
        review_layout.setColumnStretch(1, 1)
        
        # 自动安排复习
        review_layout.addWidget(QLabel("自动安排复习:"), 0, 0)
        self.auto_review_check = QCheckBox("开启")
        self.auto_review_check.setChecked(True)
        review_layout.addWidget(self.auto_review_check, 0, 1)
        
        # 复习提醒方式
        review_layout.addWidget(QLabel("复习提醒方式:"), 1, 0)
        self.review_remind_combo = QComboBox()
        self.review_remind_combo.addItems(["通知提醒", "悬浮窗提醒", "不提醒"])
        review_layout.addWidget(self.review_remind_combo, 1, 1)
        
        layout.addWidget(review_group)
        
        # 启动设置组
        startup_group = QGroupBox("启动设置")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        startup_group.setFont(font)
        startup_layout = QGridLayout(startup_group)
        startup_layout.setColumnStretch(1, 1)
        
        # 开机自启动
        startup_layout.addWidget(QLabel("开机自启动:"), 0, 0)
        self.auto_start_check = QCheckBox("开启")
        startup_layout.addWidget(self.auto_start_check, 0, 1)
        
        # 启动时最小化
        startup_layout.addWidget(QLabel("启动时最小化:"), 1, 0)
        self.start_minimized_check = QCheckBox("开启")
        startup_layout.addWidget(self.start_minimized_check, 1, 1)
        
        # 关闭到托盘
        startup_layout.addWidget(QLabel("关闭到系统托盘:"), 2, 0)
        self.minimize_to_tray_check = QCheckBox("开启")
        self.minimize_to_tray_check.setChecked(True)
        startup_layout.addWidget(self.minimize_to_tray_check, 2, 1)
        
        layout.addWidget(startup_group)
        
        # 添加伸缩项
        layout.addStretch()
        
        return tab
    
    def create_display_tab(self):
        """创建显示设置选项卡
        
        Returns:
            widget: 显示设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 悬浮窗设置组
        float_group = QGroupBox("悬浮窗设置")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        float_group.setFont(font)
        float_layout = QGridLayout(float_group)
        float_layout.setColumnStretch(1, 1)
        
        # 悬浮窗透明度
        float_layout.addWidget(QLabel("悬浮窗透明度:"), 0, 0)
        opacity_layout = QHBoxLayout()
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        opacity_layout.addWidget(self.opacity_slider, 1)
        
        self.opacity_label = QLabel("85%")
        opacity_layout.addWidget(self.opacity_label)
        
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        
        float_layout.addLayout(opacity_layout, 0, 1)
        
        # 悬浮窗大小
        float_layout.addWidget(QLabel("悬浮窗大小:"), 1, 0)
        size_layout = QHBoxLayout()
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(200, 800)
        self.window_width_spin.setValue(350)
        self.window_width_spin.setSuffix(" px")
        size_layout.addWidget(self.window_width_spin)
        
        size_layout.addWidget(QLabel(" × "))
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(150, 600)
        self.window_height_spin.setValue(250)
        self.window_height_spin.setSuffix(" px")
        size_layout.addWidget(self.window_height_spin)
        
        size_layout.addStretch()
        float_layout.addLayout(size_layout, 1, 1)
        
        layout.addWidget(float_group)
        
        # 显示设置组
        display_group = QGroupBox("显示设置")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        display_group.setFont(font)
        display_layout = QGridLayout(display_group)
        display_layout.setColumnStretch(1, 1)
        
        # 界面主题
        display_layout.addWidget(QLabel("界面主题:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        display_layout.addWidget(self.theme_combo, 0, 1)
        
        # 字体大小
        display_layout.addWidget(QLabel("字体大小:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(14)
        self.font_size_spin.setSuffix(" px")
        display_layout.addWidget(self.font_size_spin, 1, 1)
        
        layout.addWidget(display_group)
        
        # 添加伸缩项
        layout.addStretch()
        
        return tab
    
    def create_data_tab(self):
        """创建数据管理选项卡
        
        Returns:
            widget: 数据管理选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 词汇导入组
        import_group = QGroupBox("词汇导入")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        import_group.setFont(font)
        import_layout = QVBoxLayout(import_group)
        
        # 导入说明
        import_info = QLabel("从CSV文件导入词汇，CSV文件需包含以下列：word(单词)、definition(释义)，可选列：phonetic(音标)、pos(词性)、example(例句)、frequency(频率)、difficulty(难度)")
        import_info.setWordWrap(True)
        import_layout.addWidget(import_info)
        
        # 添加导入模式选择
        import_mode_label = QLabel("导入模式:")
        import_layout.addWidget(import_mode_label)
        
        import_mode_layout = QVBoxLayout()
        self.import_mode_group = QButtonGroup(self)
        
        # 仅新单词模式
        self.new_only_radio = QRadioButton("仅导入新单词（跳过已存在的单词）")
        self.import_mode_group.addButton(self.new_only_radio, 0)
        import_mode_layout.addWidget(self.new_only_radio)
        
        # 更新模式（默认）
        self.update_radio = QRadioButton("更新现有单词，导入新单词（默认）")
        self.update_radio.setChecked(True)
        self.import_mode_group.addButton(self.update_radio, 1)
        import_mode_layout.addWidget(self.update_radio)
        
        # 覆盖模式
        self.overwrite_radio = QRadioButton("覆盖所有单词（不检查是否存在）")
        self.import_mode_group.addButton(self.overwrite_radio, 2)
        import_mode_layout.addWidget(self.overwrite_radio)
        
        import_layout.addLayout(import_mode_layout)
        
        # 导入按钮
        import_button_layout = QHBoxLayout()
        
        self.import_path_edit = QLineEdit()
        self.import_path_edit.setPlaceholderText("请选择CSV文件...")
        self.import_path_edit.setReadOnly(True)
        import_button_layout.addWidget(self.import_path_edit, 1)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_csv_file)
        import_button_layout.addWidget(self.browse_button)
        
        self.import_button = QPushButton("导入词汇")
        self.import_button.clicked.connect(self.import_vocabulary)
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        import_button_layout.addWidget(self.import_button)
        
        import_layout.addLayout(import_button_layout)
        layout.addWidget(import_group)
        
        # 数据备份组
        backup_group = QGroupBox("数据备份")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        backup_group.setFont(font)
        backup_layout = QGridLayout(backup_group)
        backup_layout.setColumnStretch(2, 1)
        
        # 数据备份
        backup_layout.addWidget(QLabel("备份数据:"), 0, 0)
        self.backup_button = QPushButton("备份")
        self.backup_button.clicked.connect(self.backup_data)
        backup_layout.addWidget(self.backup_button, 0, 1)
        
        # 数据恢复
        backup_layout.addWidget(QLabel("恢复数据:"), 1, 0)
        self.restore_button = QPushButton("恢复")
        self.restore_button.clicked.connect(self.restore_data)
        backup_layout.addWidget(self.restore_button, 1, 1)
        
        layout.addWidget(backup_group)
        
        # 数据重置组
        reset_group = QGroupBox("数据重置")
        font = QFont("微软雅黑", 10)
        font.setBold(True)
        reset_group.setFont(font)
        reset_layout = QVBoxLayout(reset_group)
        
        # 重置警告
        reset_warning = QLabel("警告：重置数据将清空所有学习记录和设置，此操作不可撤销！")
        reset_warning.setStyleSheet("color: #e74c3c;")
        reset_warning.setWordWrap(True)
        reset_layout.addWidget(reset_warning)
        
        # 重置按钮
        reset_button_layout = QHBoxLayout()
        reset_button_layout.addStretch()
        
        self.reset_button = QPushButton("重置所有数据")
        self.reset_button.clicked.connect(self.reset_data)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                border: none;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_button_layout.addWidget(self.reset_button)
        
        reset_layout.addLayout(reset_button_layout)
        layout.addWidget(reset_group)
        
        # 添加伸缩项
        layout.addStretch()
        
        return tab
    
    def load_settings(self):
        """加载设置"""
        try:
            # 加载学习设置
            study_config = self.config.get('study')
            if isinstance(study_config, dict):
                self.daily_words_spin.setValue(study_config.get('daily_words', 10))
                
                difficulty_range = study_config.get('difficulty_range', [1, 3])
                if isinstance(difficulty_range, list) and len(difficulty_range) >= 2:
                    self.min_difficulty_spin.setValue(difficulty_range[0])
                    self.max_difficulty_spin.setValue(difficulty_range[1])
                else:
                    # 使用默认值
                    self.min_difficulty_spin.setValue(1)
                    self.max_difficulty_spin.setValue(3)
                
                reminder_time = study_config.get('reminder_time', '08:00')
                try:
                    hours, minutes = map(int, str(reminder_time).split(':'))
                    self.reminder_time_edit.setTime(QTime(hours, minutes))
                except (ValueError, AttributeError):
                    # 使用默认值
                    self.reminder_time_edit.setTime(QTime(8, 0))
            else:
                # 使用默认值
                self.daily_words_spin.setValue(10)
                self.min_difficulty_spin.setValue(1)
                self.max_difficulty_spin.setValue(3)
                self.reminder_time_edit.setTime(QTime(8, 0))
            
            # 加载复习设置
            review_config = self.config.get('review')
            if isinstance(review_config, dict):
                self.auto_review_check.setChecked(review_config.get('auto_review', True))
                
                remind_method = review_config.get('remind_method', 0)
                self.review_remind_combo.setCurrentIndex(min(max(0, remind_method), self.review_remind_combo.count() - 1))
            else:
                # 使用默认值
                self.auto_review_check.setChecked(True)
                self.review_remind_combo.setCurrentIndex(0)
            
            # 加载启动设置
            startup_config = self.config.get('startup')
            if isinstance(startup_config, dict):
                self.auto_start_check.setChecked(startup_config.get('auto_start', False))
                self.start_minimized_check.setChecked(startup_config.get('start_minimized', False))
                self.minimize_to_tray_check.setChecked(startup_config.get('minimize_to_tray', True))
            else:
                # 使用默认值
                self.auto_start_check.setChecked(False)
                self.start_minimized_check.setChecked(False)
                self.minimize_to_tray_check.setChecked(True)
            
            # 加载显示设置
            window_config = self.config.get('window')
            if isinstance(window_config, dict):
                try:
                    opacity = int(float(window_config.get('opacity', 0.85)) * 100)
                    self.opacity_slider.setValue(min(max(0, opacity), 100))
                except (ValueError, TypeError):
                    self.opacity_slider.setValue(85)
                
                size = window_config.get('size', [350, 250])
                if isinstance(size, list) and len(size) >= 2:
                    try:
                        self.window_width_spin.setValue(int(size[0]))
                        self.window_height_spin.setValue(int(size[1]))
                    except (ValueError, TypeError):
                        self.window_width_spin.setValue(350)
                        self.window_height_spin.setValue(250)
                else:
                    self.window_width_spin.setValue(350)
                    self.window_height_spin.setValue(250)
            else:
                # 使用默认值
                self.opacity_slider.setValue(85)
                self.window_width_spin.setValue(350)
                self.window_height_spin.setValue(250)
            
            display_config = self.config.get('display')
            if isinstance(display_config, dict):
                theme = display_config.get('theme', 'light')
                self.theme_combo.setCurrentIndex(0 if theme == 'light' else 1)
                
                try:
                    font_size = int(display_config.get('font_size', 14))
                    self.font_size_spin.setValue(min(max(8, font_size), 24))
                except (ValueError, TypeError):
                    self.font_size_spin.setValue(14)
            else:
                # 使用默认值
                self.theme_combo.setCurrentIndex(0)  # 默认使用亮色主题
                self.font_size_spin.setValue(14)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载设置失败: {e}")
            # 加载失败时使用默认设置
            self.set_default_values()
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存学习设置
            study_config = {
                'daily_words': int(self.daily_words_spin.value()),
                'difficulty_range': [
                    int(self.min_difficulty_spin.value()),
                    int(self.max_difficulty_spin.value())
                ],
                'reminder_time': self.reminder_time_edit.time().toString('HH:mm')
            }
            self.config.set_section('study', study_config)
            
            # 保存复习设置
            review_config = {
                'auto_review': bool(self.auto_review_check.isChecked()),
                'remind_method': int(self.review_remind_combo.currentIndex())
            }
            self.config.set_section('review', review_config)
            
            # 保存启动设置
            startup_config = {
                'auto_start': bool(self.auto_start_check.isChecked()),
                'start_minimized': bool(self.start_minimized_check.isChecked()),
                'minimize_to_tray': bool(self.minimize_to_tray_check.isChecked())
            }
            self.config.set_section('startup', startup_config)
            
            # 保存显示设置
            window_config = {
                'opacity': float(self.opacity_slider.value()) / 100.0,
                'size': [
                    int(self.window_width_spin.value()),
                    int(self.window_height_spin.value())
                ]
            }
            self.config.set_section('window', window_config)
            
            display_config = {
                'theme': 'light' if self.theme_combo.currentIndex() == 0 else 'dark',
                'font_size': int(self.font_size_spin.value())
            }
            self.config.set_section('display', display_config)
            
            # 如果设置了开机自启动，则需要系统操作
            if self.auto_start_check.isChecked():
                self.setup_autostart()
            
            # 发送设置更新信号
            self.settings_updated.emit()
            
            QMessageBox.information(self, "成功", "设置已保存")
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_autostart(self):
        """设置开机自启动"""
        # 这里需要根据系统类型实现不同的开机自启动方法
        # Windows系统可以使用注册表
        # 此处简化处理，仅记录设置
        pass
    
    def browse_csv_file(self):
        """浏览CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择CSV文件",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if file_path:
            self.import_path_edit.setText(file_path)
    
    def import_vocabulary(self):
        """导入词汇"""
        file_path = self.import_path_edit.text()
        
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择CSV文件")
            return
        
        # 创建专用进度对话框
        progress = QProgressDialog("正在导入词汇，请稍候...", "取消", 0, 100, self)
        progress.setWindowTitle("导入中")
        progress.setWindowModality(Qt.WindowModal)  # 模态对话框
        progress.setMinimumDuration(0)  # 立即显示
        progress.setValue(10)  # 初始进度
        progress.setAutoClose(True)  # 自动关闭
        progress.setCancelButton(None)  # 移除取消按钮
        QApplication.processEvents()
        
        try:
            # 更新进度
            progress.setValue(30)
            QApplication.processEvents()
            
            # 导入词汇
            result = self.vocab_manager.import_from_csv(file_path)
            
            # 更新进度
            progress.setValue(80)
            QApplication.processEvents()
            
            # 关闭进度对话框
            progress.setValue(100)
            progress.close()
            del progress  # 确保对象被销毁
            QApplication.processEvents()
            
            # 检查是否是验证错误
            if 'valid' in result and not result['valid']:
                QMessageBox.critical(
                    self,
                    "格式错误",
                    f"CSV文件格式无效: {result['message']}"
                )
                return
            
            # 获取导入的新单词数和更新单词数
            new_count = result.get('new', 0)
            updated_count = result.get('updated', 0)
            skipped_count = result.get('skipped', 0)
            
            # 构建详细的结果消息
            details = f"导入结果:\n\n"
            details += f"✅ 新增: {new_count} 个单词\n"
            details += f"🔄 更新: {updated_count} 个单词\n"
            details += f"⏭️ 跳过: {skipped_count} 个单词\n\n"
            
            # 添加更新和跳过的单词列表（如果数量不太多）
            updated_words = result.get('updated_words', [])
            skipped_words = result.get('skipped_words', [])
            
            if updated_words and len(updated_words) <= 10:
                details += "更新的单词:\n"
                for word in updated_words:
                    details += f"- {word}\n"
                details += "\n"
            
            if skipped_words and len(skipped_words) <= 10:
                details += "跳过的单词:\n"
                for word in skipped_words:
                    details += f"- {word}\n"
            
            if new_count > 0 or updated_count > 0:
                # 导入成功
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("导入成功")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText(f"成功导入词汇！共新增 {new_count} 个单词，更新 {updated_count} 个单词。")
                msg_box.setDetailedText(details)
                msg_box.exec_()
                
                # 发送设置更新信号
                self.settings_updated.emit()
            else:
                # 未导入新单词
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("导入结果")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText("未导入新单词，可能是CSV格式错误或单词已存在。")
                msg_box.setDetailedText(details)
                msg_box.exec_()
            
        except pd.errors.EmptyDataError:
            if 'progress' in locals() and progress:
                progress.close()
                del progress
                QApplication.processEvents()
            QMessageBox.critical(self, "导入失败", "CSV文件为空或格式不正确")
        except pd.errors.ParserError:
            if 'progress' in locals() and progress:
                progress.close()
                del progress
                QApplication.processEvents()
            QMessageBox.critical(self, "导入失败", "CSV文件解析错误，请检查文件格式")
        except Exception as e:
            if 'progress' in locals() and progress:
                progress.close()
                del progress
                QApplication.processEvents()
            QMessageBox.critical(self, "导入失败", f"导入词汇失败: {e}")
            import traceback
            traceback.print_exc()
    
    def backup_data(self):
        """备份数据"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择备份目录",
            ""
        )
        
        if not folder_path:
            return
        
        try:
            # 备份数据库文件
            import shutil
            from datetime import datetime
            
            # 获取数据库文件路径
            db_path = self.vocab_manager.db.db_path
            config_path = self.config.config_path
            
            # 创建备份文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            db_backup_path = os.path.join(folder_path, f"vocabulary_{timestamp}.db")
            config_backup_path = os.path.join(folder_path, f"config_{timestamp}.json")
            
            # 复制文件
            shutil.copy2(db_path, db_backup_path)
            shutil.copy2(config_path, config_backup_path)
            
            QMessageBox.information(
                self,
                "备份成功",
                f"数据已成功备份到:\n{db_backup_path}\n{config_backup_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"备份数据失败: {e}")
    
    def restore_data(self):
        """恢复数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择备份数据库文件",
            "",
            "数据库文件 (*.db);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            reply = QMessageBox.warning(
                self,
                "恢复确认",
                "恢复数据将覆盖当前数据，是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 关闭数据库连接
                self.vocab_manager.db.close()
                
                # 恢复数据库文件
                import shutil
                
                # 获取数据库文件路径
                db_path = self.vocab_manager.db.db_path
                
                # 复制文件
                shutil.copy2(file_path, db_path)
                
                # 重新连接数据库
                self.vocab_manager.db.connect()
                
                QMessageBox.information(
                    self,
                    "恢复成功",
                    "数据已成功恢复，应用需要重启以加载恢复的数据"
                )
                
                # 发送设置更新信号
                self.settings_updated.emit()
                
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"恢复数据失败: {e}")
    
    def reset_data(self):
        """重置数据"""
        reply = QMessageBox.warning(
            self,
            "重置确认",
            "重置将清空所有学习记录和设置，此操作不可撤销！是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 二次确认
            confirm = QMessageBox.warning(
                self,
                "再次确认",
                "您确定要删除所有数据吗？此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                try:
                    # 关闭数据库连接
                    self.vocab_manager.db.close()
                    
                    # 删除数据库文件
                    os.remove(self.vocab_manager.db.db_path)
                    
                    # 删除配置文件
                    os.remove(self.config.config_path)
                    
                    # 重新初始化
                    self.vocab_manager.db.connect()
                    self.vocab_manager.db.create_tables()
                    self.config = Config()
                    
                    QMessageBox.information(
                        self,
                        "重置成功",
                        "所有数据已重置，应用将关闭"
                    )
                    
                    # 关闭设置窗口
                    self.close()
                    
                    # 发送设置更新信号
                    self.settings_updated.emit()
                    
                    # 此处应该重启应用，简化处理
                    
                except Exception as e:
                    QMessageBox.critical(self, "重置失败", f"重置数据失败: {e}")
    
    def set_default_values(self):
        """设置默认值"""
        # 学习设置默认值
        self.daily_words_spin.setValue(10)
        self.min_difficulty_spin.setValue(1)
        self.max_difficulty_spin.setValue(3)
        self.reminder_time_edit.setTime(QTime(8, 0))
        
        # 复习设置默认值
        self.auto_review_check.setChecked(True)
        self.review_remind_combo.setCurrentIndex(0)
        
        # 启动设置默认值
        self.auto_start_check.setChecked(False)
        self.start_minimized_check.setChecked(False)
        self.minimize_to_tray_check.setChecked(True)
        
        # 显示设置默认值
        self.opacity_slider.setValue(85)
        self.window_width_spin.setValue(350)
        self.window_height_spin.setValue(250)
        self.theme_combo.setCurrentIndex(0)
        self.font_size_spin.setValue(14)
    
    def reset_settings(self):
        """重置设置为默认值"""
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要将所有设置重置为默认值吗？\n这将丢失您当前的所有设置。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 设置界面控件为默认值
                self.set_default_values()
                
                # 使用默认配置的副本，避免修改原始默认配置
                default_config = self.config.default_config.copy()
                
                # 逐个更新各配置节，而不是整体替换
                for section, values in default_config.items():
                    self.config.set_section(section, values)
                
                # 保存配置
                success = self.config.save_config()
                
                if success:
                    QMessageBox.information(self, "成功", "设置已重置为默认值")
                else:
                    QMessageBox.warning(self, "警告", "重置设置时出现问题，但界面已更新为默认值")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置设置失败: {e}")
                import traceback
                traceback.print_exc() 