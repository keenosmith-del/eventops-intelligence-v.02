"""Reproducible PDF reports from the submitted Markdown source."""

import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

root = Path(__file__).resolve().parents[1]
output = root / "output/pdf"
output.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="ReportTitle",
        fontName="Helvetica",
        fontSize=29,
        leading=34,
        textColor=colors.HexColor("#292e25"),
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="ReportSubtitle",
        fontName="Helvetica",
        fontSize=18,
        leading=23,
        textColor=colors.HexColor("#606954"),
        spaceAfter=24,
    )
)
styles.add(
    ParagraphStyle(
        name="ReportHeading",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#454e3c"),
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="ReportBody",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        spaceAfter=10,
        textColor=colors.HexColor("#383e31"),
    )
)
styles.add(
    ParagraphStyle(
        name="ReportMeta",
        fontName="Helvetica",
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#878e7c"),
        spaceAfter=20,
    )
)


def text(value):
    value = (
        value.replace("—", "-").replace("–", "-").replace("→", " > ").replace("’", "'")
    )
    value = escape(value)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)


def frame(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#e0e4d8"))
    canvas.line(48, 45, width - 48, 45)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#89917e"))
    canvas.drawString(48, 30, "EVENTOPS INTELLIGENCE / TECHNICAL ASSESSMENT")
    canvas.drawRightString(width - 48, 30, str(doc.page))
    canvas.restoreState()


for source, filename in [
    ("technical-executive-brief.md", "technical-executive-brief.pdf"),
    (
        "engineering-design-and-implementation.md",
        "engineering-design-and-implementation.pdf",
    ),
]:
    raw = (root / "docs/submission" / source).read_text()
    story = []
    for block in raw.strip().split("\n\n"):
        lines = block.splitlines()
        if lines[0].startswith("# "):
            for line in lines:
                if line.startswith("# "):
                    story.append(Paragraph(text(line[2:]), styles["ReportTitle"]))
                elif line.startswith("## "):
                    story.append(Paragraph(text(line[3:]), styles["ReportSubtitle"]))
        elif block.startswith("### "):
            story.append(Paragraph(text(block[4:]), styles["ReportHeading"]))
        elif block.startswith("**"):
            story.append(Paragraph(text(block), styles["ReportMeta"]))
        else:
            story.append(
                Paragraph(text(block.replace("\n", " ")), styles["ReportBody"])
            )
    doc = SimpleDocTemplate(
        str(output / filename),
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=47,
        bottomMargin=65,
        title=source.replace(".md", "").replace("-", " ").title(),
        author="EventOps Intelligence",
    )
    doc.build(story, onFirstPage=frame, onLaterPages=frame)
    print(filename)
