#!/usr/bin/env python3
"""
PWA 图标生成器

生成不同尺寸的 PWA 图标
尺寸: 16x16, 32x32, 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import List


class IconGenerator:
    """图标生成器"""

    # PWA 图标尺寸
    ICON_SIZES = [
        16, 32, 72, 96, 128, 144, 152, 192, 384, 512
    ]

    # 图标颜色
    PRIMARY_COLOR = (102, 126, 234)  # #667eea
    SECONDARY_COLOR = (118, 75, 162)  # #764ba2
    WHITE = (255, 255, 255)

    def __init__(self, output_dir: str):
        """
        初始化图标生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_gradient_background(
        self,
        size: int
    ) -> Image.Image:
        """
        创建渐变背景

        Args:
            size: 图标尺寸

        Returns:
            PIL Image 对象
        """
        img = Image.new('RGB', (size, size), self.PRIMARY_COLOR)
        draw = ImageDraw.Draw(img)

        # 创建从左上到右下的渐变
        for y in range(size):
            for x in range(size):
                # 计算渐变比例 (0-1)
                ratio = (x + y) / (2 * size)

                # 插值颜色
                r = int(self.PRIMARY_COLOR[0] * (1 - ratio) + self.SECONDARY_COLOR[0] * ratio)
                g = int(self.PRIMARY_COLOR[1] * (1 - ratio) + self.SECONDARY_COLOR[1] * ratio)
                b = int(self.PRIMARY_COLOR[2] * (1 - ratio) + self.SECONDARY_COLOR[2] * ratio)

                draw.point((x, y), (r, g, b))

        return img

    def draw_text_centered(
        self,
        img: Image.Image,
        text: str,
        font_size: int
    ) -> None:
        """
        在图像中心绘制文字

        Args:
            img: PIL Image 对象
            text: 要绘制的文字
            font_size: 字体大小
        """
        draw = ImageDraw.Draw(img)

        # 尝试加载字体
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                font_size
            )
        except:
            # 如果系统字体不可用，使用默认字体
            font = ImageFont.load_default()

        # 获取文字边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算居中位置
        x = (img.width - text_width) // 2
        y = (img.height - text_height) // 2

        # 绘制文字
        draw.text((x, y), text, fill=self.WHITE, font=font)

    def draw_bridge_icon(self, img: Image.Image, size: int) -> None:
        """
        绘制桥图标

        Args:
            img: PIL Image 对象
            size: 图标尺寸
        """
        draw = ImageDraw.Draw(img)

        # 计算边距和线条粗细
        margin = size // 6
        line_width = max(2, size // 20)

        # 桥的两个支柱
        pillar_width = max(4, size // 10)
        pillar_height = size - 2 * margin

        # 左支柱
        left_pillar_x = margin
        draw.rectangle(
            [left_pillar_x, margin, left_pillar_x + pillar_width, margin + pillar_height],
            fill=self.WHITE,
            outline=self.WHITE
        )

        # 右支柱
        right_pillar_x = size - margin - pillar_width
        draw.rectangle(
            [right_pillar_x, margin, right_pillar_x + pillar_width, margin + pillar_height],
            fill=self.WHITE,
            outline=self.WHITE
        )

        # 桥面（拱形）
        arch_height = pillar_height // 3
        arch_top_y = margin + (pillar_height - arch_height) // 2

        # 绘制拱形桥面
        arch_bottom_y = arch_top_y + arch_height
        draw.arc(
            [left_pillar_x, arch_top_y - line_width, right_pillar_x + pillar_width, arch_bottom_y + line_width],
            start=180,
            end=0,
            fill=self.WHITE,
            width=line_width
        )

        # 添加 "Z" 字母
        font_size = size // 3
        self.draw_text_centered(img, "Z", font_size)

    def generate_icon(self, size: int) -> Path:
        """
        生成指定尺寸的图标

        Args:
            size: 图标尺寸

        Returns:
            生成的图标文件路径
        """
        # 创建渐变背景
        img = self.create_gradient_background(size)

        # 绘制桥图标
        self.draw_bridge_icon(img, size)

        # 保存文件
        filename = f"icon-{size}x{size}.png"
        filepath = self.output_dir / filename

        img.save(filepath, 'PNG', optimize=True)

        return filepath

    def generate_all_icons(self) -> List[Path]:
        """
        生成所有尺寸的图标

        Returns:
            生成的图标文件路径列表
        """
        generated_files = []

        print("=" * 60)
        print("PWA 图标生成器")
        print("=" * 60)
        print()

        for size in self.ICON_SIZES:
            print(f"生成 {size}x{size} 图标...", end=" ")
            filepath = self.generate_icon(size)
            generated_files.append(filepath)
            print("✅ 完成")

        print()
        print("=" * 60)
        print(f"✅ 成功生成 {len(generated_files)} 个图标")
        print(f"📁 输出目录: {self.output_dir}")
        print("=" * 60)

        return generated_files

    def generate_manifest(self) -> None:
        """
        生成或更新 manifest.json 文件
        """
        manifest_path = self.output_dir.parent / "manifest.json"

        manifest_content = '''{
  "name": "智桥 - AI工具连接器",
  "short_name": "智桥",
  "description": "跨平台实时同步和通信SDK，连接多个AI编程工具",
  "start_url": "/web/ui/index.html",
  "display": "standalone",
  "orientation": "portrait-primary",
  "background_color": "#667eea",
  "theme_color": "#667eea",
  "scope": "/",
  "icons": [
'''

        icon_entries = []
        for size in self.ICON_SIZES:
            icon_entries.append(f'''    {{
      "src": "/web/ui/icons/icon-{size}x{size}.png",
      "sizes": "{size}x{size}",
      "type": "image/png",
      "purpose": "any maskable"
    }}''')

        manifest_content += ',\n'.join(icon_entries)
        manifest_content += '''
  ]
}
'''

        with open(manifest_path, 'w') as f:
            f.write(manifest_content)

        print("✅ manifest.json 已更新")


def main():
    """主函数"""
    # 输出目录
    output_dir = '/home/ai/zhineng-bridge/web/ui/icons'

    # 创建生成器
    generator = IconGenerator(output_dir)

    # 生成所有图标
    generator.generate_all_icons()

    # 更新 manifest.json
    generator.generate_manifest()

    print()
    print("=" * 60)
    print("📝 配置说明")
    print("=" * 60)
    print()
    print("✅ 所有图标已生成并保存到:")
    print(f"   {output_dir}")
    print()
    print("✅ manifest.json 已更新")
    print()
    print("📋 生成的图标尺寸:")
    for size in IconGenerator.ICON_SIZES:
        print(f"   - {size}x{size} → icon-{size}x{size}.png")
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
