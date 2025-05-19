import os
import sys
import shutil
import subprocess
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = ROOT_DIR / 'src'
DATA_DIR = ROOT_DIR / 'data'
ASSETS_DIR = ROOT_DIR / 'assets'
DIST_DIR = ROOT_DIR / 'dist'
BUILD_DIR = ROOT_DIR / 'build'


def clean_build_directories():
    """清理构建目录"""
    print("清理构建目录...")
    
    # 删除dist和build目录
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    # 删除__pycache__目录
    for pycache_dir in ROOT_DIR.glob('**/__pycache__'):
        shutil.rmtree(pycache_dir)
    
    print("清理完成")


def create_assets_directory():
    """创建和准备资源目录"""
    print("准备资源目录...")
    
    # 创建资源目录
    if not ASSETS_DIR.exists():
        ASSETS_DIR.mkdir(parents=True)
    
    # 可以在这里添加创建默认资源的代码
    # 例如，如果没有logo.png，可以创建一个默认的logo
    logo_path = ASSETS_DIR / 'logo.png'
    if not logo_path.exists():
        print("未找到应用图标，请在构建前添加 assets/logo.png 文件")
    
    print("资源目录准备完成")


def build_application():
    """使用PyInstaller构建应用"""
    print("开始构建应用...")
    
    # 确保在正确的目录中运行
    os.chdir(ROOT_DIR)
    print(f"当前工作目录: {os.getcwd()}")
    
    # PyInstaller命令参数
    pyinstaller_args = [
        'pyinstaller',
        '--clean',  # 清理临时文件
        '--noconfirm',  # 不询问确认
        
        'english_tool.spec'  # 使用spec文件
    ]
    
    # 执行PyInstaller命令
    try:
        subprocess.run(pyinstaller_args, check=True)
        print("应用构建成功")
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False
    
    return True


def optimize_dist_size():
    """优化输出目录大小"""
    print("优化输出大小...")
    
    # 可以在这里添加删除不必要的文件的代码
    # 例如，删除某些大型库的不需要的组件
    
    # 示例：删除测试目录
    for test_dir in DIST_DIR.glob('**/test'):
        if test_dir.is_dir():
            shutil.rmtree(test_dir)
    
    print("优化完成")


def main():
    """主函数"""
    print("="*50)
    print("每日单词 - 应用打包脚本")
    print("="*50)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 未找到PyInstaller，请先安装: pip install pyinstaller")
        return
    
    # 清理构建目录
    clean_build_directories()
    
    # 创建和准备资源目录
    create_assets_directory()
    
    # 构建应用
    if build_application():
        # 优化输出大小
        optimize_dist_size()
        
        # 输出成功信息
        print("\n打包完成！")
        print(f"应用程序位于: {DIST_DIR / '每日单词'}")
        print("\n运行应用: dist/每日单词/每日单词.exe")
    else:
        print("\n打包失败，请检查错误信息")


if __name__ == "__main__":
    main() 