import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "rocky")
WATCHFACE_DIR = os.path.join(BASE_DIR, "watchface")
ARTIFACT_DIR = os.environ.get("PREVIEW_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
os.makedirs(ARTIFACT_DIR, exist_ok=True)

COLORS = [
    ("mint",   "Mint",   (46, 255, 166),  (32, 180, 118),  0x2EFFA6, 0x20B476),
    ("blue",   "Blue",   (24, 144, 255),  (20, 105, 190),  0x1890FF, 0x1469BE),
    ("orange", "Orange", (255, 126, 24),  (185, 90, 18),   0xFF7E18, 0xB95A12),
    ("cyan",   "Cyan",   (0, 229, 255),   (0, 160, 180),   0x00E5FF, 0x00A0B4),
    ("gold",   "Gold",   (245, 190, 63),  (175, 135, 44),  0xF5BE3F, 0xAF872C),
    ("red",    "Red",    (255, 77, 90),   (185, 55, 65),   0xFF4D5A, 0xB93741),
    ("violet", "Violet", (184, 138, 247), (132, 98, 178),  0xB88AF7, 0x8462B2),
    ("white",  "White",  (255, 255, 255), (175, 175, 175), 0xFFFFFF, 0xAFAFAF),
]

HEART_RGB = (255, 67, 90)
HEART_HEX = 0xFF435A

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_ARIAL_BLACK = r"C:\Windows\Fonts\ariblk.ttf"
FONT_ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_bahn(size, weight=700, width=100):
    font = ImageFont.truetype(FONT_BAHN, size)
    try:
        font.set_variation_by_axes([weight, width])
    except Exception:
        pass
    return font


def render_style_a_glyph(ch, color_rgba, target_h=108):
    """Render bold, wide athletic-tactical digits matching Style A mockup (c4d6fc56.jpg):
    - Digits 0,2..9 are ~82px wide x 108px tall with thick blocky strokes
    - Digit '1' has the top nose + bottom horizontal base bar (~60px wide)
    - Colon ':' is two bold rounded square dots (18px wide)
    """
    scale = 4
    H = target_h * scale
    if ch == ":":
        W = 18 * scale
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        dot_s = 16 * scale
        x0 = (W - dot_s) // 2
        # Upper and lower square dots with rounded corners
        d.rounded_rectangle([x0, int(H * 0.22), x0 + dot_s, int(H * 0.22) + dot_s], radius=3 * scale, fill=color_rgba)
        d.rounded_rectangle([x0, int(H * 0.63), x0 + dot_s, int(H * 0.63) + dot_s], radius=3 * scale, fill=color_rgba)
        return im.resize((18, target_h), Image.Resampling.LANCZOS)

    if ch == "1":
        W = 62 * scale
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        stem_w = 22 * scale
        stem_x0 = (W - stem_w) // 2 + 2 * scale
        stem_x1 = stem_x0 + stem_w
        base_h = 18 * scale
        # Vertical stem
        d.rounded_rectangle([stem_x0, 0, stem_x1, H - base_h // 2], radius=2 * scale, fill=color_rgba)
        # Top-left angled/stepped nose
        nose_pts = [
            (stem_x0 - 18 * scale, int(H * 0.14)),
            (stem_x0 + 4 * scale, 0),
            (stem_x1, 0),
            (stem_x1, int(H * 0.27)),
            (stem_x0 - 18 * scale, int(H * 0.27)),
        ]
        d.polygon(nose_pts, fill=color_rgba)
        # Bottom horizontal base bar
        d.rounded_rectangle([2 * scale, H - base_h, W - 2 * scale, H], radius=2 * scale, fill=color_rgba)
        return im.resize((62, target_h), Image.Resampling.LANCZOS)

    # For 0, 2..9: geometric rounded-block athletic digits matching c4d6fc56.jpg (82 x 108)
    W = 82 * scale
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    T = int(21.5 * scale)
    R = int(22 * scale)
    r_in = int(7 * scale)
    mid_y0 = (H - int(19 * scale)) // 2
    mid_y1 = mid_y0 + int(19 * scale)

    def clear_rect(x0, y0, x1, y1, rad=0):
        if rad > 0:
            d.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=(0, 0, 0, 0))
        else:
            d.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 0))

    if ch == "0":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(T, T, W - 1 - T, H - 1 - T, r_in)
    elif ch == "8":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(T, T, W - 1 - T, mid_y0, r_in)
        clear_rect(T, mid_y1, W - 1 - T, H - 1 - T, r_in)
    elif ch == "9":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(T, T, W - 1 - T, mid_y0, r_in)
        clear_rect(0, mid_y1, W - 1 - T, H - 1 - T, 0)
    elif ch == "6":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(T, T, W, mid_y0, 0)
        clear_rect(T, mid_y1, W - 1 - T, H - 1 - T, r_in)
    elif ch == "5":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(T, T, W, mid_y0, 0)
        clear_rect(0, mid_y1, W - 1 - T, H - 1 - T, 0)
    elif ch == "2":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(0, T, W - 1 - T, mid_y0, 0)
        clear_rect(T, mid_y1, W, H - 1 - T, 0)
    elif ch == "3":
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=color_rgba)
        clear_rect(0, T, W - 1 - T, mid_y0, 0)
        clear_rect(0, mid_y1, W - 1 - T, H - 1 - T, 0)
    elif ch == "4":
        d.rounded_rectangle([0, 0, T, mid_y1], radius=int(4 * scale), fill=color_rgba)
        d.rounded_rectangle([0, mid_y0, W - 1, mid_y1], radius=int(4 * scale), fill=color_rgba)
        d.rounded_rectangle([W - 1 - T, 0, W - 1, H - 1], radius=int(4 * scale), fill=color_rgba)
    elif ch == "7":
        d.rounded_rectangle([0, 0, W - 1, T], radius=int(4 * scale), fill=color_rgba)
        pts = [(W - 1 - T, T // 2), (W - 1, T // 2), (int(W * 0.52), H - 1), (int(W * 0.52) - T, H - 1)]
        d.polygon(pts, fill=color_rgba)

    return im.resize((82, target_h), Image.Resampling.LANCZOS)


def render_style_b_glyph(ch, color_rgba, target_h=112):
    """Render ultra-bold modern wide rounded-sans digits matching Style B mockup (a337207a.jpg)."""
    scale = 4
    H = target_h * scale
    if ch == ":":
        W = 18 * scale
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        dot_s = 16 * scale
        x0 = (W - dot_s) // 2
        d.rounded_rectangle([x0, int(H * 0.22), x0 + dot_s, int(H * 0.22) + dot_s], radius=2 * scale, fill=color_rgba)
        d.rounded_rectangle([x0, int(H * 0.63), x0 + dot_s, int(H * 0.63) + dot_s], radius=2 * scale, fill=color_rgba)
        return im.resize((18, target_h), Image.Resampling.LANCZOS)

    canvas_w, canvas_h = 680, 680
    font_path = FONT_ARIAL_BLACK if os.path.exists(FONT_ARIAL_BLACK) else FONT_ARIAL_BOLD
    font = ImageFont.truetype(font_path, int(target_h * scale * 1.22))
    im = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((120, 80), ch, font=font, fill=color_rgba, stroke_width=int(1.2 * scale), stroke_fill=color_rgba)

    ref = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    ImageDraw.Draw(ref).text((120, 80), "0", font=font, fill=color_rgba, stroke_width=int(1.2 * scale), stroke_fill=color_rgba)
    rb = ref.getbbox()
    bb = im.getbbox()
    top = min(rb[1], bb[1])
    bottom = max(rb[3], bb[3])
    cropped = im.crop((bb[0], top, bb[2], bottom))
    raw_ratio = cropped.width / max(1, rb[2] - rb[0])
    target_w = 54 if ch == "1" else max(72, round(86 * raw_ratio))
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def generate_clock_sets():
    metrics = {"a": {}, "b": {}, "aod": {}}
    glyphs = [(str(d), str(d)) for d in range(10)] + [(":", "colon")]
    color_entries = [("white", (255, 255, 255), (175, 175, 175))] + [
        (key, rgb, aod_rgb) for key, _, rgb, aod_rgb, _, _ in COLORS if key != "white"
    ]

    for key, rgb, aod_rgb in color_entries:
        rgba = (*rgb, 255)
        aod_rgba = (*aod_rgb, 255)

        dir_a = os.path.join(ASSETS_DIR, "clock_a", key)
        dir_b = os.path.join(ASSETS_DIR, "clock_b", key)
        dir_aod = os.path.join(ASSETS_DIR, "clock_aod", key)
        ensure_dir(dir_a)
        ensure_dir(dir_b)
        ensure_dir(dir_aod)

        for ch, name in glyphs:
            im_a = render_style_a_glyph(ch, rgba, 108)
            im_a.save(os.path.join(dir_a, f"{name}.png"))
            if key == "white":
                metrics["a"][ch] = {"w": im_a.width, "h": im_a.height}

            im_b = render_style_b_glyph(ch, rgba, 112)
            im_b.save(os.path.join(dir_b, f"{name}.png"))
            if key == "white":
                metrics["b"][ch] = {"w": im_b.width, "h": im_b.height}

            # Solid, clean dimmed digits for AOD at the same full size (not thin hollow outline)
            im_aod = render_style_a_glyph(ch, aod_rgba, 104)
            im_aod.save(os.path.join(dir_aod, f"{name}.png"))
            if key == "white":
                metrics["aod"][ch] = {"w": im_aod.width, "h": im_aod.height}

    return metrics


def generate_data_digits():
    """Crisp bold data digits for TEXT_IMG (Temp, HRV, RHR, BIO, PAI, HR)."""
    font_path = FONT_SEGOE_BOLD if os.path.exists(FONT_SEGOE_BOLD) else FONT_ARIAL_BOLD

    def render_fixed_data_glyph(ch, rgb, size_px=34):
        scale = 4
        font = ImageFont.truetype(font_path, int(size_px * scale))
        ref = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        ImageDraw.Draw(ref).text((40, 40), "0", font=font, fill=(*rgb, 255))
        rb = ref.getbbox()

        im = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((40, 40), ch, font=font, fill=(*rgb, 255))
        bb = im.getbbox()
        if not bb:
            return Image.new("RGBA", (18, 30), (0, 0, 0, 0))
        top = min(rb[1], bb[1]) - 4
        bottom = max(rb[3], bb[3]) + 4
        pad_x = 4 if ch in ("-", "°", "%") else 2
        crop = im.crop((bb[0] - pad_x, top, bb[2] + pad_x, bottom))
        nw = max(1, round(crop.width / scale))
        nh = max(1, round(crop.height / scale))
        return crop.resize((nw, nh), Image.Resampling.LANCZOS)

    # White set for cards & heart rate (size 35 -> ~28px tall inked digits)
    white_dir = os.path.join(ASSETS_DIR, "data", "white")
    ensure_dir(white_dir)
    for d in range(10):
        render_fixed_data_glyph(str(d), (255, 255, 255), 35).save(os.path.join(white_dir, f"{d}.png"))
    render_fixed_data_glyph("-", (255, 255, 255), 35).save(os.path.join(white_dir, "minus.png"))
    render_fixed_data_glyph("°", (255, 255, 255), 35).save(os.path.join(white_dir, "degree.png"))
    render_fixed_data_glyph("%", (255, 255, 255), 35).save(os.path.join(white_dir, "percent.png"))
    render_fixed_data_glyph("--", (140, 140, 140), 32).save(os.path.join(white_dir, "invalid.png"))

    # Top weather temperature digits (size 31)
    top_dir = os.path.join(ASSETS_DIR, "data", "top")
    ensure_dir(top_dir)
    for d in range(10):
        render_fixed_data_glyph(str(d), (255, 255, 255), 31).save(os.path.join(top_dir, f"{d}.png"))
    render_fixed_data_glyph("-", (255, 255, 255), 31).save(os.path.join(top_dir, "minus.png"))
    render_fixed_data_glyph("°", (255, 255, 255), 31).save(os.path.join(top_dir, "degree.png"))
    render_fixed_data_glyph("%", (255, 255, 255), 31).save(os.path.join(top_dir, "percent.png"))
    render_fixed_data_glyph("--", (140, 140, 140), 29).save(os.path.join(top_dir, "invalid.png"))


def draw_battery_icon(level_frac, fill_rgb, out_path):
    scale = 4
    w, h = 48 * scale, 26 * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Outer shell
    d.rounded_rectangle([2, 2, w - 16, h - 2], radius=6 * scale, outline=(255, 255, 255, 255), width=int(2.2 * scale))
    # Nub
    d.rounded_rectangle([w - 14, 7 * scale, w - 2, h - 7 * scale], radius=2 * scale, fill=(255, 255, 255, 255))
    # Inner fill bar
    inner_x0, inner_y0 = 6 * scale, 6 * scale
    inner_x1, inner_y1 = w - 20, h - 6 * scale
    max_fill = inner_x1 - inner_x0
    fw = max(2 * scale, int(max_fill * level_frac))
    if level_frac > 0.02:
        d.rounded_rectangle([inner_x0, inner_y0, inner_x0 + fw, inner_y1], radius=3 * scale, fill=(*fill_rgb, 255))
    im.resize((48, 26), Image.Resampling.LANCZOS).save(out_path)


def generate_icons():
    for key, _, rgb, _, _, _ in COLORS:
        bdir = os.path.join(ASSETS_DIR, "icons", "battery", key)
        ensure_dir(bdir)
        for idx, frac in enumerate([0.15, 0.35, 0.60, 0.82, 1.0]):
            draw_battery_icon(frac, rgb, os.path.join(bdir, f"{idx}.png"))

    # Heart icon (34x32)
    icons_dir = os.path.join(ASSETS_DIR, "icons")
    ensure_dir(icons_dir)
    for is_aod in (False, True):
        scale = 4
        w, h = 34 * scale, 32 * scale
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = []
        for deg in range(0, 360, 2):
            t = math.radians(deg)
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            px = w / 2 + x * (w / 36.0)
            py = h / 2 + y * (h / 35.0) - 2
            pts.append((px, py))
        if is_aod:
            d.polygon(pts, outline=(180, 55, 70, 255), width=2 * scale)
            out_name = "aod_heart.png"
        else:
            d.polygon(pts, fill=(*HEART_RGB, 255))
            out_name = "heart.png"
        im.resize((34, 32), Image.Resampling.LANCZOS).save(os.path.join(icons_dir, out_name))

    # 29 Weather icons (34x32)
    wdir = os.path.join(icons_dir, "weather")
    ensure_dir(wdir)

    def draw_cloud(d, cx, cy, s, color=(240, 240, 240, 255)):
        d.ellipse([cx - 11 * s, cy - 5 * s, cx + 2 * s, cy + 8 * s], fill=color)
        d.ellipse([cx - 5 * s, cy - 10 * s, cx + 9 * s, cy + 5 * s], fill=color)
        d.ellipse([cx + 2 * s, cy - 4 * s, cx + 13 * s, cy + 8 * s], fill=color)
        d.rounded_rectangle([cx - 10 * s, cy + 1 * s, cx + 12 * s, cy + 8 * s], radius=3 * s, fill=color)

    def draw_sun(d, cx, cy, s, color=(255, 210, 70, 255)):
        d.ellipse([cx - 6 * s, cy - 6 * s, cx + 6 * s, cy + 6 * s], fill=color)
        for a in range(0, 360, 45):
            r1, r2 = 8 * s, 11.5 * s
            rad = math.radians(a)
            d.line(
                [cx + r1 * math.cos(rad), cy + r1 * math.sin(rad), cx + r2 * math.cos(rad), cy + r2 * math.sin(rad)],
                fill=color,
                width=max(2, int(2.2 * s)),
            )

    def draw_moon(d, cx, cy, s, color=(250, 250, 250, 255)):
        d.ellipse([cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s], fill=color)
        d.ellipse([cx - 2 * s, cy - 11 * s, cx + 13 * s, cy + 4 * s], fill=(0, 0, 0, 0))

    def draw_rain(d, cx, cy, s, count=3):
        for i in range(count):
            ox = cx - (count - 1) * 3.8 * s + i * 7.6 * s
            d.line([ox, cy + 9 * s, ox - 2 * s, cy + 14 * s], fill=(120, 195, 255, 255), width=max(2, int(2.2 * s)))

    def draw_snow(d, cx, cy, s, count=3):
        for i in range(count):
            ox = cx - (count - 1) * 3.8 * s + i * 7.6 * s
            d.ellipse([ox - 2 * s, cy + 9 * s, ox + 2 * s, cy + 13 * s], fill=(230, 245, 255, 255))

    def draw_bolt(d, cx, cy, s):
        pts = [(cx + 1 * s, cy + 6 * s), (cx - 3.5 * s, cy + 11 * s), (cx + 0.5 * s, cy + 11 * s), (cx - 2 * s, cy + 16 * s), (cx + 4.5 * s, cy + 10 * s), (cx + 0.5 * s, cy + 10 * s)]
        d.polygon(pts, fill=(255, 215, 65, 255))

    for idx in range(29):
        s = 4
        im = Image.new("RGBA", (34 * s, 32 * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, cy = 17 * s, 15 * s
        if idx == 3:
            draw_sun(d, cx, cy + 1 * s, s)
        elif idx == 28:
            draw_moon(d, cx, cy + 1 * s, s)
        elif idx == 26:
            draw_moon(d, cx + 4 * s, cy - 3 * s, s * 0.75)
            draw_cloud(d, cx - 1 * s, cy + 2 * s, s * 0.9)
        elif idx == 27:
            draw_moon(d, cx + 4 * s, cy - 4 * s, s * 0.7)
            draw_cloud(d, cx, cy, s * 0.85)
            draw_rain(d, cx, cy, s * 0.9, 2)
        elif idx in (0, 4):
            draw_cloud(d, cx, cy, s)
        elif idx in (1, 5, 7, 10, 18, 21, 24):
            draw_cloud(d, cx, cy - 2 * s, s * 0.95)
            draw_rain(d, cx, cy - 2 * s, s, 3 if idx in (7, 10, 18, 21, 24) else 2)
        elif idx in (2, 6, 8, 9, 16):
            draw_cloud(d, cx, cy - 2 * s, s * 0.95)
            draw_snow(d, cx, cy - 2 * s, s, 3)
        elif idx in (12, 19):
            draw_cloud(d, cx, cy - 2 * s, s * 0.95)
            draw_rain(d, cx - 2 * s, cy - 2 * s, s, 2)
            draw_snow(d, cx + 4 * s, cy - 2 * s, s, 1)
        elif idx in (15, 20):
            draw_cloud(d, cx, cy - 3 * s, s * 0.95)
            draw_bolt(d, cx, cy - 3 * s, s)
        elif idx in (13, 14, 17, 11, 22, 23):
            for row in (-4, 0, 4):
                d.rounded_rectangle([cx - 11 * s, cy + row * s - s, cx + 11 * s, cy + row * s + s], radius=s, fill=(205, 205, 205, 255))
        else:
            draw_sun(d, cx + 5 * s, cy - 4 * s, s * 0.7)
            draw_cloud(d, cx - 1 * s, cy + 1 * s, s * 0.9)
        im.resize((34, 32), Image.Resampling.LANCZOS).save(os.path.join(wdir, f"{idx}.png"))


def generate_backgrounds():
    # Pure neutral grays (R == G == B) so AMOLED never tints them blue!
    s = 2
    im_a = Image.new("RGBA", (480 * s, 480 * s), (0, 0, 0, 255))
    da = ImageDraw.Draw(im_a)
    card_xs = [64, 155, 246, 337]
    for cx in card_xs:
        da.rounded_rectangle(
            [cx * s, 280 * s, (cx + 80) * s, 358 * s],
            radius=16 * s,
            fill=(24, 24, 24, 255),
            outline=(78, 78, 78, 255),
            width=2 * s,
        )
    im_a.resize((480, 480), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, "bg_a.png"))

    im_b = Image.new("RGBA", (480 * s, 480 * s), (0, 0, 0, 255))
    db = ImageDraw.Draw(im_b)
    db.rounded_rectangle(
        [52 * s, 280 * s, 428 * s, 358 * s],
        radius=20 * s,
        fill=(18, 18, 18, 255),
        outline=(86, 86, 86, 255),
        width=2 * s,
    )
    for dx in (148, 240, 332):
        db.line([dx * s, 294 * s, dx * s, 344 * s], fill=(72, 72, 72, 255), width=2)
    im_b.resize((480, 480), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, "bg_b.png"))


def generate_editor_assets():
    edir = os.path.join(ASSETS_DIR, "editor")
    ensure_dir(edir)

    mask = Image.new("RGBA", (480, 480), (0, 0, 0, 175))
    mask.save(os.path.join(edir, "mask.png"))

    for fname, border_col, bw in [("select.png", (255, 255, 255, 255), 3), ("unselect.png", (115, 115, 115, 200), 2)]:
        im = Image.new("RGBA", (140, 110), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([2, 2, 137, 107], radius=16, outline=border_col, width=bw)
        im.save(os.path.join(edir, fname))

    tips = Image.new("RGBA", (140, 28), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tips)
    dt.rounded_rectangle([1, 1, 138, 26], radius=10, fill=(28, 28, 28, 235), outline=(96, 96, 96, 255), width=1)
    tips.save(os.path.join(edir, "tips.png"))

    font_lbl = load_bahn(18, weight=700, width=100)
    for fname, title, is_b in [("style_a.png", "ARCOS + 4", False), ("style_b.png", "BATERIA + 1", True)]:
        im = Image.new("RGBA", (140, 110), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([6, 6, 133, 103], radius=14, fill=(18, 18, 18, 235))
        if not is_b:
            d.arc([20, 18, 120, 92], start=135, end=225, fill=(24, 144, 255, 255), width=4)
            d.arc([20, 18, 120, 92], start=-45, end=45, fill=(255, 126, 24, 255), width=4)
            for i in range(4):
                rx = 30 + i * 21
                d.rounded_rectangle([rx, 58, rx + 17, 74], radius=3, outline=(120, 120, 120, 255), width=1)
        else:
            d.arc([24, 14, 116, 86], start=215, end=325, fill=(46, 255, 166, 255), width=4)
            d.rounded_rectangle([28, 56, 112, 74], radius=5, outline=(120, 120, 120, 255), width=1)
        bb = d.textbbox((0, 0), title, font=font_lbl)
        d.text(((140 - (bb[2] - bb[0])) // 2, 80), title, font=font_lbl, fill=(240, 240, 240, 255))
        im.save(os.path.join(edir, fname))

    for key, label, rgb, _, _, _ in COLORS:
        im = Image.new("RGBA", (140, 110), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([6, 6, 133, 103], radius=14, fill=(18, 18, 18, 235))
        d.ellipse([48, 20, 92, 64], fill=(*rgb, 255), outline=(255, 255, 255, 180), width=2)
        bb = d.textbbox((0, 0), label.upper(), font=font_lbl)
        d.text(((140 - (bb[2] - bb[0])) // 2, 74), label.upper(), font=font_lbl, fill=(240, 240, 240, 255))
        im.save(os.path.join(edir, f"color_{key}.png"))


def write_glyph_metrics_js(metrics):
    ensure_dir(WATCHFACE_DIR)
    palette = [
        {
            "key": key,
            "name": label,
            "normalHex": hex_norm,
            "aodHex": hex_aod,
        }
        for key, label, _, _, hex_norm, hex_aod in COLORS
    ]
    js = (
        "// Auto-generated by scripts/generate_assets.py\n"
        f"export const GLYPH_METRICS = {json.dumps(metrics, indent=2)}\n"
        f"export const PALETTE = {json.dumps(palette, indent=2)}\n"
    )
    with open(os.path.join(WATCHFACE_DIR, "glyphs.js"), "w", encoding="utf-8") as f:
        f.write(js)


def render_composite_preview(style, accent1_key, accent2_key, metrics, out_path):
    bg_path = os.path.join(ASSETS_DIR, f"bg_{style}.png")
    canvas = Image.open(bg_path).convert("RGBA")
    d = ImageDraw.Draw(canvas)

    c1 = next(c for c in COLORS if c[0] == accent1_key)
    c2 = next(c for c in COLORS if c[0] == accent2_key)

    # Outer arcs (PIL uses 0°=3 o'clock; on watch ARC_PROGRESS uses 0°=12 o'clock)
    if style == "a":
        d.arc([14, 14, 466, 466], start=132, end=228, fill=(42, 42, 42, 255), width=12)
        d.arc([14, 14, 466, 466], start=132, end=210, fill=(*c1[2], 255), width=12)
        d.arc([14, 14, 466, 466], start=-48, end=48, fill=(42, 42, 42, 255), width=12)
        d.arc([14, 14, 466, 466], start=-30, end=48, fill=(*c2[2], 255), width=12)
    else:
        d.arc([14, 14, 466, 466], start=216, end=324, fill=(42, 42, 42, 255), width=16)
        d.arc([14, 14, 466, 466], start=216, end=216 + int(108 * 0.64), fill=(*c1[2], 255), width=16)

    # Battery row
    bat_icon = Image.open(os.path.join(ASSETS_DIR, "icons", "battery", accent1_key if style == "b" else "white", "2.png"))
    canvas.alpha_composite(bat_icon, (172, 48))
    font_bat = ImageFont.truetype(FONT_SEGOE_BOLD, 30)
    d.text((230, 44), "64%", font=font_bat, fill=(255, 255, 255, 255))

    # Weather + Spanish Date row (centered around x=240)
    w_icon = Image.open(os.path.join(ASSETS_DIR, "icons", "weather", "28.png"))
    canvas.alpha_composite(w_icon, (96, 94))
    font_sub = ImageFont.truetype(FONT_SEGOE_BOLD, 28)
    d.text((140, 93), "8°", font=font_sub, fill=(255, 255, 255, 255))
    d.line([202, 95, 202, 123], fill=(110, 110, 110, 255), width=2)
    if style == "b":
        d.text((218, 93), "DOM", font=font_sub, fill=(255, 255, 255, 255))
        d.text((290, 93), "08", font=font_sub, fill=(*c1[2], 255))
        d.text((330, 93), "NOV", font=font_sub, fill=(255, 255, 255, 255))
    else:
        d.text((218, 93), "DOM 08 NOV", font=font_sub, fill=(255, 255, 255, 255))

    # Centered Time 10:09 using exact glyph metrics!
    mset = metrics[style]
    digits = [("1", "white"), ("0", "white"), (":", "white"), ("0", accent1_key), ("9", accent1_key)]
    gap_d = 8
    gap_c = 12
    total_w = mset["1"]["w"] + gap_d + mset["0"]["w"] + gap_c + mset[":"]["w"] + gap_c + mset["0"]["w"] + gap_d + mset["9"]["w"]
    cur_x = round((480 - total_w) / 2)
    time_y = 148 if style == "a" else 146
    for idx, (ch, ckey) in enumerate(digits):
        fname = "colon.png" if ch == ":" else f"{ch}.png"
        gim = Image.open(os.path.join(ASSETS_DIR, f"clock_{style}", ckey, fname))
        canvas.alpha_composite(gim, (cur_x, time_y))
        cur_x += gim.width + (gap_c if idx in (1, 2) else gap_d)

    # Cards / Pill labels & sample values
    font_lbl = ImageFont.truetype(FONT_SEGOE_BOLD, 20)
    font_val = ImageFont.truetype(FONT_SEGOE_BOLD, 34)
    if style == "a":
        centers = [104, 195, 286, 377]
        items = [("HRV", "66", c1[2]), ("RHR", "44", c1[2]), ("BIO", "55", c2[2]), ("PAI", "84", c2[2])]
    else:
        centers = [100, 194, 286, 380]
        items = [("HRV", "66", c1[2]), ("RHR", "44", c1[2]), ("BIO", "55", c1[2]), ("PAI", "84", c1[2])]
    for cx, (lbl, val, lcol) in zip(centers, items):
        lb = d.textbbox((0, 0), lbl, font=font_lbl)
        d.text((cx - (lb[2] - lb[0]) // 2, 286), lbl, font=font_lbl, fill=(*lcol, 255))
        vb = d.textbbox((0, 0), val, font=font_val)
        d.text((cx - (vb[2] - vb[0]) // 2, 310), val, font=font_val, fill=(255, 255, 255, 255))

    # Bottom HR + sparkline
    heart = Image.open(os.path.join(ASSETS_DIR, "icons", "heart.png"))
    canvas.alpha_composite(heart, (192, 374))
    d.text((236, 368), "47", font=font_val, fill=(255, 255, 255, 255))

    spark_pts = [
        (152, 436), (164, 429), (176, 434), (188, 424), (200, 431),
        (212, 428), (224, 435), (236, 433), (248, 426), (260, 434),
        (272, 430), (284, 425), (296, 431), (308, 434), (324, 432),
    ]
    d.line(spark_pts, fill=(*HEART_RGB, 255), width=3)
    lx, ly = spark_pts[-1]
    d.ellipse([lx - 4, ly - 4, lx + 4, ly + 4], fill=(*HEART_RGB, 255))

    mask_c = Image.new("L", (480, 480), 0)
    ImageDraw.Draw(mask_c).ellipse([0, 0, 479, 479], fill=255)
    out = Image.new("RGBA", (480, 480), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), mask_c)
    out.save(out_path)
    return out


def main():
    ensure_dir(ASSETS_DIR)
    metrics = generate_clock_sets()
    generate_data_digits()
    generate_icons()
    generate_backgrounds()
    generate_editor_assets()
    write_glyph_metrics_js(metrics)

    prev_a = render_composite_preview("a", "blue", "orange", metrics, os.path.join(ARTIFACT_DIR, "preview_style_a.png"))
    prev_b = render_composite_preview("b", "mint", "mint", metrics, os.path.join(ARTIFACT_DIR, "preview_style_b.png"))

    prev_a.resize((324, 324), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, "icon.png"))
    print("Assets generated successfully! Glyph metrics A:", json.dumps(metrics["a"]))


if __name__ == "__main__":
    main()
