# app_taller/pdf_utils.py
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet


def build_header_footer(logo_path: str, titulo: str):
    """
    Devuelve una función callback para usar en onFirstPage / onLaterPages
    que dibuja el logo, título y número de página.
    """
    def _hf(canvas, doc):
        width, height = A4

        # Logo
        if logo_path and os.path.exists(logo_path):
            try:
                canvas.drawImage(
                    logo_path,
                    40,
                    height - 60,
                    width=100,
                    height=30,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                # Si falla el logo, no rompemos el PDF
                pass

        # Título y número de página
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 40, height - 35, titulo)
        canvas.drawRightString(
            width - 40, 20, f"Página {canvas.getPageNumber()}"
        )

    return _hf


def pdf_tabla(title: str, headers, data, col_widths=None):
    """
    Genera los elementos (Paragraph + Table + Spacer) para una sección tipo tabla.
    """
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(title, styles["Heading3"]))
    elements.append(Spacer(1, 6))

    # Evitar reventar si no hay datos
    data = data or []
    table_data = [headers] + data

    t = Table(table_data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003399")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )

    elements.append(t)
    elements.append(Spacer(1, 12))
    return elements
