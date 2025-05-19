import os
import sys
import time
import logging
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

def get_base_path():
    """获取应用基础路径
    
    Returns:
        Path: 应用基础路径
    """
    try:
        if getattr(sys, 'frozen', False):
            # 如果是打包后的环境
            base_path = Path(sys._MEIPASS)
            print(f"运行在打包环境中，基础路径: {base_path}")
        else:
            # 如果是开发环境
            base_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            print(f"运行在开发环境中，基础路径: {base_path}")
        
        # 验证路径是否存在
        if not base_path.exists():
            raise FileNotFoundError(f"基础路径不存在: {base_path}")
            
        return base_path
    except Exception as e:
        print(f"获取基础路径时出错: {e}")
        # 如果出错，使用当前目录作为后备方案
        return Path(os.getcwd())

# 设置基础路径
BASE_PATH = get_base_path()
if str(BASE_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_PATH))

# 添加调试信息
print(f"Python路径: {sys.path}")
print(f"当前工作目录: {os.getcwd()}")

# 确保src目录在Python路径中
src_path = BASE_PATH / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from src.ui.main_window import MainWindow
    from src.data.database import Database
    from src.data.config import Config
    from src.utils.helper import setup_logger, handle_exception, get_app_dir, get_assets_dir
    print("成功导入所有必要的模块")
except ImportError as e:
    print(f"导入模块时出错: {e}")
    print(f"尝试导入的模块路径: {sys.path}")
    raise


def parse_arguments():
    """解析命令行参数
    
    Returns:
        args: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='每日单词 - 英语学习工具')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', help='指定配置文件路径')
    parser.add_argument('--db', help='指定数据库文件路径')
    
    return parser.parse_args()


def setup_environment():
    """设置应用环境
    
    Returns:
        dict: 包含环境设置的字典
    """
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # 设置日志
    logger = setup_logger('app', log_level)
    logger.info("应用启动中...")
    
    # 设置全局异常处理
    sys.excepthook = handle_exception
    
    # 创建环境设置字典
    env = {
        'logger': logger,
        'debug': args.debug,
        'config_path': args.config,
        'db_path': args.db
    }
    
    return env


def initialize_database(db_path=None):
    """初始化数据库
    
    Args:
        db_path: 数据库文件路径，默认为None
        
    Returns:
        db: 数据库连接实例
    """
    # 创建数据库实例
    db = Database(db_path)
    
    # 连接数据库
    db.connect()
    
    # 创建数据表
    db.create_tables()
    
    # 检查是否需要导入基础词汇
    db.cursor.execute("SELECT COUNT(*) as count FROM vocabulary")
    result = db.cursor.fetchone()
    
    if result['count'] == 0:
        # 词汇库为空，导入基础词汇
        from src.utils.helper import get_data_dir
        csv_path = get_data_dir() / 'basic_vocabulary.csv'
        
        if csv_path.exists():
            db.import_vocabulary_from_csv(str(csv_path))
            logger = setup_logger('app')
            logger.info(f"已导入基础词汇库: {csv_path}")
    
    return db


def check_first_run():
    """检查是否首次运行应用
    
    Returns:
        is_first_run: 是否首次运行
    """
    config = Config()
    
    # 获取首次运行标记
    first_run = config.get('app', 'first_run')
    
    if first_run is None:
        # 设置为非首次运行
        config.set('app', 'first_run', 'false')
        config.set('app', 'install_time', str(int(time.time())))
        return True
    
    return False


def main():
    """应用主函数"""
    # 设置环境
    env = setup_environment()
    logger = env['logger']
    
    try:
        # 创建QApplication实例
        app = QApplication(sys.argv)
        app.setApplicationName("每日单词")
        app.setApplicationDisplayName("每日单词 - 英语学习工具")
        
        # 设置应用图标
        icon_path = get_assets_dir() / 'logo.png'
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # 初始化数据库
        db = initialize_database(env.get('db_path'))
        
        # 创建并显示主窗口
        main_window = MainWindow()
        main_window.show()
        
        # 检查是否首次运行
        if check_first_run():
            # 显示欢迎对话框或引导教程
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                main_window,
                "欢迎使用每日单词",
                "感谢您选择使用每日单词学习工具！\n\n"
                "这是一款帮助您有效学习英语词汇的应用。\n"
                "每天坚持学习，您将看到显著的进步。\n\n"
                "祝您学习愉快！"
            )
        
        # 运行应用
        logger.info("应用启动完成")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("应用已退出")


if __name__ == "__main__":
    main() 