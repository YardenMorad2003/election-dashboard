"""Generate mcp/logo.png (512x512) — app icon for the MCP connector listing.

Flat mark: slate-navy rounded square, ivory results-chart bars with one
accent bar, echoing the dashboard's Slate identity.
"""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 512
NAVY = (31, 51, 82)        # slate navy background
IVORY = (245, 241, 232)    # bars
ACCENT = (127, 179, 213)   # leading-party bar
BASELINE = (245, 241, 232, 90)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, SIZE, SIZE], radius=100, fill=NAVY)

# results chart: five descending bars, tallest accented
heights = [236, 176, 132, 96, 64]
bar_w, gap = 56, 24
total_w = len(heights) * bar_w + (len(heights) - 1) * gap
x = (SIZE - total_w) // 2
base_y = 396
for i, h in enumerate(heights):
    color = ACCENT if i == 0 else IVORY
    d.rounded_rectangle([x, base_y - h, x + bar_w, base_y],
                        radius=14, fill=color)
    x += bar_w + gap

# baseline
line = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
ImageDraw.Draw(line).rounded_rectangle(
    [(SIZE - total_w) // 2 - 8, base_y + 22,
     (SIZE + total_w) // 2 + 8, base_y + 34],
    radius=6, fill=BASELINE)
img = Image.alpha_composite(img, line)

out = Path(__file__).resolve().parent / "logo.png"
img.save(out)
print(f"wrote {out} ({out.stat().st_size} bytes)")
