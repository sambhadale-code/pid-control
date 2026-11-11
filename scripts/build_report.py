from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "final" / "PID_Control_Final.md"
OUTPUT = ROOT / "docs" / "final" / "PID_Control_Final.pdf"
CONTENT_WIDTH = A4[0] - 96


def inline_markup(text: str) -> str:
    text = re.sub(
        r"\\\((.+?)\\\)",
        lambda match: equation_text(match.group(1)),
        text,
    )
    text = html.escape(text, quote=False)
    text = re.sub(r"\^([0-9]+)", r"<sup>\1</sup>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#245b82">\1</link>',
        text,
    )
    return text


def equation_text(source: str) -> str:
    source = source.replace(
        r"\frac{e_k-e_{k-1}}{\Delta t}",
        "(e_k-e_(k-1))/Delta t",
    )
    substitutions = {
        r"\ddot{x}": "d2x/dt2",
        r"\dot{x}": "dx/dt",
        r"\Delta": " Delta ",
        r"\int": " integral ",
        r"\tau": "tau",
        r"\omega": "omega",
        r"\pi": "pi",
        r"\sqrt": "sqrt",
        r"\quad": "   ",
        r"\qquad": "   ",
        r"\Longrightarrow": " => ",
        r"\approx": " approx ",
        r"\max": "max",
        r"\,": " ",
        r"\ ": " ",
        r"\times": "*",
        r"\cdot": "*",
        r"\text": "",
        r"\left": "",
        r"\right": "",
    }
    for old, new in substitutions.items():
        source = source.replace(old, new)
    source = source.replace(r"\frac{e_k-e_{k-1}}{Delta t}", "(e_k-e_(k-1))/Delta t")
    source = source.replace(r"\frac{x_{max}-r}{|r|}", "(x_max-r)/|r|")
    source = source.replace(r"\frac{2pi}{omega_u}", "(2pi)/(omega_u)")
    source = source.replace(r"\frac{2pi}{sqrt3}", "(2pi)/(sqrt3)")
    source = re.sub(
        r"\\frac\{([^{}]*)\}\{([^{}]*)\}",
        lambda match: f"({match.group(1)})/({match.group(2)})",
        source,
    )
    source = source.replace(r"\;", " ")
    source = source.replace(r"\%", "%")
    source = re.sub(r"\^([23])", lambda match: {"2": "^2", "3": "^3"}[match.group(1)], source)
    source = re.sub(r"_\{([^{}]*)\}", r"_(\1)", source)
    source = source.replace("{", "").replace("}", "")
    return source.replace("\n", " ").strip()


def make_styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=30,
            textColor=colors.HexColor("#18354d"),
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )
    base.add(
        ParagraphStyle(
            name="Subtitle",
            parent=base["Normal"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#52606d"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    base.add(
        ParagraphStyle(
            name="Section",
            parent=base["Heading2"],
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#18354d"),
            spaceBefore=14,
            spaceAfter=7,
            keepWithNext=True,
        )
    )
    base.add(
        ParagraphStyle(
            name="Subsection",
            parent=base["Heading3"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#245b82"),
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
        )
    )
    base.add(
        ParagraphStyle(
            name="BodyCompact",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=13.2,
            spaceAfter=6,
        )
    )
    base.add(
        ParagraphStyle(
            name="Equation",
            parent=base["BodyText"],
            fontName="Courier",
            fontSize=9,
            leading=13,
            leftIndent=12,
            rightIndent=8,
            borderColor=colors.HexColor("#dce5eb"),
            borderWidth=0.5,
            borderPadding=6,
            backColor=colors.HexColor("#f5f8fa"),
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    base.add(
        ParagraphStyle(
            name="Caption",
            parent=base["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#52606d"),
            spaceAfter=8,
        )
    )
    base.add(
        ParagraphStyle(
            name="TableCell",
            parent=base["BodyText"],
            fontSize=8,
            leading=10,
            spaceAfter=0,
        )
    )
    base.add(
        ParagraphStyle(
            name="ListItem",
            parent=base["BodyText"],
            fontSize=9.3,
            leading=12.5,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        )
    )
    return base


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#dce5eb"))
    canvas.line(48, 34, A4[0] - 48, 34)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#657786"))
    canvas.drawString(48, 22, "PID Control | Internship Assignment")
    canvas.drawRightString(A4[0] - 48, 22, f"Page {document.page}")
    canvas.restoreState()


def build_story():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    styles = make_styles()
    story = []
    index = 0
    in_math = False
    math_lines: list[str] = []

    while index < len(lines):
        line = lines[index].strip()
        if not line or line == "---":
            index += 1
            continue

        if line.startswith(r"\["):
            in_math = True
            math_lines = [line.removeprefix(r"\[").strip()]
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(r"\]"):
                math_lines.append(lines[index].strip())
                index += 1
            if index < len(lines):
                math_lines.append(lines[index].strip().removeprefix(r"\]"))
            equation = equation_text(" ".join(math_lines))
            story.append(Paragraph(html.escape(equation), styles["Equation"]))
            in_math = False
            index += 1
            continue

        if line.startswith("```"):
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index].rstrip())
                index += 1
            story.append(
                Preformatted(
                    "\n".join(code_lines),
                    ParagraphStyle(
                        name=f"Code{index}",
                        fontName="Courier",
                        fontSize=8,
                        leading=10,
                        backColor=colors.HexColor("#f3f5f7"),
                        borderColor=colors.HexColor("#dce5eb"),
                        borderWidth=0.5,
                        borderPadding=6,
                    ),
                )
            )
            story.append(Spacer(1, 6))
            index += 1
            continue

        if line.startswith("# "):
            story.append(Paragraph(inline_markup(line[2:]), styles["ReportTitle"]))
            index += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), styles["Subsection"]))
            index += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), styles["Section"]))
            index += 1
            continue

        if line.startswith("!["):
            match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
            if match:
                image_path = (SOURCE.parent / match.group(2)).resolve()
                if not image_path.is_file():
                    raise FileNotFoundError(f"Report image not found: {image_path}")
                width, height = ImageReader(str(image_path)).getSize()
                scale = min((CONTENT_WIDTH - 8) / width, 3.7 * inch / height)
                image = Image(str(image_path), width=width * scale, height=height * scale)
                story.append(KeepTogether([image, Spacer(1, 3)]))
            index += 1
            continue

        if line.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            rows = [split_table_row(row) for row in table_lines]
            rows = [row for row in rows if not all(re.fullmatch(r":?-{3,}:?", c) for c in row)]
            table_data = [
                [
                    Paragraph(
                        f"<b>{inline_markup(cell)}</b>" if row_index == 0 else inline_markup(cell),
                        styles["TableCell"],
                    )
                    for cell in row
                ]
                for row_index, row in enumerate(rows)
            ]
            column_count = max(len(row) for row in table_data)
            widths = [CONTENT_WIDTH / column_count] * column_count
            table = Table(table_data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1f5")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#18354d")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5dc")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.extend([table, Spacer(1, 7)])
            continue

        if line.startswith("- "):
            story.append(
                Paragraph("- " + inline_markup(line[2:]), styles["ListItem"])
            )
            index += 1
            continue
        if re.match(r"^\d+\.\s", line):
            marker, content = line.split(".", 1)
            story.append(
                Paragraph(f"{marker}. {inline_markup(content.strip())}", styles["ListItem"])
            )
            index += 1
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            next_line = lines[index].strip()
            if (
                not next_line
                or next_line == "---"
                or next_line.startswith(("#", "|", "![", "```", "- "))
                or next_line.startswith(r"\[")
                or re.match(r"^\d+\.\s", next_line)
            ):
                break
            paragraph_lines.append(next_line)
            index += 1
        paragraph = " ".join(paragraph_lines)
        if paragraph.startswith("*") and paragraph.endswith("*"):
            paragraph = paragraph[1:-1]
            story.append(Paragraph(inline_markup(paragraph), styles["Caption"]))
        elif paragraph.startswith("**") and paragraph.endswith("**"):
            story.append(
                Paragraph(inline_markup(paragraph), styles["Subtitle"])
            )
        else:
            story.append(Paragraph(inline_markup(paragraph), styles["BodyCompact"]))

    if in_math:
        raise ValueError("Unclosed display-math block in report source.")
    return story


def main() -> None:
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=42,
        bottomMargin=48,
        title="PID Control - Internship Assignment",
        author="",
        subject="PID control simulation and tuning report",
    )
    document.build(build_story(), onFirstPage=page_footer, onLaterPages=page_footer)
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    main()
