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
    ("lavender", "Lavender", (198, 164, 255), (140, 115, 182), 0xC6A4FF, 0x8C73B6),
    ("white",    "White",    (255, 255, 255), (175, 175, 175), 0xFFFFFF, 0xAFAFAF),
    ("mint",     "Mint",     (46, 255, 166),  (32, 180, 118),  0x2EFFA6, 0x20B476),
    ("cyan",     "Cyan",     (41, 217, 255),  (28, 152, 180),  0x29D9FF, 0x1C98B4),
    ("blue",     "Blue",     (24, 144, 255),  (20, 105, 190),  0x1890FF, 0x1469BE),
    ("orange",   "Orange",   (255, 126, 24),  (185, 90, 18),   0xFF7E18, 0xB95A12),
    ("amber",    "Amber",    (245, 162, 24),  (175, 115, 18),  0xF5A218, 0xAF7312),
    ("red",      "Red",      (255, 77, 90),   (185, 55, 65),   0xFF4D5A, 0xB93741),
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


def render_lavender_glyph(ch, color_rgba, target_h=112):
    """Render bold geometric sans digits with normal 2-dot vertical colon (:) matching Dual Pill Lavender."""
    scale = 4
    H = target_h * scale
    if ch == ":":
        W = 24 * scale
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        dot_d = 20 * scale
        x0 = (W - dot_d) // 2
        # Two normal circular colon dots
        for frac in (0.21, 0.61):
            y0 = int(H * frac)
            d.ellipse([x0, y0, x0 + dot_d, y0 + dot_d], fill=color_rgba)
        return im.resize((24, target_h), Image.Resampling.LANCZOS)

    canvas_w, canvas_h = 1000, 1000
    font_path = FONT_ARIAL_BLACK if os.path.exists(FONT_ARIAL_BLACK) else FONT_ARIAL_BOLD
    font = ImageFont.truetype(font_path, int(target_h * scale * 1.22))
    im = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((150, 100), ch, font=font, fill=color_rgba, stroke_width=int(1.6 * scale), stroke_fill=color_rgba)

    ref = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    ImageDraw.Draw(ref).text((150, 100), "0", font=font, fill=color_rgba, stroke_width=int(1.6 * scale), stroke_fill=color_rgba)
    rb = ref.getbbox()
    bb = im.getbbox()
    pad_y = 6
    top = max(0, min(rb[1], bb[1]) - pad_y)
    bottom = min(canvas_h, max(rb[3], bb[3]) + pad_y)
    cropped = im.crop((bb[0], top, bb[2], bottom))
    raw_ratio = cropped.width / max(1, rb[2] - rb[0])
    target_w = 54 if ch == "1" else max(74, round(86 * raw_ratio))
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def generate_clock_sets():
    metrics = {"normal": {}, "aod": {}}
    glyphs = [(str(d), str(d)) for d in range(10)] + [(":", "colon")]

    for key, _, rgb, aod_rgb, _, _ in COLORS:
        rgba = (*rgb, 255)
        aod_rgba = (*aod_rgb, 255)

        dir_norm = os.path.join(ASSETS_DIR, "clock", key)
        dir_aod = os.path.join(ASSETS_DIR, "clock_aod", key)
        ensure_dir(dir_norm)
        ensure_dir(dir_aod)

        for ch, name in glyphs:
            im_n = render_lavender_glyph(ch, rgba, 112)
            im_n.save(os.path.join(dir_norm, f"{name}.png"))
            if key == "white":
                metrics["normal"][ch] = {"w": im_n.width, "h": im_n.height}

            im_aod = render_lavender_glyph(ch, aod_rgba, 108)
            im_aod.save(os.path.join(dir_aod, f"{name}.png"))
            if key == "white":
                metrics["aod"][ch] = {"w": im_aod.width, "h": im_aod.height}

    return metrics


def generate_data_digits():
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

    white_dir = os.path.join(ASSETS_DIR, "data", "white")
    ensure_dir(white_dir)
    for d in range(10):
        render_fixed_data_glyph(str(d), (255, 255, 255), 34).save(os.path.join(white_dir, f"{d}.png"))
    render_fixed_data_glyph("-", (255, 255, 255), 34).save(os.path.join(white_dir, "minus.png"))
    render_fixed_data_glyph("°", (255, 255, 255), 34).save(os.path.join(white_dir, "degree.png"))
    render_fixed_data_glyph("%", (255, 255, 255), 34).save(os.path.join(white_dir, "percent.png"))
    render_fixed_data_glyph("--", (140, 140, 140), 31).save(os.path.join(white_dir, "invalid.png"))

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
    w, h = 44 * scale, 22 * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, w - 14, h - 2], radius=5 * scale, outline=(255, 255, 255, 255), width=int(2.0 * scale))
    d.rounded_rectangle([w - 12, 6 * scale, w - 2, h - 6 * scale], radius=2 * scale, fill=(255, 255, 255, 255))
    inner_x0, inner_y0 = 6 * scale, 5 * scale
    inner_x1, inner_y1 = w - 18, h - 5 * scale
    max_fill = inner_x1 - inner_x0
    fw = max(2 * scale, int(max_fill * level_frac))
    if level_frac > 0.02:
        d.rounded_rectangle([inner_x0, inner_y0, inner_x0 + fw, inner_y1], radius=2 * scale, fill=(*fill_rgb, 255))
    im.resize((44, 22), Image.Resampling.LANCZOS).save(out_path)


def generate_icons():
    for key, _, rgb, _, _, _ in COLORS:
        bdir = os.path.join(ASSETS_DIR, "icons", "battery", key)
        ensure_dir(bdir)
        for idx, frac in enumerate([0.15, 0.35, 0.60, 0.82, 1.0]):
            draw_battery_icon(frac, rgb, os.path.join(bdir, f"{idx}.png"))

    icons_dir = os.path.join(ASSETS_DIR, "icons")
    ensure_dir(icons_dir)
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
    d.polygon(pts, fill=(*HEART_RGB, 255))
    im.resize((34, 32), Image.Resampling.LANCZOS).save(os.path.join(icons_dir, "heart.png"))

    wdir = os.path.join(icons_dir, "weather")
    ensure_dir(wdir)

    def draw_cloud(d, cx, cy, s, color=(235, 225, 255, 255)):
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

    def draw_moon(d, cx, cy, s, color=(198, 164, 255, 255)):
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
    """Generate background with top battery capsule + left biometric pill (primary), and separate right pill sprites (secondary)."""
    s = 4
    pills_dir = os.path.join(ASSETS_DIR, "pills")
    ensure_dir(pills_dir)

    for key, _, rgb, _, _, _ in COLORS:
        im = Image.new("RGBA", (480 * s, 480 * s), (0, 0, 0, 255))
        d = ImageDraw.Draw(im)

        # Top battery capsule outline in primary accent color (x=164..316, y=38..80, radius=21)
        d.rounded_rectangle(
            [164 * s, 38 * s, 316 * s, 80 * s],
            radius=21 * s,
            fill=(14, 14, 14, 255),
            outline=(*rgb, 255),
            width=int(2.2 * s),
        )

        # Left rounded biometric pill (HRV | RHR) in primary accent color at x=70..234, y=296..362
        pill_border = (int(rgb[0] * 0.78), int(rgb[1] * 0.78), int(rgb[2] * 0.78), 255)
        bx0, bx1, mid_x = 70, 234, 152
        d.rounded_rectangle(
            [bx0 * s, 296 * s, bx1 * s, 362 * s],
            radius=16 * s,
            fill=(18, 18, 18, 255),
            outline=pill_border,
            width=int(2.0 * s),
        )
        d.line(
            [(mid_x * s, 308 * s), (mid_x * s, 350 * s)],
            fill=pill_border,
            width=int(1.6 * s),
        )

        im.resize((480, 480), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, f"bg_{key}.png"))

        # Right rounded biometric pill sprite (BIO | PAI) at x=244..412, y=294..364 (168x70)
        # Drawn with secondary (minutes) color so the right capsule matches the minutes color!
        pw, ph = 168, 70
        pim = Image.new("RGBA", (pw * s, ph * s), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pim)
        rx0, ry0 = 2 * s, 2 * s
        rx1, ry1 = (pw - 2) * s, (ph - 2) * s
        rmid_x = (pw // 2) * s
        pd.rounded_rectangle(
            [rx0, ry0, rx1, ry1],
            radius=16 * s,
            fill=(18, 18, 18, 255),
            outline=pill_border,
            width=int(2.0 * s),
        )
        pd.line(
            [(rmid_x, 14 * s), (rmid_x, (ph - 14) * s)],
            fill=pill_border,
            width=int(1.6 * s),
        )
        pim.resize((pw, ph), Image.Resampling.LANCZOS).save(os.path.join(pills_dir, f"pill_{key}.png"))


def generate_editor_assets():
    edir = os.path.join(ASSETS_DIR, "editor")
    ensure_dir(edir)

    mask = Image.new("RGBA", (480, 480), (0, 0, 0, 185))
    mask.save(os.path.join(edir, "mask.png"))

    box_w, box_h = 156, 136
    for fname, border_col, bw in [("select.png", (255, 255, 255, 255), 3), ("unselect.png", (110, 110, 110, 200), 2)]:
        im = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([2, 2, box_w - 3, box_h - 3], radius=16, outline=border_col, width=bw)
        im.save(os.path.join(edir, fname))

    tips = Image.new("RGBA", (120, 26), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tips)
    dt.rounded_rectangle([1, 1, 118, 24], radius=10, fill=(28, 28, 28, 240), outline=(96, 96, 96, 255), width=1)
    tips.save(os.path.join(edir, "tips.png"))

    font_zone = ImageFont.truetype(FONT_SEGOE_BOLD, 13)
    font_lbl = ImageFont.truetype(FONT_SEGOE_BOLD, 16)
    font_clock_mini = load_bahn(32, weight=700, width=100)

    for key, label, rgb, _, _, _ in COLORS:
        # 1. Primary card: "TEMA + CAP. IZQ" + miniature side arcs & left pill box + color name
        im_p = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        dp = ImageDraw.Draw(im_p)
        dp.rounded_rectangle([6, 6, box_w - 7, box_h - 7], radius=14, fill=(18, 18, 18, 245))
        dp.rounded_rectangle([12, 11, box_w - 13, 33], radius=7, fill=(38, 38, 38, 255))
        zb = dp.textbbox((0, 0), "TEMA + CAP. IZQ", font=font_zone)
        dp.text(((box_w - (zb[2] - zb[0])) // 2, 13 - zb[1]), "TEMA + CAP. IZQ", font=font_zone, fill=(255, 255, 255, 255))

        # Mini left & right arcs + left rounded pill box in chosen color
        dp.arc([20, 38, box_w - 20, 98], start=138, end=222, fill=(*rgb, 255), width=4)
        dp.arc([20, 38, box_w - 20, 98], start=-42, end=42, fill=(*rgb, 255), width=4)
        dp.rounded_rectangle([34, 52, 76, 84], radius=8, fill=(18, 18, 18, 255), outline=(*rgb, 255), width=2)
        dp.rounded_rectangle([80, 52, box_w - 34, 84], radius=8, fill=(18, 18, 18, 255), outline=(80, 80, 80, 255), width=1)

        cb = dp.textbbox((0, 0), label.upper(), font=font_lbl)
        dp.text(((box_w - (cb[2] - cb[0])) // 2, 103 - cb[1]), label.upper(), font=font_lbl, fill=(*rgb, 255))
        im_p.save(os.path.join(edir, f"primary_{key}.png"))

        # 2. Secondary card: "MIN + CAP. DER" + miniature "10:09" (2 dots) & right pill in chosen color
        im_s = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        ds = ImageDraw.Draw(im_s)
        ds.rounded_rectangle([6, 6, box_w - 7, box_h - 7], radius=14, fill=(18, 18, 18, 245))
        ds.rounded_rectangle([12, 11, box_w - 13, 33], radius=7, fill=(38, 38, 38, 255))
        zb2 = ds.textbbox((0, 0), "MIN + CAP. DER", font=font_zone)
        ds.text(((box_w - (zb2[2] - zb2[0])) // 2, 13 - zb2[1]), "MIN + CAP. DER", font=font_zone, fill=(255, 255, 255, 255))

        b10 = ds.textbbox((0, 0), "10:", font=font_clock_mini)
        b09 = ds.textbbox((0, 0), "09", font=font_clock_mini)
        w10 = b10[2] - b10[0]
        w09 = b09[2] - b09[0]
        tot_w = w10 + 4 + w09
        sx = (box_w - tot_w) // 2
        ds.text((sx - b10[0], 39 - b10[1]), "10:", font=font_clock_mini, fill=(255, 255, 255, 255))
        ds.text((sx + w10 + 4 - b09[0], 39 - b09[1]), "09", font=font_clock_mini, fill=(*rgb, 255))
        ds.rounded_rectangle([34, 74, 76, 94], radius=6, fill=(18, 18, 18, 255), outline=(80, 80, 80, 255), width=1)
        ds.rounded_rectangle([80, 74, box_w - 34, 94], radius=6, fill=(18, 18, 18, 255), outline=(*rgb, 255), width=2)

        ds.text(((box_w - (cb[2] - cb[0])) // 2, 103 - cb[1]), label.upper(), font=font_lbl, fill=(*rgb, 255))
        im_s.save(os.path.join(edir, f"secondary_{key}.png"))


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


def render_composite_preview(accent_key, digit_key, metrics, out_path):
    canvas = Image.open(os.path.join(ASSETS_DIR, f"bg_{accent_key}.png")).convert("RGBA")
    right_pill = Image.open(os.path.join(ASSETS_DIR, "pills", f"pill_{digit_key}.png")).convert("RGBA")
    canvas.alpha_composite(right_pill, (244, 294))
    d = ImageDraw.Draw(canvas)

    c_acc = next(c for c in COLORS if c[0] == accent_key)
    c_dig = next(c for c in COLORS if c[0] == digit_key)

    # Slim left & right arcs
    d.arc([12, 12, 468, 468], start=132, end=228, fill=(42, 42, 42, 255), width=7)
    d.arc([12, 12, 468, 468], start=132, end=218, fill=(*c_acc[2], 255), width=7)
    d.arc([12, 12, 468, 468], start=-48, end=48, fill=(42, 42, 42, 255), width=7)
    d.arc([12, 12, 468, 468], start=-38, end=48, fill=(*c_acc[2], 255), width=7)

    # Top battery inside capsule
    bat_icon = Image.open(os.path.join(ASSETS_DIR, "icons", "battery", "white", "2.png"))
    canvas.alpha_composite(bat_icon, (182, 48))
    font_bat = ImageFont.truetype(FONT_SEGOE_BOLD, 28)
    d.text((234, 42), "64%", font=font_bat, fill=(255, 255, 255, 255))

    # Weather + Date row (DOM in accent, 08 in white, NOV in accent)
    w_icon = Image.open(os.path.join(ASSETS_DIR, "icons", "weather", "28.png"))
    canvas.alpha_composite(w_icon, (96, 110))
    font_sub = ImageFont.truetype(FONT_SEGOE_BOLD, 28)
    d.text((140, 109), "8°", font=font_sub, fill=(255, 255, 255, 255))
    d.line([198, 110, 198, 138], fill=(110, 110, 110, 255), width=2)
    d.text((216, 109), "DOM", font=font_sub, fill=(*c_acc[2], 255))
    d.text((292, 109), "08", font=font_sub, fill=(255, 255, 255, 255))
    d.text((334, 109), "NOV", font=font_sub, fill=(*c_acc[2], 255))

    # Centered Time 10:09 with 2-dot colon
    mset = metrics["normal"]
    digits = [("1", "white"), ("0", "white"), (":", "white"), ("0", digit_key), ("9", digit_key)]
    gap_d = 8
    gap_c = 12
    total_w = mset["1"]["w"] + gap_d + mset["0"]["w"] + gap_c + mset[":"]["w"] + gap_c + mset["0"]["w"] + gap_d + mset["9"]["w"]
    cur_x = round((480 - total_w) / 2)
    time_y = 170
    for idx, (ch, ckey) in enumerate(digits):
        fname = "colon.png" if ch == ":" else f"{ch}.png"
        gim = Image.open(os.path.join(ASSETS_DIR, "clock", ckey, fname))
        canvas.alpha_composite(gim, (cur_x, time_y))
        cur_x += gim.width + (gap_c if idx in (1, 2) else gap_d)

    # Dual pills labels & values (Left pill = primary color, Right pill = secondary/minutes color)
    font_lbl = ImageFont.truetype(FONT_SEGOE_BOLD, 19)
    font_val = ImageFont.truetype(FONT_SEGOE_BOLD, 32)
    centers = [111, 193, 287, 369]
    items = [("HRV", "66", c_acc[2]), ("RHR", "44", c_acc[2]), ("BIO", "55", c_dig[2]), ("PAI", "84", c_dig[2])]
    for cx_col, (lbl, val, l_rgb) in zip(centers, items):
        lb = d.textbbox((0, 0), lbl, font=font_lbl)
        d.text((cx_col - (lb[2] - lb[0]) // 2, 300), lbl, font=font_lbl, fill=(*l_rgb, 255))
        vb = d.textbbox((0, 0), val, font=font_val)
        d.text((cx_col - (vb[2] - vb[0]) // 2, 318), val, font=font_val, fill=(255, 255, 255, 255))

    # Bottom HR + sparkline
    heart = Image.open(os.path.join(ASSETS_DIR, "icons", "heart.png"))
    canvas.alpha_composite(heart, (194, 380))
    d.text((238, 374), "47", font=font_val, fill=(255, 255, 255, 255))

    spark_pts = [
        (160, 430), (171, 424), (182, 429), (193, 420), (204, 427),
        (215, 424), (226, 431), (237, 429), (248, 422), (259, 430),
        (270, 426), (281, 421), (292, 427), (303, 430), (316, 428),
    ]
    d.line(spark_pts, fill=(*HEART_RGB, 255), width=3)
    lx, ly = spark_pts[-1]
    d.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(*HEART_RGB, 255))

    mask_c = Image.new("L", (480, 480), 0)
    ImageDraw.Draw(mask_c).ellipse([0, 0, 479, 479], fill=255)
    out = Image.new("RGBA", (480, 480), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), mask_c)
    ensure_dir(os.path.dirname(out_path))
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

    prev = render_composite_preview("lavender", "white", metrics, os.path.join(ARTIFACT_DIR, "preview_dual_lavender.png"))
    prev.resize((324, 324), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, "icon.png"))
    print("Dual Pill Lavender assets generated successfully!")


if __name__ == "__main__":
    main()
