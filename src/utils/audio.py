import os
import tempfile
import threading
import pygame
from gtts import gTTS
from pathlib import Path


class AudioManager:
    """音频管理类，提供文本转语音和播放功能"""
    
    def __init__(self, cache_dir=None):
        """初始化音频管理器
        
        Args:
            cache_dir: 音频缓存目录，默认为None，将使用默认临时目录
        """
        # 初始化pygame音频系统
        pygame.mixer.init()
        
        # 设置缓存目录
        if cache_dir is None:
            # 使用应用数据目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.cache_dir = os.path.join(base_dir, 'data', 'audio_cache')
        else:
            self.cache_dir = cache_dir
            
        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # 线程锁，防止并发问题
        self.lock = threading.Lock()
        
        # 记录当前播放的音频
        self.current_sound = None
    
    def text_to_speech(self, text, lang='en', slow=False):
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            lang: 语言代码，默认为英语
            slow: 是否使用慢速朗读，默认为False
            
        Returns:
            audio_path: 生成的音频文件路径，失败则返回None
        """
        try:
            # 生成文件名，使用文本的MD5哈希作为文件名
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            audio_path = os.path.join(self.cache_dir, f"{text_hash}_{lang}.mp3")
            
            # 检查缓存是否存在
            if not os.path.exists(audio_path):
                with self.lock:  # 加锁，防止并发问题
                    # 再次检查，防止在等待锁的过程中有其他线程已经创建了文件
                    if not os.path.exists(audio_path):
                        # 使用gTTS生成语音
                        tts = gTTS(text=text, lang=lang, slow=slow)
                        tts.save(audio_path)
            
            return audio_path
        except Exception as e:
            print(f"文本转语音失败: {e}")
            return None
    
    def play_audio(self, audio_path, block=False):
        """播放音频文件
        
        Args:
            audio_path: 音频文件路径
            block: 是否阻塞等待播放完成，默认为False
            
        Returns:
            success: 操作是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audio_path):
                return False
            
            # 停止当前正在播放的音频
            self.stop_audio()
            
            # 播放新的音频
            with self.lock:
                self.current_sound = pygame.mixer.Sound(audio_path)
                self.current_sound.play()
            
            # 如果需要阻塞等待
            if block:
                # 获取音频长度并等待
                length = self.current_sound.get_length()
                pygame.time.wait(int(length * 1000))
            
            return True
        except Exception as e:
            print(f"播放音频失败: {e}")
            return False
    
    def stop_audio(self):
        """停止当前播放的音频"""
        with self.lock:
            if self.current_sound:
                self.current_sound.stop()
                self.current_sound = None
    
    def speak_text(self, text, lang='en', slow=False, block=False):
        """将文本转换为语音并播放
        
        Args:
            text: 要朗读的文本
            lang: 语言代码，默认为英语
            slow: 是否使用慢速朗读，默认为False
            block: 是否阻塞等待播放完成，默认为False
            
        Returns:
            success: 操作是否成功
        """
        # 将文本转换为语音
        audio_path = self.text_to_speech(text, lang, slow)
        
        if audio_path:
            # 播放语音
            return self.play_audio(audio_path, block)
        
        return False
    
    def clean_cache(self, max_age_days=30):
        """清理过期的缓存文件
        
        Args:
            max_age_days: 最大保留天数，默认为30天
            
        Returns:
            count: 清理的文件数量
        """
        try:
            import time
            
            count = 0
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for file_name in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, file_name)
                
                # 检查文件是否为常规文件
                if os.path.isfile(file_path):
                    # 获取文件修改时间
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    # 如果文件超过最大保留时间，则删除
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        count += 1
            
            return count
        except Exception as e:
            print(f"清理缓存失败: {e}")
            return 0
            
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        self.stop_audio()
        try:
            pygame.mixer.quit()
        except:
            pass 