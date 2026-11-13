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
    ("amber",  "Amber",  (245, 162, 24),  (175, 115, 18),  0xF5A218, 0xAF7312),
    ("cream",  "Cream",  (255, 243, 214), (180, 172, 150), 0xFFF3D6, 0xB4AC96),
    ("gold",   "Gold",   (245, 190, 63),  (175, 135, 44),  0xF5BE3F, 0xAF872C),
    ("orange", "Orange", (255, 126, 24),  (185, 90, 18),   0xFF7E18, 0xB95A12),
    ("mint",   "Mint",   (46, 255, 166),  (32, 180, 118),  0x2EFFA6, 0x20B476),
    ("cyan",   "Cyan",   (41, 217, 255),  (28, 152, 180),  0x29D9FF, 0x1C98B4),
    ("blue",   "Blue",   (24, 144, 255),  (20, 105, 190),  0x1890FF, 0x1469BE),
    ("red",    "Red",    (255, 77, 90),   (185, 55, 65),   0xFF4D5A, 0xB93741),
    ("violet", "Violet", (198, 164, 255), (140, 115, 182), 0xC6A4FF, 0x8C73B6),
    ("white",  "White",  (255, 255, 255), (175, 175, 175), 0xFFFFFF, 0xAFAFAF),
]

CREAM_RGB = (255, 243, 214)
CREAM_HEX = 0xFFF3D6
HEART_RGB = (255, 67, 90)
HEART_HEX = 0xFF435A

FONT_BAHN = r"C:\Windows\Fonts\bahnschrift.ttf"
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


def render_tactical_glyph(ch, color_rgba, target_h=104):
    """Render bold tactical blocky digits matching the Tactical Amber reference:
    - '1' has top-left angled nose + bottom horizontal slab base bar (60px wide)
    - '0', '2'..'9' are geometric rounded-block tactical digits (80px wide)
    - ':' is two bold rounded-square dots (18px wide)
    """
    scale = 4
    H = target_h * scale
    if ch == ":":
        W = 18 * scale
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        dot_s = 16 * scale
        x0 = (W - dot_s) // 2
        d.rounded_rectangle([x0, int(H * 0.22), x0 + dot_s, int(H * 0.22) + dot_s], radius=3 * scale, fill=color_rgba)
        d.rounded_rectangle([x0, int(H * 0.62), x0 + dot_s, int(H * 0.62) + dot_s], radius=3 * scale, fill=color_rgba)
        return im.resize((18, target_h), Image.Resampling.LANCZOS)

    if ch == "1":
        W = 60 * scale
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        stem_w = 22 * scale
        stem_x0 = (W - stem_w) // 2 + 2 * scale
        stem_x1 = stem_x0 + stem_w
        base_h = 18 * scale
        d.rounded_rectangle([stem_x0, 0, stem_x1, H - base_h // 2], radius=2 * scale, fill=color_rgba)
        nose_pts = [
            (stem_x0 - 18 * scale, int(H * 0.14)),
            (stem_x0 + 4 * scale, 0),
            (stem_x1, 0),
            (stem_x1, int(H * 0.27)),
            (stem_x0 - 18 * scale, int(H * 0.27)),
        ]
        d.polygon(nose_pts, fill=color_rgba)
        d.rounded_rectangle([2 * scale, H - base_h, W - 2 * scale, H], radius=2 * scale, fill=color_rgba)
        return im.resize((60, target_h), Image.Resampling.LANCZOS)

    W = 80 * scale
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    T = int(21 * scale)
    R = int(21 * scale)
    r_in = int(6 * scale)
    mid_y0 = (H - int(18.5 * scale)) // 2
    mid_y1 = mid_y0 + int(18.5 * scale)

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

    return im.resize((80, target_h), Image.Resampling.LANCZOS)


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
            im_n = render_tactical_glyph(ch, rgba, 104)
            im_n.save(os.path.join(dir_norm, f"{name}.png"))
            if key == "cream":
                metrics["normal"][ch] = {"w": im_n.width, "h": im_n.height}

            im_aod = render_tactical_glyph(ch, aod_rgba, 102)
            im_aod.save(os.path.join(dir_aod, f"{name}.png"))
            if key == "cream":
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

    # Cream/White set for cards & heart rate (size 33 -> ~26px tall)
    white_dir = os.path.join(ASSETS_DIR, "data", "cream")
    ensure_dir(white_dir)
    for d in range(10):
        render_fixed_data_glyph(str(d), CREAM_RGB, 33).save(os.path.join(white_dir, f"{d}.png"))
    render_fixed_data_glyph("-", CREAM_RGB, 33).save(os.path.join(white_dir, "minus.png"))
    render_fixed_data_glyph("°", CREAM_RGB, 33).save(os.path.join(white_dir, "degree.png"))
    render_fixed_data_glyph("%", CREAM_RGB, 33).save(os.path.join(white_dir, "percent.png"))
    render_fixed_data_glyph("--", (140, 134, 120), 30).save(os.path.join(white_dir, "invalid.png"))

    # Top weather temperature digits (size 30)
    top_dir = os.path.join(ASSETS_DIR, "data", "top")
    ensure_dir(top_dir)
    for d in range(10):
        render_fixed_data_glyph(str(d), CREAM_RGB, 30).save(os.path.join(top_dir, f"{d}.png"))
    render_fixed_data_glyph("-", CREAM_RGB, 30).save(os.path.join(top_dir, "minus.png"))
    render_fixed_data_glyph("°", CREAM_RGB, 30).save(os.path.join(top_dir, "degree.png"))
    render_fixed_data_glyph("%", CREAM_RGB, 30).save(os.path.join(top_dir, "percent.png"))
    render_fixed_data_glyph("--", (140, 134, 120), 28).save(os.path.join(top_dir, "invalid.png"))


def draw_battery_icon(level_frac, fill_rgb, out_path):
    scale = 4
    w, h = 48 * scale, 24 * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, w - 16, h - 2], radius=5 * scale, outline=(*CREAM_RGB, 255), width=int(2.2 * scale))
    d.rounded_rectangle([w - 14, 6 * scale, w - 2, h - 6 * scale], radius=2 * scale, fill=(*CREAM_RGB, 255))
    inner_x0, inner_y0 = 6 * scale, 6 * scale
    inner_x1, inner_y1 = w - 20, h - 6 * scale
    max_fill = inner_x1 - inner_x0
    fw = max(2 * scale, int(max_fill * level_frac))
    if level_frac > 0.02:
        d.rounded_rectangle([inner_x0, inner_y0, inner_x0 + fw, inner_y1], radius=2 * scale, fill=(*fill_rgb, 255))
    im.resize((48, 24), Image.Resampling.LANCZOS).save(out_path)


def generate_segmented_arcs():
    """Pre-render the 10-segment curved battery gauge + thin outer curved line for each accent color."""
    s = 4
    crop_x0, crop_y0, crop_w, crop_h = 120, 32, 240, 48
    cx, cy = 240 * s, 240 * s

    for key, _, rgb, _, _, _ in COLORS:
        seg_dir = os.path.join(ASSETS_DIR, "arc_seg", key)
        ensure_dir(seg_dir)
        active_col = (*rgb, 255)
        inactive_col = (max(24, int(rgb[0] * 0.24)), max(24, int(rgb[1] * 0.24)), max(20, int(rgb[2] * 0.24)), 255)

        for filled_count in range(11):
            full = Image.new("RGBA", (480 * s, 120 * s), (0, 0, 0, 0))
            d = ImageDraw.Draw(full)

            # Outer thin curved line from -33° to +33° around 12 o'clock (i.e. 237° to 303° in PIL angles)
            r_line = 205 * s
            d.arc(
                [cx - r_line, cy - r_line, cx + r_line, cy + r_line],
                start=237,
                end=303,
                fill=active_col,
                width=int(2.0 * s),
            )

            # 10 distinct trapezoid/annular segments from r_in=190 to r_out=200
            r_in = 190 * s
            r_out = 200 * s
            start_deg = -32.5
            total_span = 65.0
            gap_deg = 1.0
            seg_span = (total_span - 9 * gap_deg) / 10.0

            for i in range(10):
                a0 = start_deg + i * (seg_span + gap_deg)
                a1 = a0 + seg_span
                pts = []
                steps = 12
                for st in range(steps + 1):
                    ang = math.radians(a0 + (a1 - a0) * (st / steps))
                    pts.append((cx + r_out * math.sin(ang), cy - r_out * math.cos(ang)))
                for st in range(steps, -1, -1):
                    ang = math.radians(a0 + (a1 - a0) * (st / steps))
                    pts.append((cx + r_in * math.sin(ang), cy - r_in * math.cos(ang)))
                d.polygon(pts, fill=active_col if i < filled_count else inactive_col)

            cropped = full.crop((crop_x0 * s, crop_y0 * s, (crop_x0 + crop_w) * s, (crop_y0 + crop_h) * s))
            cropped.resize((crop_w, crop_h), Image.Resampling.LANCZOS).save(os.path.join(seg_dir, f"{filled_count}.png"))


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

    def draw_cloud(d, cx, cy, s, color=(*CREAM_RGB, 255)):
        d.ellipse([cx - 11 * s, cy - 5 * s, cx + 2 * s, cy + 8 * s], fill=color)
        d.ellipse([cx - 5 * s, cy - 10 * s, cx + 9 * s, cy + 5 * s], fill=color)
        d.ellipse([cx + 2 * s, cy - 4 * s, cx + 13 * s, cy + 8 * s], fill=color)
        d.rounded_rectangle([cx - 10 * s, cy + 1 * s, cx + 12 * s, cy + 8 * s], radius=3 * s, fill=color)

    def draw_sun(d, cx, cy, s, color=(255, 200, 55, 255)):
        d.ellipse([cx - 6 * s, cy - 6 * s, cx + 6 * s, cy + 6 * s], fill=color)
        for a in range(0, 360, 45):
            r1, r2 = 8 * s, 11.5 * s
            rad = math.radians(a)
            d.line(
                [cx + r1 * math.cos(rad), cy + r1 * math.sin(rad), cx + r2 * math.cos(rad), cy + r2 * math.sin(rad)],
                fill=color,
                width=max(2, int(2.2 * s)),
            )

    def draw_moon(d, cx, cy, s, color=(*CREAM_RGB, 255)):
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
                d.rounded_rectangle([cx - 11 * s, cy + row * s - s, cx + 11 * s, cy + row * s + s], radius=s, fill=(*CREAM_RGB, 255))
        else:
            draw_sun(d, cx + 5 * s, cy - 4 * s, s * 0.7)
            draw_cloud(d, cx - 1 * s, cy + 1 * s, s * 0.9)
        im.resize((34, 32), Image.Resampling.LANCZOS).save(os.path.join(wdir, f"{idx}.png"))


def draw_chamfer_box(d, x0, y0, x1, y1, ch, fill_col, outline_col, width):
    pts = [
        (x0 + ch, y0),
        (x1 - ch, y0),
        (x1, y0 + ch),
        (x1, y1 - ch),
        (x1 - ch, y1),
        (x0 + ch, y1),
        (x0, y1 - ch),
        (x0, y0 + ch),
    ]
    d.polygon(pts, fill=fill_col)
    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i + 1) % len(pts)]
        d.line([p1, p2], fill=outline_col, width=width)


def generate_backgrounds():
    """Generate tactical 60-tick bezel + chamfered octagonal boxes for each accent color."""
    s = 4
    cx, cy = 240 * s, 240 * s

    for key, _, rgb, _, _, _ in COLORS:
        im = Image.new("RGBA", (480 * s, 480 * s), (0, 0, 0, 255))
        d = ImageDraw.Draw(im)

        col_bright = (*rgb, 255)
        col_minor = (int(rgb[0] * 0.82), int(rgb[1] * 0.82), int(rgb[2] * 0.82), 255)

        # 60 perimeter bezel ticks
        for i in range(60):
            ang = math.radians(i * 6.0)
            sin_a, cos_a = math.sin(ang), -math.cos(ang)
            r_out = 234 * s
            if i % 15 == 0:
                r_in = 212 * s
                w = int(5.5 * s)
                col = col_bright
            elif i % 5 == 0:
                r_in = 216 * s
                w = int(3.4 * s)
                col = col_bright
            else:
                r_in = 223 * s
                w = int(1.6 * s)
                col = col_minor

            x0 = cx + r_in * sin_a
            y0 = cy + r_in * cos_a
            x1 = cx + r_out * sin_a
            y1 = cy + r_out * cos_a
            d.line([(x0, y0), (x1, y1)], fill=col, width=w)

        # Two chamfered octagonal boxes at y=296..358
        # Left box: x=68..232, Right box: x=248..412
        for bx0, bx1, mid_x in [(68, 232, 150), (248, 412, 330)]:
            draw_chamfer_box(
                d,
                bx0 * s,
                296 * s,
                bx1 * s,
                358 * s,
                9 * s,
                fill_col=(10, 10, 10, 255),
                outline_col=col_bright,
                width=int(2.0 * s),
            )
            d.line(
                [(mid_x * s, 307 * s), (mid_x * s, 347 * s)],
                fill=col_bright,
                width=int(1.6 * s),
            )

        im.resize((480, 480), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, f"bg_{key}.png"))


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

    font_zone = ImageFont.truetype(FONT_SEGOE_BOLD, 14)
    font_lbl = ImageFont.truetype(FONT_SEGOE_BOLD, 16)
    font_clock_mini = load_bahn(34, weight=700, width=100)

    for key, label, rgb, _, _, _ in COLORS:
        # 1. Primary card: "TEMA / BISEL" + miniature bezel arc & chamfered box + color name
        im_p = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        dp = ImageDraw.Draw(im_p)
        dp.rounded_rectangle([6, 6, box_w - 7, box_h - 7], radius=14, fill=(18, 18, 18, 245))
        dp.rounded_rectangle([14, 11, box_w - 15, 33], radius=7, fill=(38, 38, 38, 255))
        zb = dp.textbbox((0, 0), "TEMA / BISEL", font=font_zone)
        dp.text(((box_w - (zb[2] - zb[0])) // 2, 13 - zb[1]), "TEMA / BISEL", font=font_zone, fill=(255, 255, 255, 255))

        # Mini segmented top arc + chamfered octagonal box in chosen color
        dp.arc([36, 40, box_w - 36, 92], start=210, end=330, fill=(*rgb, 255), width=5)
        draw_chamfer_box(dp, 32, 62, box_w - 32, 92, 6, (10, 10, 10, 255), (*rgb, 255), 2)
        dp.line([(box_w // 2, 67), (box_w // 2, 87)], fill=(*rgb, 255), width=2)

        cb = dp.textbbox((0, 0), label.upper(), font=font_lbl)
        dp.text(((box_w - (cb[2] - cb[0])) // 2, 103 - cb[1]), label.upper(), font=font_lbl, fill=(*rgb, 255))
        im_p.save(os.path.join(edir, f"primary_{key}.png"))

        # 2. Secondary card: "COLOR MINUTOS" + miniature "10:09" with 09 in chosen color + color name
        im_s = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        ds = ImageDraw.Draw(im_s)
        ds.rounded_rectangle([6, 6, box_w - 7, box_h - 7], radius=14, fill=(18, 18, 18, 245))
        ds.rounded_rectangle([14, 11, box_w - 15, 33], radius=7, fill=(38, 38, 38, 255))
        zb2 = ds.textbbox((0, 0), "COLOR MINUTOS", font=font_zone)
        ds.text(((box_w - (zb2[2] - zb2[0])) // 2, 13 - zb2[1]), "COLOR MINUTOS", font=font_zone, fill=(255, 255, 255, 255))

        b10 = ds.textbbox((0, 0), "10:", font=font_clock_mini)
        b09 = ds.textbbox((0, 0), "09", font=font_clock_mini)
        w10 = b10[2] - b10[0]
        w09 = b09[2] - b09[0]
        tot_w = w10 + 4 + w09
        sx = (box_w - tot_w) // 2
        ds.text((sx - b10[0], 50 - b10[1]), "10:", font=font_clock_mini, fill=(*CREAM_RGB, 255))
        ds.text((sx + w10 + 4 - b09[0], 50 - b09[1]), "09", font=font_clock_mini, fill=(*rgb, 255))

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
    d = ImageDraw.Draw(canvas)

    c_acc = next(c for c in COLORS if c[0] == accent_key)

    # Top 10-segment arc (6/10 filled for 64%)
    seg_img = Image.open(os.path.join(ASSETS_DIR, "arc_seg", accent_key, "6.png"))
    canvas.alpha_composite(seg_img, (120, 32))

    # Battery row
    bat_icon = Image.open(os.path.join(ASSETS_DIR, "icons", "battery", accent_key, "2.png"))
    canvas.alpha_composite(bat_icon, (176, 76))
    font_bat = ImageFont.truetype(FONT_SEGOE_BOLD, 30)
    d.text((234, 70), "64%", font=font_bat, fill=(*CREAM_RGB, 255))

    # Weather + Date row
    w_icon = Image.open(os.path.join(ASSETS_DIR, "icons", "weather", "28.png"))
    canvas.alpha_composite(w_icon, (100, 124))
    font_sub = ImageFont.truetype(FONT_SEGOE_BOLD, 28)
    d.text((144, 123), "8°", font=font_sub, fill=(*CREAM_RGB, 255))
    d.line([202, 124, 202, 152], fill=(*c_acc[2], 255), width=2)
    d.text((222, 123), "DOM", font=font_sub, fill=(*c_acc[2], 255))
    d.text((296, 123), "08 NOV", font=font_sub, fill=(*CREAM_RGB, 255))

    # Centered Time 10:09
    mset = metrics["normal"]
    digits = [("1", "cream"), ("0", "cream"), (":", "cream"), ("0", digit_key), ("9", digit_key)]
    gap_d = 8
    gap_c = 12
    total_w = mset["1"]["w"] + gap_d + mset["0"]["w"] + gap_c + mset[":"]["w"] + gap_c + mset["0"]["w"] + gap_d + mset["9"]["w"]
    cur_x = round((480 - total_w) / 2)
    time_y = 178
    for idx, (ch, ckey) in enumerate(digits):
        fname = "colon.png" if ch == ":" else f"{ch}.png"
        gim = Image.open(os.path.join(ASSETS_DIR, "clock", ckey, fname))
        canvas.alpha_composite(gim, (cur_x, time_y))
        cur_x += gim.width + (gap_c if idx in (1, 2) else gap_d)

    # Chamfered boxes labels & values
    font_lbl = ImageFont.truetype(FONT_SEGOE_BOLD, 19)
    font_val = ImageFont.truetype(FONT_SEGOE_BOLD, 32)
    centers = [109, 191, 289, 371]
    items = [("HRV", "66"), ("RHR", "44"), ("BIO", "55"), ("PAI", "84")]
    for cx_col, (lbl, val) in zip(centers, items):
        lb = d.textbbox((0, 0), lbl, font=font_lbl)
        d.text((cx_col - (lb[2] - lb[0]) // 2, 300), lbl, font=font_lbl, fill=(*c_acc[2], 255))
        vb = d.textbbox((0, 0), val, font=font_val)
        d.text((cx_col - (vb[2] - vb[0]) // 2, 317), val, font=font_val, fill=(*CREAM_RGB, 255))

    # Bottom HR + sparkline
    heart = Image.open(os.path.join(ASSETS_DIR, "icons", "heart.png"))
    canvas.alpha_composite(heart, (194, 368))
    d.text((236, 363), "47", font=font_val, fill=(*CREAM_RGB, 255))

    spark_pts = [
        (162, 418), (173, 412), (184, 417), (195, 408), (206, 415),
        (217, 412), (228, 419), (239, 417), (250, 410), (261, 418),
        (272, 414), (283, 409), (294, 415), (305, 418), (318, 416),
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
    generate_segmented_arcs()
    generate_icons()
    generate_backgrounds()
    generate_editor_assets()
    write_glyph_metrics_js(metrics)

    prev = render_composite_preview("amber", "cream", metrics, os.path.join(ARTIFACT_DIR, "preview_tactical_amber.png"))
    prev.resize((324, 324), Image.Resampling.LANCZOS).save(os.path.join(ASSETS_DIR, "icon.png"))
    print("Tactical Amber assets generated successfully!")


if __name__ == "__main__":
    main()
