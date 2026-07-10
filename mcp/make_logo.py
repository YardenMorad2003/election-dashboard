"""Generate the MCP connector icons.

  mcp/logo.png        1024x1024  main listing icon
  mcp/logo_small.png  256x256    composer icon (bolder 3-bar variant)

Both are full-bleed RGB squares (no alpha, no baked corner rounding —
directories apply their own mask) rendered 4x supersampled for smooth
edges. Motif: pill-shaped descending results bars on a navy gradient,
echoing the dashboard's Slate identity.
"""

from pathlib import Path

from PIL import Image, ImageDraw

SS = 4  # supersample factor
TOP = (30, 52, 80)      # gradient top
BOTTOM = (15, 26, 44)   # gradient bottom
IVORY = (242, 238, 230)
ACCENT = (127, 183, 224)


def gradient_square(px):
    img = Image.new("RGB", (px, px))
    d = ImageDraw.Draw(img)
    for y in range(px):
        t = y / (px - 1)
        d.line([(0, y), (px, y)], fill=tuple(
            round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))
    return img, d


def draw_bars(d, px, heights, bar_w, gap, base_y):
    n = len(heights)
    total = n * bar_w + (n - 1) * gap
    x = (px - total) / 2
    for i, h in enumerate(heights):
        d.rounded_rectangle(
            [x, base_y - h, x + bar_w, base_y],
            radius=bar_w / 2,
            fill=ACCENT if i == 0 else IVORY)
        x += bar_w + gap


def render(out_px, heights, bar_w_f, gap_f, base_f):
    px = out_px * SS
    img, d = gradient_square(px)
    draw_bars(d, px, [h * px for h in heights],
              bar_w_f * px, gap_f * px, base_f * px)
    return img.resize((out_px, out_px), Image.LANCZOS)


HERE = Path(__file__).resolve().parent

# main icon: four descending pill bars
render(1024, heights=(0.52, 0.39, 0.285, 0.20),
       bar_w_f=0.125, gap_f=0.062, base_f=0.79).save(HERE / "logo.png")

# composer icon: three bolder bars, larger margins survive small display
render(256, heights=(0.54, 0.38, 0.25),
       bar_w_f=0.175, gap_f=0.085, base_f=0.78).save(HERE / "logo_small.png")

for name in ("logo.png", "logo_small.png"):
    p = HERE / name
    with Image.open(p) as im:
        print(f"{name}: {im.size[0]}x{im.size[1]} {im.mode}, "
              f"{p.stat().st_size} bytes")
