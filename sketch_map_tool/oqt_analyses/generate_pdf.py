from io import BytesIO

from celery import canvas


def generate_pdf(report_properties: dict) -> BytesIO:
    pdf_bytes = BytesIO()
    canv_output = canvas.Canvas(pdf_bytes)

    text = canv_output.beginText()
    text.textLines("New Quality Report")
    canv_output.drawText(text)

    return canv_output
