from PIL import Image, ImageDraw, ImageFont
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取logo保存路径
logo_path = os.path.join(current_dir, 'logo.png')

# 创建一个正方形图像
img_size = 256
img = Image.new('RGBA', (img_size, img_size), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# 定义颜色
bg_color = (52, 152, 219)  # 蓝色背景
text_color = (255, 255, 255)  # 白色文本

# 绘制圆形背景
draw.ellipse([(0, 0), (img_size, img_size)], fill=bg_color)

# 尝试加载字体，如果找不到则使用默认字体
try:
    font = ImageFont.truetype("arial.ttf", 120)
except IOError:
    font = ImageFont.load_default()

# 绘制文本 "ET"（English Tool的缩写）
draw.text((img_size/2, img_size/2), "ET", font=font, fill=text_color, anchor="mm")

# 保存图像
img.save(logo_path)

print(f"Logo已生成：{logo_path}") 