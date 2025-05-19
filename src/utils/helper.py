import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path


def get_app_dir():
    """获取应用根目录
    
    Returns:
        app_dir: 应用根目录路径
    """
    # 如果是打包后的应用，使用特定方法获取路径
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的应用
        app_dir = Path(os.path.dirname(sys.executable))
    else:
        # 开发环境
        app_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    return app_dir


def get_data_dir():
    """获取数据目录
    
    如果目录不存在则创建它
    
    Returns:
        data_dir: 数据目录路径
    """
    data_dir = get_app_dir() / 'data'
    
    # 确保目录存在
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
    
    return data_dir


def get_assets_dir():
    """获取资源目录
    
    Returns:
        assets_dir: 资源目录路径
    """
    assets_dir = get_app_dir() / 'assets'
    return assets_dir


def get_logs_dir():
    """获取日志目录
    
    如果目录不存在则创建它
    
    Returns:
        logs_dir: 日志目录路径
    """
    logs_dir = get_data_dir() / 'logs'
    
    # 确保目录存在
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)
    
    return logs_dir


def setup_logger(name=None, log_level=logging.INFO):
    """配置日志记录器
    
    Args:
        name: 日志名称，默认为None，使用根日志记录器
        log_level: 日志级别，默认为INFO
        
    Returns:
        logger: 配置好的日志记录器
    """
    # 获取日志目录
    logs_dir = get_logs_dir()
    
    # 创建日志文件路径，使用当前日期作为文件名
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # 获取日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复配置处理器
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器
    
    Args:
        exc_type: 异常类型
        exc_value: 异常值
        exc_traceback: 异常堆栈
    """
    # 忽略键盘中断异常
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 获取日志记录器
    logger = setup_logger('error')
    
    # 记录异常信息
    logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))


def safe_execute(func, *args, **kwargs):
    """安全执行函数，捕获并记录异常
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        result: 函数执行结果，如果发生异常则返回None
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = setup_logger('error')
        logger.error(f"执行函数 {func.__name__} 时出错: {e}")
        logger.error(traceback.format_exc())
        return None


def format_time(seconds):
    """格式化时间
    
    Args:
        seconds: 秒数
        
    Returns:
        formatted_time: 格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def capitalize_first(text):
    """首字母大写
    
    Args:
        text: 输入文本
        
    Returns:
        capitalized: 首字母大写的文本
    """
    if not text:
        return ""
    return text[0].upper() + text[1:]


def word_counter(text):
    """计算文本中的单词数
    
    Args:
        text: 输入文本
        
    Returns:
        count: 单词数量
    """
    if not text:
        return 0
    
    # 分割文本并过滤空字符串
    words = [word for word in text.split() if word]
    return len(words)


def text_ellipsis(text, max_length=50):
    """文本截断，超过最大长度则添加省略号
    
    Args:
        text: 输入文本
        max_length: 最大长度，默认为50
        
    Returns:
        result: 处理后的文本
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def ensure_file_exists(file_path, default_content=""):
    """确保文件存在，如果不存在则创建
    
    Args:
        file_path: 文件路径
        default_content: 默认内容，默认为空字符串
        
    Returns:
        exists: 文件是否已经存在
    """
    path = Path(file_path)
    
    # 确保父目录存在
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    
    # 检查文件是否存在
    if path.exists():
        return True
    
    # 创建文件
    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_content)
    
    return False 