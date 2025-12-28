#!/usr/bin/env python3
"""
Create AgTools application icon.

Generates a professional, sharp agriculture-themed icon for the desktop application.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_agtools_icon():
    """Create a multi-size ICO file for AgTools with sharp graphics."""

    # Icon sizes needed for Windows
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        # Create base image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Colors - agriculture theme
        bg_green = (46, 125, 50)       # Material Green 700
        light_green = (76, 175, 80)    # Material Green 500
        dark_green = (27, 94, 32)      # Material Green 900
        gold = (255, 193, 7)           # Amber/wheat color
        dark_gold = (255, 160, 0)      # Darker gold

        # Calculate dimensions
        center_x = size // 2
        center_y = size // 2
        margin = max(1, size // 16)

        # Draw circular background with gradient effect
        # Outer ring (dark)
        draw.ellipse([margin, margin, size - margin - 1, size - margin - 1],
                     fill=dark_green)

        # Inner circle (main green)
        inner_margin = margin + max(1, size // 20)
        draw.ellipse([inner_margin, inner_margin,
                     size - inner_margin - 1, size - inner_margin - 1],
                     fill=bg_green)

        # Draw wheat/crop stalks
        if size >= 24:
            # Scale factors
            scale = size / 256

            # Stalk parameters
            stalk_width = max(2, int(8 * scale))
            grain_size = max(2, int(16 * scale))

            # Base Y position (bottom of stalks)
            base_y = int(size * 0.85)
            top_y = int(size * 0.18)

            # Center stalk
            cx = center_x
            draw.line([(cx, base_y), (cx, top_y + grain_size * 2)],
                     fill=gold, width=stalk_width)

            # Left stalk
            lx = int(center_x - size * 0.22)
            draw.line([(lx, base_y), (int(lx + size * 0.08), top_y + grain_size * 3)],
                     fill=gold, width=stalk_width)

            # Right stalk
            rx = int(center_x + size * 0.22)
            draw.line([(rx, base_y), (int(rx - size * 0.08), top_y + grain_size * 3)],
                     fill=gold, width=stalk_width)

            # Draw grain heads (ellipses for wheat look)
            # Center grain head
            for i in range(3):
                offset = i * grain_size * 0.8
                gy = top_y + offset
                gx = cx
                draw.ellipse([gx - grain_size//2, gy - grain_size//4,
                             gx + grain_size//2, gy + grain_size//4],
                            fill=dark_gold)

            # Left grain head
            for i in range(3):
                offset = i * grain_size * 0.8
                gy = top_y + grain_size + offset
                gx = int(lx + size * 0.08)
                draw.ellipse([gx - grain_size//2, gy - grain_size//4,
                             gx + grain_size//2, gy + grain_size//4],
                            fill=dark_gold)

            # Right grain head
            for i in range(3):
                offset = i * grain_size * 0.8
                gy = top_y + grain_size + offset
                gx = int(rx - size * 0.08)
                draw.ellipse([gx - grain_size//2, gy - grain_size//4,
                             gx + grain_size//2, gy + grain_size//4],
                            fill=dark_gold)

            # Add small leaves on stalks for detail (larger sizes only)
            if size >= 64:
                leaf_len = int(size * 0.12)
                leaf_y = int(size * 0.55)

                # Left leaf on center stalk
                draw.line([(cx, leaf_y), (cx - leaf_len, leaf_y - leaf_len//2)],
                         fill=light_green, width=max(1, stalk_width//2))

                # Right leaf on center stalk
                leaf_y2 = int(size * 0.65)
                draw.line([(cx, leaf_y2), (cx + leaf_len, leaf_y2 - leaf_len//2)],
                         fill=light_green, width=max(1, stalk_width//2))

        else:
            # For very small sizes, draw simple wheat symbol
            draw.line([(center_x, int(size * 0.75)), (center_x, int(size * 0.25))],
                     fill=gold, width=max(1, size // 8))
            # Simple grain at top
            draw.ellipse([center_x - size//6, int(size * 0.2),
                         center_x + size//6, int(size * 0.35)],
                        fill=dark_gold)

        images.append(img)

    # Get the script directory, go up one level to agtools root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    # Save as ICO file with all sizes
    icon_path = os.path.join(root_dir, 'agtools.ico')

    # Save the largest image first, then append others
    # ICO format: save with explicit sizes
    images[-1].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes]
    )

    print(f"Icon created: {icon_path}")

    # Also save a PNG version for other uses
    png_path = os.path.join(root_dir, 'agtools_icon.png')
    images[-1].save(png_path, format='PNG')
    print(f"PNG created: {png_path}")

    return icon_path


if __name__ == "__main__":
    create_agtools_icon()
