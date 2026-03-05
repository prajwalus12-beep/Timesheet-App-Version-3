"""
Image-based CAPTCHA generator using Pillow.
Renders the code as distorted text on a noisy background.
"""
import io
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def generate_captcha_image(code: str) -> io.BytesIO:
    """Generate a CAPTCHA image for the given code and return as PNG BytesIO."""
    width, height = 220, 80

    # --- Background ---
    bg_color = (
        random.randint(220, 245),
        random.randint(220, 245),
        random.randint(220, 245),
    )
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # --- Use a built-in font at a reasonable size ---
    try:
        font = ImageFont.truetype("arial.ttf", 38)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
        except OSError:
            font = ImageFont.load_default()

    # --- Draw each character with slight rotation & jitter ---
    char_width = width // (len(code) + 1)
    for i, ch in enumerate(code):
        # Create a small transparent image for the character
        ch_img = Image.new("RGBA", (50, 60), (255, 255, 255, 0))
        ch_draw = ImageDraw.Draw(ch_img)

        # Random color per character (dark shades for readability)
        color = (
            random.randint(10, 140),
            random.randint(10, 140),
            random.randint(10, 140),
        )
        ch_draw.text((5, 5), ch, font=font, fill=color)

        # Rotate slightly
        angle = random.randint(-25, 25)
        ch_img = ch_img.rotate(angle, resample=Image.BICUBIC, expand=True)

        # Paste onto main image
        x = 10 + i * char_width + random.randint(-3, 3)
        y = random.randint(2, 15)
        img.paste(ch_img, (x, y), ch_img)

    # --- Noise: random lines ---
    for _ in range(random.randint(4, 7)):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        line_color = (
            random.randint(80, 200),
            random.randint(80, 200),
            random.randint(80, 200),
        )
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=random.randint(1, 2))

    # --- Noise: random arcs ---
    for _ in range(random.randint(2, 4)):
        x1 = random.randint(0, width // 2)
        y1 = random.randint(0, height // 2)
        x2 = x1 + random.randint(40, 120)
        y2 = y1 + random.randint(20, 60)
        arc_color = (
            random.randint(80, 180),
            random.randint(80, 180),
            random.randint(80, 180),
        )
        draw.arc(
            [(x1, y1), (x2, y2)],
            start=random.randint(0, 180),
            end=random.randint(180, 360),
            fill=arc_color,
            width=2,
        )

    # --- Noise: random dots ---
    for _ in range(random.randint(60, 120)):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        dot_color = (
            random.randint(60, 200),
            random.randint(60, 200),
            random.randint(60, 200),
        )
        draw.point((x, y), fill=dot_color)

    # --- Slight blur for anti-aliasing ---
    img = img.filter(ImageFilter.SMOOTH)

    # --- Save to buffer ---
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
