from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

from generate_paper_draft import (
    ABSTRACT,
    AUTHORS,
    AFFILIATION,
    DATASET_ROWS,
    LABEL_DIAGNOSTICS,
    PERFORMANCE_ROWS,
    REFERENCES,
    SECTIONS,
    TITLE,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "A_Multi_Agent_Weak_Supervision_Framework_for_Domain_Relevant_Patent_Identification_latex_style.pdf"
FONTS = ROOT / "paper" / "fonts"
FIG_OVERALL_BW = ROOT / "figures" / "research_overall_framework_bw.png"
FIG_MAS_BW = ROOT / "figures" / "mas_framework_bw.png"


def register_fonts() -> tuple[str, str, str]:
    """Register Computer Modern Unicode fonts if available; fall back to Times."""
    font_sets = [
        (
            FONTS / "cmu_ttf" / "cm-unicode-0.7.0" / "cmunrm.ttf",
            FONTS / "cmu_ttf" / "cm-unicode-0.7.0" / "cmunbx.ttf",
            FONTS / "cmu_ttf" / "cm-unicode-0.7.0" / "cmunti.ttf",
        ),
        (FONTS / "cmunrm.otf", FONTS / "cmunbx.otf", FONTS / "cmunti.otf"),
    ]
    for regular, bold, italic in font_sets:
        try:
            pdfmetrics.registerFont(TTFont("CMU", str(regular)))
            pdfmetrics.registerFont(TTFont("CMU-Bold", str(bold)))
            pdfmetrics.registerFont(TTFont("CMU-Italic", str(italic)))
            return "CMU", "CMU-Bold", "CMU-Italic"
        except Exception:
            continue
    return "Times-Roman", "Times-Bold", "Times-Italic"


FONT, BOLD, ITALIC = register_fonts()


def clean(s: str) -> str:
    replacements = {
        "allenai/scibert_scivocab_uncased": "allenai/scibert-scivocab-uncased",
        "abstain_candidate": "abstain candidate",
        "easy_positive": "easy positive",
        "easy_negative": "easy negative",
        "hard_negative": "hard negative",
        "candidate_type": "candidate type",
        "NOT_SEED": "NOT-SEED",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def on_page(canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.saveState()
    canvas.setFont(FONT, 10)
    canvas.drawCentredString(letter[0] / 2, 0.45 * inch, str(page_num))
    if page_num == 1:
        canvas.setFont(FONT, 20)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.translate(0.38 * inch, 5.5 * inch)
        canvas.rotate(90)
        canvas.drawCentredString(0, 0, "Working draft | June 2026")
    canvas.restoreState()


def styles():
    _ = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            fontName=FONT,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=22,
        ),
        "author": ParagraphStyle(
            "author",
            fontName=FONT,
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "affil": ParagraphStyle(
            "affil",
            fontName=FONT,
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=22,
        ),
        "abstract_heading": ParagraphStyle(
            "abstract_heading",
            fontName=BOLD,
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "abstract": ParagraphStyle(
            "abstract",
            fontName=FONT,
            fontSize=10.5,
            leading=12.8,
            alignment=TA_JUSTIFY,
            firstLineIndent=0,
            spaceAfter=15,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=FONT,
            fontSize=10.5,
            leading=13,
            alignment=TA_JUSTIFY,
            firstLineIndent=0,
            spaceAfter=9,
        ),
        "section": ParagraphStyle(
            "section",
            fontName=BOLD,
            fontSize=17,
            leading=21,
            alignment=TA_LEFT,
            spaceBefore=16,
            spaceAfter=12,
        ),
        "subsection": ParagraphStyle(
            "subsection",
            fontName=BOLD,
            fontSize=13,
            leading=16,
            alignment=TA_LEFT,
            spaceBefore=13,
            spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName=FONT,
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "ref": ParagraphStyle(
            "ref",
            fontName=FONT,
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            leftIndent=18,
            firstLineIndent=-18,
            spaceAfter=5,
        ),
    }


S = styles()


def p(text: str, style="body") -> Paragraph:
    return Paragraph(clean(text), S[style])


def figure_block(caption: str, image_path: Path, width_in: float = 6.45) -> list:
    with PILImage.open(image_path) as img:
        width, height = img.size
    draw_width = width_in * inch
    draw_height = draw_width * height / width
    figure = RLImage(str(image_path), width=draw_width, height=draw_height, hAlign="CENTER")
    return [
        KeepTogether(
            [
                figure,
                Paragraph(clean(caption), S["caption"]),
                Spacer(1, 8),
            ]
        )
    ]


def title_block() -> list:
    return [
        Spacer(1, 0.7 * inch),
        Paragraph(clean(TITLE), S["title"]),
        Paragraph(clean(AUTHORS), S["author"]),
        Paragraph(clean(AFFILIATION), S["affil"]),
        Paragraph("Abstract", S["abstract_heading"]),
        Paragraph(clean(ABSTRACT), S["abstract"]),
    ]


def booktabs_table(caption: str, headers: list[str], rows: list[list[str]], widths: list[float]) -> list:
    data = [headers] + rows
    table = Table(data, colWidths=[w * inch for w in widths], repeatRows=1, hAlign="CENTER")
    style = TableStyle(
        [
            ("FONT", (0, 0), (-1, -1), FONT, 9.4),
            ("FONT", (0, 0), (-1, 0), FONT, 9.4),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 0.45, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ]
    )
    table.setStyle(style)
    return [Paragraph(clean(caption), S["caption"]), table, Spacer(1, 12)]


def dataset_table() -> list:
    return booktabs_table(
        "Table 1: Gold evaluation sets and in-domain labeling candidate pools.",
        ["Domain", "SEED", "NOT-SEED", "Gold N", "Labeling Pool N"],
        [[r[0], f"{r[1]:,}", f"{r[2]:,}", f"{r[3]:,}", f"{r[4]:,}"] for r in DATASET_ROWS],
        [2.35, 0.72, 0.9, 0.82, 1.16],
    )


def labeling_table() -> list:
    return booktabs_table(
        "Table 2: In-domain label distribution and OOD false positives. MAS negatives combine easy_negative and hard_negative; Snorkel negatives are NOT_SEED labels.",
        ["Domain", "Labeler", "Positive", "Negative", "Boundary / Abstain", "OOD FP"],
        [[r[0], r[1], f"{r[2]:,}", f"{r[3]:,}", f"{r[4]:,}", f"{r[5]:,}"] for r in LABEL_DIAGNOSTICS],
        [2.15, 0.72, 0.85, 0.85, 1.1, 0.66],
    )


def performance_table() -> list:
    return booktabs_table(
        "Table 3: SciBERT evaluation on held-out gold benchmarks at threshold 0.5.",
        ["Domain", "Labeler", "AUC", "Macro-F1", "Recall", "Precision", "Accuracy"],
        [[r[0], r[1], f"{r[2]:.3f}", f"{r[3]:.3f}", f"{r[4]:.3f}", f"{r[5]:.3f}", f"{r[6]:.3f}"] for r in PERFORMANCE_ROWS],
        [1.95, 0.65, 0.62, 0.78, 0.68, 0.78, 0.72],
    )


def build_story() -> list:
    story = title_block()

    # Introduction through Methods.
    for section_idx, (heading, paragraphs) in enumerate(SECTIONS[:3]):
        story.append(Paragraph(clean(heading), S["section"]))
        for paragraph in paragraphs:
            story.append(p(paragraph))
        if section_idx == 0:
            story.extend(
                figure_block(
                    "Figure 1: Overall controlled framework for comparing Snorkel and MAS weak supervision in domain-relevant patent identification.",
                    FIG_OVERALL_BW,
                )
            )
        if section_idx == 2:
            story.extend(
                figure_block(
                    "Figure 2: MAS labeling framework. Node A extracts relevance evidence and routes the patent; Node B checks boundary and hard-negative exclusions; Node C deterministically maps the structured state to a pseudo-label.",
                    FIG_MAS_BW,
                )
            )

    # Results with tables interleaved in the same order as the paper narrative.
    heading, paragraphs = SECTIONS[3]
    story.append(Paragraph(clean(heading), S["section"]))
    for paragraph in paragraphs:
        story.append(p(paragraph))
    story.append(Paragraph("4.1 Dataset Scale", S["subsection"]))
    story.extend(dataset_table())
    story.append(Paragraph("4.2 Labeling Diagnostics", S["subsection"]))
    story.extend(labeling_table())
    story.append(Paragraph("4.3 Downstream Performance", S["subsection"]))
    story.extend(performance_table())

    for heading, paragraphs in SECTIONS[4:]:
        story.append(Paragraph(clean(heading), S["section"]))
        for paragraph in paragraphs:
            story.append(p(paragraph))

    story.append(Paragraph("References", S["section"]))
    for ref in REFERENCES:
        story.append(Paragraph(clean(ref), S["ref"]))
    return story


def build_pdf():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=0.78 * inch,
        bottomMargin=0.75 * inch,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    doc.build(build_story())
    print(OUT)


if __name__ == "__main__":
    build_pdf()
