"""Generate printable device stickers with QR code + human-readable text.

Each sticker is an A6-sized PDF intended to be printed and affixed to the
physical sensor at install time.
"""

import json
from io import BytesIO
import qrcode
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_sticker_pdf(
    *,
    dev_eui: str,
    app_key: str,
    join_eui: str,
    device_name: str,
    device_type: str,
) -> bytes:
    """
    Generate an A6 sticker PDF for a newly-created device.

    Layout:
      - Norani brand bar at the top
      - QR code on the left (encodes DevEUI/JoinEUI/AppKey for scanning)
      - Device name + type + EUI on the right
      - Footer with Norani contact info

    Returns the PDF as raw bytes.
    """

    # 1. Build the QR code payload (industry-standard LoRaWAN format)
    qr_payload = json.dumps({
        "DevEUI": dev_eui,
        "JoinEUI": join_eui,
        "AppKey": app_key,
    })
    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    # 2. Render PDF on A6 (105 x 148 mm)
    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=A6)
    width, height = A6  # in points

    # Brand bar at top
    c.setFillColorRGB(0.122, 0.306, 0.475)  # #1F4E79
    c.rect(0, height - 18 * mm, width, 18 * mm, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(10 * mm, height - 12 * mm, "Norani")
    # Orange dot accent
    c.setFillColorRGB(0.961, 0.486, 0)  # #F57C00
    c.circle(28 * mm, height - 12 * mm + 1, 1.2 * mm, fill=True, stroke=False)
    # Tagline
    c.setFillColorRGB(0.733, 0.871, 0.984)
    c.setFont("Helvetica", 7)
    c.drawString(10 * mm, height - 16 * mm, "LoRaWAN device")

    # QR code (left side)
    qr_size = 50 * mm
    qr_x = 8 * mm
    qr_y = height - 18 * mm - qr_size - 5 * mm
    c.drawImage(
        ImageReader(qr_buf),
        qr_x, qr_y,
        qr_size, qr_size,
    )

    # Text fields (right side of QR)
    text_x = qr_x + qr_size + 5 * mm
    text_y = height - 25 * mm

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    # Truncate long names
    display_name = device_name[:30] + "..." if len(device_name) > 30 else device_name
    c.drawString(text_x, text_y, display_name)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(text_x, text_y - 5 * mm, device_type[:35])

    # EUI
    c.setFont("Courier-Bold", 7)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(text_x, text_y - 12 * mm, "DevEUI:")
    c.setFont("Courier", 7)
    c.drawString(text_x, text_y - 16 * mm, dev_eui)

    # Instructions below QR
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(8 * mm, qr_y - 5 * mm, "Scan QR to provision device.")
    c.drawString(8 * mm, qr_y - 9 * mm, "Apply sticker to sensor enclosure.")

    # Footer
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(8 * mm, 5 * mm, "Norani Ltd  |  Kigali, Rwanda  |  norani.rw")

    c.save()
    pdf_buf.seek(0)
    return pdf_buf.getvalue()
