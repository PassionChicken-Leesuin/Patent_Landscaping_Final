from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_OVERALL = ROOT / "research_overall_framework.png"
OUT_MAS = ROOT / "mas_framework.png"

W, H = 1920, 1080

FONT_REG = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")
FONT_LIGHT = Path(r"C:\Windows\Fonts\malgunsl.ttf")

COLORS = {
    "bg": "#F7FAFC",
    "panel": "#FFFFFF",
    "ink": "#1D2939",
    "muted": "#667085",
    "line": "#98A2B3",
    "soft_line": "#D0D5DD",
    "data": "#2F6FED",
    "snorkel": "#E85D75",
    "mas": "#009E8E",
    "downstream": "#F79009",
    "eval": "#7A5AF8",
    "guard": "#344054",
    "green_soft": "#E6F7F4",
    "blue_soft": "#EAF1FF",
    "pink_soft": "#FDECEF",
    "orange_soft": "#FFF3E0",
    "violet_soft": "#F1EDFF",
    "gray_soft": "#EEF2F6",
}


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    fp = FONT_BOLD if weight == "bold" else FONT_LIGHT if weight == "light" else FONT_REG
    return ImageFont.truetype(str(fp), size=size)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)
    return img, draw


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    if not text:
        return 0, 0
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=6)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> str:
    lines: list[str] = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            lines.append("")
            continue
        words = raw.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else f"{cur} {word}"
            if text_size(draw, trial, fnt)[0] <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            if text_size(draw, word, fnt)[0] <= max_w:
                cur = word
            else:
                piece = ""
                for ch in word:
                    trial_piece = piece + ch
                    if text_size(draw, trial_piece, fnt)[0] <= max_w:
                        piece = trial_piece
                    else:
                        if piece:
                            lines.append(piece)
                        piece = ch
                cur = piece
        if cur:
            lines.append(cur)
    return "\n".join(lines)


def rounded(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: str,
    outline: str = COLORS["soft_line"],
    width: int = 2,
    radius: int = 8,
):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    text: str,
    fill: str,
    ink: str = COLORS["ink"],
    outline: str | None = None,
    size: int = 24,
):
    draw.rounded_rectangle(xy, radius=8, fill=fill, outline=outline or fill, width=1)
    f = font(size, "bold")
    tw, th = text_size(draw, text, f)
    x1, y1, x2, y2 = xy
    draw.text(((x1 + x2 - tw) / 2, (y1 + y2 - th) / 2 - 2), text, font=f, fill=ink)


def card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    lines: Iterable[str],
    accent: str,
    fill: str = COLORS["panel"],
    label: str | None = None,
    title_size: int = 28,
    body_size: int = 20,
    label_fill: str | None = None,
):
    x1, y1, x2, y2 = xy
    rounded(draw, xy, fill=fill, outline=accent, width=3)
    draw.rounded_rectangle((x1, y1, x1 + 12, y2), radius=8, fill=accent)
    if label:
        pill(draw, (x1 + 24, y1 + 22, x1 + 112, y1 + 58), label, label_fill or accent, "#FFFFFF", size=20)
        tx = x1 + 128
    else:
        tx = x1 + 30
    draw.text((tx, y1 + 22), title, font=font(title_size, "bold"), fill=COLORS["ink"])
    by = y1 + 72
    for line in lines:
        text = wrap(draw, line, font(body_size), x2 - x1 - 58)
        draw.multiline_text((x1 + 30, by), text, font=font(body_size), fill=COLORS["muted"], spacing=4)
        by += text_size(draw, text, font(body_size))[1] + 9


def title_block(draw: ImageDraw.ImageDraw, title: str, subtitle: str, right_note: str | None = None):
    draw.text((72, 54), title, font=font(52, "bold"), fill=COLORS["ink"])
    draw.text((76, 122), subtitle, font=font(26), fill=COLORS["muted"])
    if right_note:
        pill(draw, (1370, 68, 1848, 118), right_note, "#E8EEF7", COLORS["guard"], "#CBD5E1", 22)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str = COLORS["line"],
    width: int = 5,
    label: str | None = None,
    label_offset: tuple[int, int] = (0, 0),
    dashed: bool = False,
):
    x1, y1 = start
    x2, y2 = end
    if dashed:
        draw_dashed_line(draw, start, end, color, width)
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 18
    p1 = (x2 - size * math.cos(ang - math.pi / 6), y2 - size * math.sin(ang - math.pi / 6))
    p2 = (x2 - size * math.cos(ang + math.pi / 6), y2 - size * math.sin(ang + math.pi / 6))
    draw.polygon([end, p1, p2], fill=color)
    if label:
        f = font(20, "bold")
        tw, th = text_size(draw, label, f)
        mx = (x1 + x2) / 2 + label_offset[0]
        my = (y1 + y2) / 2 + label_offset[1]
        draw.rounded_rectangle((mx - tw / 2 - 14, my - th / 2 - 8, mx + tw / 2 + 14, my + th / 2 + 8),
                               radius=8, fill="#FFFFFF", outline=COLORS["soft_line"], width=1)
        draw.text((mx - tw / 2, my - th / 2 - 2), label, font=f, fill=color)


def poly_arrow(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    color: str = COLORS["line"],
    width: int = 5,
    label: str | None = None,
    label_xy: tuple[int, int] | None = None,
    dashed: bool = False,
):
    for a, b in zip(points[:-2], points[1:-1]):
        if dashed:
            draw_dashed_line(draw, a, b, color, width)
        else:
            draw.line((*a, *b), fill=color, width=width)
    arrow(draw, points[-2], points[-1], color=color, width=width, dashed=dashed)
    if label and label_xy:
        f = font(20, "bold")
        tw, th = text_size(draw, label, f)
        x, y = label_xy
        draw.rounded_rectangle((x - 14, y - 8, x + tw + 14, y + th + 8),
                               radius=8, fill="#FFFFFF", outline=COLORS["soft_line"], width=1)
        draw.text((x, y - 2), label, font=f, fill=color)


def draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    width: int,
    dash: int = 18,
    gap: int = 12,
):
    x1, y1 = start
    x2, y2 = end
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist == 0:
        return
    dx = (x2 - x1) / dist
    dy = (y2 - y1) / dist
    pos = 0.0
    while pos < dist:
        end_pos = min(pos + dash, dist)
        draw.line(
            (x1 + dx * pos, y1 + dy * pos, x1 + dx * end_pos, y1 + dy * end_pos),
            fill=color,
            width=width,
        )
        pos += dash + gap


def footer_band(draw: ImageDraw.ImageDraw, text: str):
    rounded(draw, (72, 945, 1848, 1034), fill="#FFFFFF", outline="#CBD5E1", width=2)
    f = font(23, "bold")
    wrapped = wrap(draw, text, f, 1708)
    _, th = text_size(draw, wrapped, f)
    draw.multiline_text((104, 945 + (89 - th) / 2 - 2), wrapped, font=f, fill=COLORS["guard"], spacing=5)


def build_overall():
    img, draw = canvas()
    title_block(
        draw,
        "연구 전체 Framework",
        "Autonomous-driving patent landscaping: Snorkel vs MAS weak-supervision comparison",
        "Controlled: labeler만 변경",
    )

    # Input stack
    card(draw, (70, 210, 390, 352), "Candidate Pool", [
        "Training_Set.csv",
        "6,195 unlabeled patents",
    ], COLORS["data"], fill=COLORS["blue_soft"], title_size=27)
    card(draw, (70, 410, 390, 552), "Gold Benchmark", [
        "Evaluation_Set.csv",
        "1,208 gold rows - test only",
    ], COLORS["eval"], fill=COLORS["violet_soft"], title_size=27)
    card(draw, (70, 610, 390, 752), "OOD Negatives", [
        "5 domains, 6,296 rows",
        "fixed NOT_SEED pool",
    ], COLORS["guard"], fill=COLORS["gray_soft"], title_size=27)

    card(draw, (430, 350, 730, 572), "Preprocess", [
        "Title + Abstract only",
        "remove 56 leakage cases",
        "clean pool = 6,139",
    ], COLORS["data"], fill="#FFFFFF")

    # Labeling lanes
    rounded(draw, (780, 210, 1186, 780), fill="#FFFFFF", outline="#CBD5E1", width=2)
    draw.text((810, 230), "Two pseudo-labeling arms", font=font(26, "bold"), fill=COLORS["ink"])
    draw.text((810, 265), "same candidate pool, different labeler", font=font(20), fill=COLORS["muted"])
    card(draw, (820, 315, 1148, 477), "Snorkel Arm", [
        "LFs + LabelModel",
        "label: 1 / 0 / ABSTAIN",
    ], COLORS["snorkel"], fill=COLORS["pink_soft"], label="A", title_size=27, body_size=20)
    card(draw, (820, 560, 1148, 722), "MAS Arm", [
        "rubric-guided agents",
        "score + candidate_type",
    ], COLORS["mas"], fill=COLORS["green_soft"], label="B", title_size=27, body_size=20)

    card(draw, (1235, 384, 1538, 640), "Shared Train Assembly", [
        "arm positives + in-pool negatives",
        "fixed OOD negatives",
        "equal-N + hard-negative ablation",
    ], COLORS["downstream"], fill=COLORS["orange_soft"], title_size=26, body_size=20)

    card(draw, (1610, 320, 1848, 480), "Fixed Downstream", [
        "SciBERT fine-tune",
        "same recipe",
        "same split logic",
    ], COLORS["downstream"], fill="#FFFFFF", title_size=25, body_size=20)
    card(draw, (1610, 610, 1848, 770), "Gold Evaluation", [
        "Macro-F1, Precision",
        "Recall, AUC",
        "by expansion level",
    ], COLORS["eval"], fill="#FFFFFF", title_size=25, body_size=20)

    # Arrows
    arrow(draw, (390, 281), (430, 430), COLORS["data"], label="candidate", label_offset=(-12, -40))
    arrow(draw, (730, 430), (820, 396), COLORS["snorkel"], label="Arm A", label_offset=(0, -42))
    arrow(draw, (730, 492), (820, 641), COLORS["mas"], label="Arm B", label_offset=(-4, 38))
    arrow(draw, (1148, 396), (1235, 468), COLORS["snorkel"])
    arrow(draw, (1148, 641), (1235, 552), COLORS["mas"])
    arrow(draw, (1538, 512), (1610, 400), COLORS["downstream"])
    arrow(draw, (1729, 480), (1729, 610), COLORS["downstream"])
    poly_arrow(draw, [(390, 681), (760, 681), (760, 805), (1185, 805), (1235, 590)],
               COLORS["guard"], label="fixed negatives", label_xy=(535, 775))
    poly_arrow(draw, [(390, 481), (505, 865), (1540, 865), (1729, 770)],
               COLORS["eval"], width=4, dashed=True,
               label="gold never enters labelers", label_xy=(840, 858))

    footer_band(
        draw,
        "Research question: Does MAS pseudo-labeling outperform Snorkel when candidate pool, negative pool, downstream model, gold test set, and metrics are fixed?",
    )
    img.save(OUT_OVERALL, quality=95)


def build_mas():
    img, draw = canvas()
    title_block(
        draw,
        "MAS Framework",
        "LangGraph-style pseudo-labeling pipeline for autonomous-driving patents",
        "No gold input",
    )

    card(draw, (70, 215, 390, 360), "Inputs", [
        "clean pool: 6,139 patents",
        "Title + Abstract",
    ], COLORS["data"], fill=COLORS["blue_soft"])
    card(draw, (70, 415, 390, 590), "Static Rubric", [
        "autonomous_driving_v2",
        "automate vs assist",
        "fixed thresholds",
    ], COLORS["mas"], fill=COLORS["green_soft"])
    card(draw, (70, 645, 390, 795), "Parallel Runner", [
        "10 keys, round-robin",
        "ThreadPool + retries",
        "temperature = 0",
    ], COLORS["guard"], fill=COLORS["gray_soft"])

    rounded(draw, (450, 210, 1418, 815), fill="#FFFFFF", outline="#CBD5E1", width=2)
    draw.text((485, 235), "Per-patent execution graph", font=font(30, "bold"), fill=COLORS["ink"])
    draw.text((485, 275), "usually 1 LLM call; only boundary or hard-negative candidates escalate", font=font(22), fill=COLORS["muted"])

    pill(draw, (500, 390, 615, 438), "START", COLORS["blue_soft"], COLORS["data"], "#C7D7FE", 23)
    card(draw, (675, 330, 1035, 526), "Relevance + Route", [
        "fast LLM evidence extraction",
        "core_score + route",
    ], COLORS["data"], fill=COLORS["blue_soft"], label="A", title_size=26, body_size=20)
    card(draw, (785, 615, 1125, 773), "Exclusion Check", [
        "only boundary / hard cases",
        "exclusion stance + risk",
    ], COLORS["snorkel"], fill=COLORS["pink_soft"], label="B", title_size=26, body_size=20)
    card(draw, (1170, 330, 1392, 526), "C. Score + Type", [
        "deterministic scoring",
        "hard-negative cap + type flag",
    ], COLORS["mas"], fill=COLORS["green_soft"], title_size=24, body_size=18)
    pill(draw, (1232, 625, 1338, 673), "END", COLORS["green_soft"], COLORS["mas"], "#B7E9E1", 23)

    arrow(draw, (615, 414), (675, 414), COLORS["data"])
    arrow(draw, (1035, 410), (1170, 410), COLORS["data"], label="easy routes", label_offset=(0, -42))
    poly_arrow(draw, [(918, 526), (918, 585), (955, 615)], COLORS["snorkel"], label="boundary / hard_negative", label_xy=(704, 555))
    poly_arrow(draw, [(1125, 694), (1270, 694), (1270, 526)], COLORS["snorkel"])
    arrow(draw, (1270, 526), (1270, 625), COLORS["mas"])

    card(draw, (1485, 235, 1848, 430), "Ranked Output", [
        "mas_ranked_scores.csv",
        "rank + score + candidate_type",
        "sorted by final_score",
    ], COLORS["mas"], fill="#FFFFFF", title_size=26, body_size=20)
    card(draw, (1485, 485, 1848, 640), "Audit Log", [
        "mas_audit.jsonl",
        "route, evidence, exclusion",
        "full per-patent state",
    ], COLORS["guard"], fill="#FFFFFF", title_size=26, body_size=20)
    card(draw, (1485, 695, 1848, 855), "Downstream Mapping", [
        "positive -> SEED",
        "negative types -> NOT_SEED",
        "boundary / abstain dropped",
    ], COLORS["downstream"], fill=COLORS["orange_soft"], title_size=26, body_size=20)

    arrow(draw, (1392, 410), (1485, 332), COLORS["mas"])
    arrow(draw, (1392, 458), (1485, 562), COLORS["guard"], width=4)
    poly_arrow(draw, [(1666, 430), (1875, 430), (1875, 695), (1666, 695)], COLORS["downstream"])

    # Rubric and runner influence arrows
    poly_arrow(draw, [(390, 502), (585, 502), (675, 380)], COLORS["mas"], width=4, dashed=True,
               label="rubric injected", label_xy=(475, 470))
    poly_arrow(draw, [(390, 720), (585, 720), (675, 486)], COLORS["guard"], width=4, dashed=True,
               label="parallel tasks", label_xy=(470, 692))
    arrow(draw, (390, 287), (500, 414), COLORS["data"], width=5)

    footer_band(
        draw,
        "Guardrails: Evaluation_Set is never seen by MAS; thresholds are fixed, not gold-tuned; temperature = 0; CSV is slim output and JSONL is the audit trail.",
    )
    img.save(OUT_MAS, quality=95)


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    build_overall()
    build_mas()
    print(OUT_OVERALL)
    print(OUT_MAS)
