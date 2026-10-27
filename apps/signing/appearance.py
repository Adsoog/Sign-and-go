import io
import qrcode
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
    TextStringObject,
)
from apps.signing.coordinates import convert_normalized_to_pdf_box


def generate_qr_image_bytes(data_url: str, size: int = 150) -> bytes:
    """Generates a high-contrast QR code image as PNG bytes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(data_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F172A", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def _clean_signer_and_org(signer_name: str, subject: str) -> tuple[str, str]:
    """
    Extracts clean human-readable signer name and organization from subject/signer_name.
    Strips raw ASN.1 OIDs like 'countryName=', 'organizationName=', etc.
    """
    org = ""
    cn = ""

    if "organizationName=" in subject or "commonName=" in subject:
        import re
        m_cn = re.search(r"commonName=([^,\)]+)", subject)
        if m_cn:
            cn = m_cn.group(1).strip()
        m_org = re.search(r"organizationName=([^,\)]+)", subject)
        if m_org:
            org = m_org.group(1).strip()
    elif " - " in subject:
        parts = [p.strip() for p in subject.split(" - ")]
        cn = parts[0]
        if len(parts) > 1:
            org = parts[1].split("(")[0].strip()
    elif "·" in subject:
        parts = [p.strip() for p in subject.split("·")]
        cn = parts[0]
        if len(parts) > 1:
            org = parts[1].split("(")[0].strip()
    else:
        cn = subject.split(",")[0].replace("CN=", "").strip()

    final_signer = signer_name.strip() if signer_name else (cn or "Firmante")
    if org and org.lower() == final_signer.lower():
        org = ""

    return final_signer, org


def _fit_text(c: canvas.Canvas, text: str, font_name: str, font_size: float, max_width: float) -> str:
    """Truncates text with ellipsis if it exceeds max_width to strictly prevent collisions."""
    if not text or max_width <= 0:
        return ""
    if c.stringWidth(text, font_name, font_size) <= max_width:
        return text
    ellipsis = "..."
    ellipsis_w = c.stringWidth(ellipsis, font_name, font_size)
    if ellipsis_w >= max_width:
        return ""
    avail_w = max_width - ellipsis_w
    for i in range(len(text), 0, -1):
        candidate = text[:i]
        if c.stringWidth(candidate, font_name, font_size) <= avail_w:
            return candidate + ellipsis
    return ellipsis


def create_signature_stamp_overlay(
    page_width: float,
    page_height: float,
    box: tuple[float, float, float, float],
    signer_name: str,
    subject: str,
    signed_date_str: str,
    verification_url: str,
    tracking_beacon_url: str | None = None,
) -> bytes:
    """
    Renders an elegant, professional visual signature box on a blank canvas of identical page size.
    Returns the overlay PDF as bytes.
    """
    x1, y1, x2, y2 = box
    box_w = x2 - x1
    box_h = y2 - y1

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    c.saveState()

    # 1. Clean, crisp white card background with subtle dark slate border
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(HexColor("#0F172A"))
    c.setLineWidth(0.8)
    c.roundRect(x1, y1, box_w, box_h, 3, fill=1, stroke=1)

    # 2. Left vertical accent bar in dark navy slate
    c.setFillColor(HexColor("#0F172A"))
    c.roundRect(x1, y1, 3.5, box_h, 1.5, fill=1, stroke=0)

    # 3. Clean signer and organization data
    clean_signer, clean_org = _clean_signer_and_org(signer_name, subject)

    # 4. QR code layout
    show_qr = box_w >= 120 and box_h >= 36
    if show_qr:
        qr_size = min(box_h - 12, 60.0)
        qr_x = x2 - qr_size - 7
        qr_y = y1 + (box_h - qr_size) / 2

        # Draw subtle vertical dividing hairline
        div_x = qr_x - 7
        c.setStrokeColor(HexColor("#E2E8F0"))
        c.setLineWidth(0.5)
        c.line(div_x, y1 + 5, div_x, y2 - 5)

        # Draw QR code
        try:
            qr_bytes = generate_qr_image_bytes(verification_url)
            from reportlab.lib.utils import ImageReader
            qr_img = ImageReader(io.BytesIO(qr_bytes))
            c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
        except Exception:
            div_x = x2
        text_max_w = max(10, div_x - (x1 + 10) - 4)
    else:
        text_max_w = max(10, box_w - 18)

    # 5. Clean, proportional typography strictly fitted inside text_max_w
    text_x = x1 + 10

    if box_h >= 75:
        # Full layout
        c.setFillColor(HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(text_x, y2 - 13, _fit_text(c, "FIRMADO DIGITALMENTE", "Helvetica-Bold", 7.5, text_max_w))

        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(text_x, y2 - 27, _fit_text(c, clean_signer, "Helvetica-Bold", 9.5, text_max_w))

        c.setFillColor(HexColor("#475569"))
        c.setFont("Helvetica", 6.5)
        org_label = clean_org if clean_org else "Certificado Digital Cualificado"
        c.drawString(text_x, y2 - 39, _fit_text(c, org_label, "Helvetica", 6.5, text_max_w))

        c.setFillColor(HexColor("#64748B"))
        c.setFont("Helvetica", 6.5)
        c.drawString(text_x, y2 - 49, _fit_text(c, f"Fecha: {signed_date_str}", "Helvetica", 6.5, text_max_w))

        c.setFillColor(HexColor("#0284C7"))
        c.setFont("Helvetica", 5.8)
        c.drawString(text_x, y1 + 6, _fit_text(c, "Verificacion PAdES - Escanear QR", "Helvetica", 5.8, text_max_w))

    elif box_h >= 50:
        # Medium layout
        c.setFillColor(HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(text_x, y2 - 11, _fit_text(c, "FIRMADO DIGITALMENTE", "Helvetica-Bold", 6.5, text_max_w))

        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(text_x, y2 - 23, _fit_text(c, clean_signer, "Helvetica-Bold", 8.5, text_max_w))

        c.setFillColor(HexColor("#64748B"))
        c.setFont("Helvetica", 6.0)
        c.drawString(text_x, y2 - 33, _fit_text(c, f"Fecha: {signed_date_str}", "Helvetica", 6.0, text_max_w))

        c.setFillColor(HexColor("#0284C7"))
        c.setFont("Helvetica", 5.5)
        c.drawString(text_x, y1 + 5, _fit_text(c, "Verificacion PAdES - Escanear QR", "Helvetica", 5.5, text_max_w))

    else:
        # Compact layout
        c.setFillColor(HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(text_x, y2 - 12, _fit_text(c, clean_signer, "Helvetica-Bold", 7.5, text_max_w))

        c.setFillColor(HexColor("#64748B"))
        c.setFont("Helvetica", 6.0)
        c.drawString(text_x, y1 + 5, _fit_text(c, f"Fecha: {signed_date_str}", "Helvetica", 6.0, text_max_w))

    c.restoreState()
    c.showPage()
    c.save()

    packet.seek(0)
    return packet.getvalue()


def embed_visual_appearance_in_pdf(
    source_pdf_bytes: bytes,
    page_number: int,
    norm_x: float,
    norm_y: float,
    norm_w: float,
    norm_h: float,
    signer_name: str,
    subject: str,
    signed_date_str: str,
    verification_url: str,
    tracking_beacon_url: str | None = None,
) -> tuple[bytes, tuple[float, float, float, float]]:
    """
    Merges the visual appearance overlay onto the target page of source_pdf_bytes.
    Adds a clickable URI link annotation over the signature box.
    Returns (modified_pdf_bytes, pdf_box_coordinates).
    """
    reader = PdfReader(io.BytesIO(source_pdf_bytes))
    writer = PdfWriter()

    target_page_idx = max(0, min(len(reader.pages) - 1, page_number - 1))
    target_page = reader.pages[target_page_idx]

    page_width = float(target_page.mediabox.width)
    page_height = float(target_page.mediabox.height)

    box = convert_normalized_to_pdf_box(
        norm_x=norm_x,
        norm_y=norm_y,
        norm_width=norm_w,
        norm_height=norm_h,
        page_width_pts=page_width,
        page_height_pts=page_height,
    )

    overlay_bytes = create_signature_stamp_overlay(
        page_width=page_width,
        page_height=page_height,
        box=box,
        signer_name=signer_name,
        subject=subject,
        signed_date_str=signed_date_str,
        verification_url=verification_url,
        tracking_beacon_url=tracking_beacon_url,
    )

    overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
    overlay_page = overlay_reader.pages[0]

    for idx, page in enumerate(reader.pages):
        if idx == target_page_idx:
            page.merge_page(overlay_page)
            # Add interactive URI link annotation over the box
            x1, y1, x2, y2 = box
            link_annot = DictionaryObject()
            link_annot.update({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(x1), FloatObject(y1), FloatObject(x2), FloatObject(y2)]),
                NameObject("/Border"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),
                NameObject("/A"): DictionaryObject({
                    NameObject("/Type"): NameObject("/Action"),
                    NameObject("/S"): NameObject("/URI"),
                    NameObject("/URI"): TextStringObject(verification_url),
                }),
            })
            if "/Annots" not in page:
                page[NameObject("/Annots")] = ArrayObject([link_annot])
            else:
                page["/Annots"].append(link_annot)

        writer.add_page(page)

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    return out_buf.getvalue(), box
