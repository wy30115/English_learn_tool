import os
import json
from pathlib import Path


class Config:
    """配置管理类，负责读写应用配置"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 获取应用根目录
        self.app_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.data_dir = self.app_dir / 'data'
        
        # 确保目录存在
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
        
        # 配置文件路径
        self.config_path = self.data_dir / 'config.json'
        
        # 默认配置
        self.default_config = {
            "window": {
                "position": [100, 100],
                "size": [300, 200],
                "opacity": 0.85
            },
            "study": {
                "daily_words": 10,
                "difficulty_range": [1, 3],
                "reminder_time": "08:00"
            },
            "display": {
                "font_size": 14,
                "theme": "light"
            },
            "startup": {
                "auto_start": False,
                "start_minimized": False,
                "first_launch": True
            }
        }
        
        # 初始化配置
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件
        
        如果配置文件不存在或有错误，则使用默认配置
        
        Returns:
            config: 配置字典
        """
        if not self.config_path.exists():
            # 配置文件不存在，创建默认配置
            return self.create_default_config()
        
        try:
            # 读取配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查配置是否完整，如果有缺失项，使用默认值补充
            return self.merge_with_default(config)
                
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            # 配置文件有错误，使用默认配置
            return self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件
        
        Returns:
            config: 默认配置字典
        """
        try:
            # 先创建一个副本，避免修改原始默认配置
            default_config = self.default_config.copy()
            
            # 尝试写入配置文件
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
            except Exception as write_error:
                print(f"写入默认配置文件时出错: {write_error}")
                # 即使写入失败，仍然返回默认配置
            
            return default_config
        except Exception as e:
            print(f"创建默认配置文件时出错: {e}")
            # 确保至少返回一个有效的字典，避免程序崩溃
            return {
                "window": {"position": [100, 100], "size": [300, 200], "opacity": 0.85},
                "study": {"daily_words": 10, "difficulty_range": [1, 3], "reminder_time": "08:00"},
                "display": {"font_size": 14, "theme": "light"},
                "startup": {"auto_start": False, "start_minimized": False, "first_launch": True}
            }
    
    def merge_with_default(self, config):
        """将用户配置与默认配置合并，确保所有配置项都存在
        
        Args:
            config: 用户配置字典
            
        Returns:
            merged_config: 合并后的配置字典
        """
        merged = self.default_config.copy()
        
        # 递归合并字典
        def merge_dict(target, source):
            for key, value in source.items():
                if key in target:
                    if isinstance(value, dict) and isinstance(target[key], dict):
                        # 递归合并子字典
                        merge_dict(target[key], value)
                    else:
                        # 使用用户配置覆盖默认配置
                        target[key] = value
        
        merge_dict(merged, config)
        return merged
    
    def save_config(self):
        """保存配置到文件
        
        Returns:
            success: 操作是否成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件时出错: {e}")
            return False
    
    def get(self, section, key=None):
        """获取配置项
        
        Args:
            section: 配置节名称
            key: 配置项名称，如果为None则返回整个节
            
        Returns:
            value: 配置值，如果配置项不存在则返回None
        """
        # 检查section是否在配置中
        if section not in self.config:
            # 如果key是一个字典，那么它可能是作为默认值传递的
            if isinstance(key, dict):
                return key
            return {} if key is None else None
        
        if key is None:
            return self.config[section]
        
        # 确保section是字典类型
        if isinstance(self.config[section], dict):
            return self.config[section].get(key, None)
        else:
            return None
    
    def set(self, section, key, value):
        """设置配置项
        
        Args:
            section: 配置节名称
            key: 配置项名称
            value: 配置项值
            
        Returns:
            success: 操作是否成功
        """
        try:
            # 确保节存在
            if section not in self.config:
                self.config[section] = {}
            
            # 设置配置项
            self.config[section][key] = value
            
            # 保存配置
            return self.save_config()
            
        except Exception as e:
            print(f"设置配置项时出错: {e}")
            return False
    
    def set_section(self, section, values):
        """设置整个配置节
        
        Args:
            section: 配置节名称
            values: 配置节内容
            
        Returns:
            success: 操作是否成功
        """
        try:
            # 设置配置节
            self.config[section] = values
            
            # 保存配置
            return self.save_config()
            
        except Exception as e:
            print(f"设置配置节时出错: {e}")
            return False 