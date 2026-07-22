from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "figures"
FONT_DIR = ROOT / "paper" / "fonts" / "cmu_ttf" / "cm-unicode-0.7.0"

OUT_OVERALL = OUT_DIR / "research_overall_framework_bw.png"
OUT_MAS = OUT_DIR / "mas_framework_bw.png"

W, H = 2400, 1160

INK = "#111111"
MID = "#555555"
LIGHT = "#E8E8E8"
LIGHTER = "#F6F6F6"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    if bold:
        name = "cmunbx.ttf"
    elif italic:
        name = "cmunti.ttf"
    else:
        name = "cmunrm.ttf"
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size=size)
    fallback = Path(r"C:\Windows\Fonts\times.ttf")
    return ImageFont.truetype(str(fallback), size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=8)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> str:
    lines: list[str] = []
    for raw in text.split("\n"):
        words = raw.split()
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if text_size(draw, trial, fnt)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return "\n".join(lines)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)
    return img, draw


def rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: str = WHITE,
    outline: str = INK,
    width: int = 3,
):
    draw.rectangle(xy, fill=fill, outline=outline, width=width)


def dashed_rect(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], dash: int = 18, gap: int = 12):
    x1, y1, x2, y2 = xy
    dashed_line(draw, (x1, y1), (x2, y1), dash=dash, gap=gap)
    dashed_line(draw, (x2, y1), (x2, y2), dash=dash, gap=gap)
    dashed_line(draw, (x2, y2), (x1, y2), dash=dash, gap=gap)
    dashed_line(draw, (x1, y2), (x1, y1), dash=dash, gap=gap)


def dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str = INK,
    width: int = 3,
    dash: int = 22,
    gap: int = 14,
):
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end_pos = min(pos + dash, length)
        draw.line(
            (x1 + dx * pos, y1 + dy * pos, x1 + dx * end_pos, y1 + dy * end_pos),
            fill=fill,
            width=width,
        )
        pos += dash + gap


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str = INK,
    width: int = 4,
    dashed: bool = False,
):
    if dashed:
        dashed_line(draw, start, end, fill=fill, width=width)
    else:
        draw.line((*start, *end), fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 22
    p1 = (x2 - size * math.cos(angle - math.pi / 6), y2 - size * math.sin(angle - math.pi / 6))
    p2 = (x2 - size * math.cos(angle + math.pi / 6), y2 - size * math.sin(angle + math.pi / 6))
    draw.polygon([end, p1, p2], fill=fill)


def poly_arrow(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: str = INK, width: int = 4):
    for a, b in zip(points[:-2], points[1:-1]):
        draw.line((*a, *b), fill=fill, width=width)
    arrow(draw, points[-2], points[-1], fill=fill, width=width)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int = 34, bold: bool = True):
    draw.text(xy, text, font=font(size, bold=bold), fill=INK)


def small_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str):
    draw.text(xy, text, font=font(26, italic=True), fill=MID)


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    body: str,
    fill: str = WHITE,
    title_size: int = 34,
    body_size: int = 25,
    align: str = "center",
):
    x1, y1, x2, y2 = xy
    rect(draw, xy, fill=fill)
    title_font = font(title_size, bold=True)
    body_font = font(body_size)
    title_wrapped = wrap(draw, title, title_font, x2 - x1 - 56)
    body_wrapped = wrap(draw, body, body_font, x2 - x1 - 56)
    tw, th = text_size(draw, title_wrapped, title_font)
    bw, bh = text_size(draw, body_wrapped, body_font)
    total = th + 18 + bh
    y = y1 + (y2 - y1 - total) // 2 - 2
    x_title = x1 + (x2 - x1 - tw) // 2 if align == "center" else x1 + 30
    x_body = x1 + (x2 - x1 - bw) // 2 if align == "center" else x1 + 30
    draw.multiline_text((x_title, y), title_wrapped, font=title_font, fill=INK, spacing=8, align=align)
    draw.multiline_text((x_body, y + th + 18), body_wrapped, font=body_font, fill=INK, spacing=8, align=align)


def section_band(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str):
    x1, y1, x2, y2 = xy
    rect(draw, xy, fill=LIGHTER, outline=INK, width=2)
    tw, th = text_size(draw, title, font(28, bold=True))
    draw.rectangle((x1 + 20, y1 - 20, x1 + tw + 52, y1 + 28), fill=WHITE)
    draw.text((x1 + 36, y1 - 13), title, font=font(28, bold=True), fill=INK)


def build_overall():
    img, draw = canvas()
    label(draw, (105, 62), "Overall Research Framework", 44)
    small_label(draw, (105, 118), "Only the weak-supervision labeler changes; downstream model and evaluation are held fixed.")

    section_band(draw, (80, 190, 2320, 1070), "Controlled experimental pipeline")

    box(
        draw,
        (135, 270, 500, 470),
        "Domain setup",
        "Six technology domains\nCPC prefix and keyword query\ngold positives / negatives",
        fill=LIGHTER,
    )
    box(
        draw,
        (135, 600, 500, 800),
        "Candidate pool",
        "Title and abstract records\nin-domain candidates plus\nOOD gold examples",
        fill=WHITE,
    )
    arrow(draw, (318, 470), (318, 600))

    box(
        draw,
        (675, 265, 1135, 505),
        "Snorkel arm",
        "Domain labeling functions\nLabelModel aggregation\nSEED / NOT-SEED / abstain",
        fill=WHITE,
    )
    box(
        draw,
        (675, 625, 1135, 865),
        "MAS arm",
        "Rubric-guided agents\nrelevance, exclusion, scoring\npositive / negative / abstain",
        fill=LIGHT,
    )

    poly_arrow(draw, [(500, 370), (595, 370), (595, 385), (675, 385)])
    poly_arrow(draw, [(500, 700), (595, 700), (595, 745), (675, 745)])
    dashed_line(draw, (595, 370), (595, 745), fill=MID, width=3)

    box(
        draw,
        (1320, 320, 1705, 510),
        "Training data",
        "Binary pseudo-labels\nsame mapping protocol\nsame train / validation split",
        fill=WHITE,
    )
    box(
        draw,
        (1320, 630, 1705, 820),
        "SciBERT classifier",
        "SciBERT encoder\n4 epochs; max length 256\nclass-weighted loss",
        fill=WHITE,
    )
    arrow(draw, (1135, 385), (1320, 415))
    arrow(draw, (1135, 745), (1320, 725))
    arrow(draw, (1512, 510), (1512, 630))

    box(
        draw,
        (1900, 445, 2265, 705),
        "Gold evaluation",
        "Held-out domain benchmark\nAUC, Macro-F1, recall,\nprecision, accuracy",
        fill=LIGHTER,
    )
    arrow(draw, (1705, 725), (1900, 575))

    draw.line((1220, 240, 1220, 930), fill=INK, width=3)
    draw.text((1176, 940), "labeler outputs", font=font(24, italic=True), fill=MID)
    draw.text((1452, 900), "fixed downstream training", font=font(24, italic=True), fill=MID)
    draw.text((1905, 765), "fair comparison", font=font(24, italic=True), fill=MID)

    img.save(OUT_OVERALL, dpi=(300, 300))


def build_mas():
    img, draw = canvas()
    label(draw, (105, 62), "MAS Weak-Supervision Labeling Framework", 44)
    small_label(draw, (105, 118), "Structured agents create auditable pseudo-labels for patent relevance.")

    box(
        draw,
        (95, 310, 455, 535),
        "Inputs",
        "Patent title and abstract\nDomain rubric\nKeyword and exclusion cues",
        fill=LIGHTER,
    )

    box(
        draw,
        (650, 220, 1105, 470),
        "Node A\nRelevance and Route",
        "Extract functional evidence\nscore domain relevance\nroute case type",
        fill=WHITE,
    )
    box(
        draw,
        (650, 690, 1105, 940),
        "Node B\nConditional Exclusion",
        "Run only for boundary or\nhard-negative cases\ncheck look-alike patents",
        fill=LIGHTER,
    )
    box(
        draw,
        (1320, 455, 1775, 705),
        "Node C\nDeterministic Scoring",
        "Combine scores and flags\nassign final candidate type\napply abstain / drop rules",
        fill=WHITE,
    )
    box(
        draw,
        (1945, 330, 2290, 830),
        "Outputs",
        "pseudo-label\nconfidence score\ncandidate type\nrationale\nevidence spans",
        fill=LIGHTER,
    )

    arrow(draw, (455, 423), (650, 345))
    arrow(draw, (1105, 345), (1320, 550))
    poly_arrow(draw, [(905, 470), (905, 585), (905, 690)])
    poly_arrow(draw, [(1105, 815), (1200, 815), (1200, 610), (1320, 610)])
    arrow(draw, (1775, 580), (1945, 580))

    dashed_rect(draw, (590, 170, 1840, 990))
    draw.rectangle((690, 1000, 1740, 1070), fill=WHITE, outline=INK, width=2)
    draw.text(
        (727, 1017),
        "candidate type = positive | easy neg. | hard neg. | boundary | abstain",
        font=font(28),
        fill=INK,
    )

    draw.text((705, 518), "easy cases", font=font(25, italic=True), fill=MID)
    draw.text((728, 640), "boundary / hard-negative route", font=font(25, italic=True), fill=MID)
    draw.text((1350, 735), "mapping to final label", font=font(25, italic=True), fill=MID)

    img.save(OUT_MAS, dpi=(300, 300))


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_overall()
    build_mas()
    print(OUT_OVERALL)
    print(OUT_MAS)
