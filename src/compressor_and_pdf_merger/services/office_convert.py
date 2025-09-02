from __future__ import annotations
from pathlib import Path
import io
import mammoth
from xhtml2pdf import pisa
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd
from pptx import Presentation
from PIL import Image, ImageDraw, ImageFont
import fitz
from pptx.enum.shapes import MSO_SHAPE_TYPE

EMU_PER_INCH = 914400

def _ensure_font_css() -> str:
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
        return "body { font-family: DejaVuSans; }"
    except Exception:
        return "body { font-family: sans-serif; }"

def docx_to_pdf_basic(docx_path: str | Path, out_pdf: str | Path) -> str:
    docx_path, out_pdf = Path(docx_path), Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    font_css = _ensure_font_css()
    with open(docx_path, "rb") as f:
        try:
            conv = mammoth.images.inline(mammoth.images.img_element(src=mammoth.images.data_uri))
            res = mammoth.convert_to_html(f, convert_image=conv)
        except Exception:
            res = mammoth.convert_to_html(f)
    html = f"<html><head><meta charset='utf-8'><style>@page{{size:A4;margin:18mm}}{font_css}</style></head><body>{res.value}</body></html>"
    with open(out_pdf, "wb") as dst:
        pisa.CreatePDF(html, dest=dst)
    return str(out_pdf)

def xlsx_to_pdf_basic(xlsx_path: str | Path, out_pdf: str | Path) -> str:
    xlsx_path, out_pdf = Path(xlsx_path), Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    xls = pd.ExcelFile(xlsx_path)
    parts = [
        "<html><head><meta charset='utf-8'><style>@page{size:A4;margin:15mm}body{font-family:sans-serif;font-size:12px}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:4px;text-align:left;vertical-align:top}"
        "thead th{background:#f2f2f2}.pb{page-break-after:always}</style></head><body>"
    ]
    for i, sheet in enumerate(xls.sheet_names):
        df = xls.parse(sheet, dtype=str).fillna("")
        parts.append(f"<h2>{sheet}</h2>")
        parts.append(df.to_html(index=False, border=0, escape=False))
        if i < len(xls.sheet_names) - 1:
            parts.append("<div class='pb'></div>")
    parts.append("</body></html>")
    html = "".join(parts)
    with open(out_pdf, "wb") as dst:
        pisa.CreatePDF(html, dest=dst)
    return str(out_pdf)

def _emu_to_px(val_emu: int, dpi: int) -> int:
    return int((val_emu / EMU_PER_INCH) * dpi)

def _pt_to_px(pt: float, dpi: int) -> int:
    try:
        return max(8, int(pt / 72.0 * dpi))
    except Exception:
        return max(8, dpi // 12)

def _shape_box(shape, dpi: int, offset=(0, 0)):
    try:
        l = _emu_to_px(int(shape.left), dpi) + offset[0]
        t = _emu_to_px(int(shape.top), dpi) + offset[1]
        w = _emu_to_px(int(shape.width), dpi)
        h = _emu_to_px(int(shape.height), dpi)
        return l, t, w, h
    except Exception:
        return None

def _render_textframe(draw, shape, dpi: int, base_font, offset=(0, 0)):
    if not getattr(shape, "has_text_frame", False):
        return
    box = _shape_box(shape, dpi, offset)
    if not box:
        return
    l, t, w, h = box
    y = t
    try:
        for p in shape.text_frame.paragraphs:
            runs = p.runs if getattr(p, "runs", None) else []
            txt = "".join([r.text for r in runs if getattr(r, "text", "")]) or p.text or ""
            if not txt.strip():
                continue
            sz_pt = next((float(r.font.size.pt) for r in runs if r.font.size), 0.0) or 18.0
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", _pt_to_px(sz_pt, dpi))
            except Exception:
                font = base_font
            draw.multiline_text((l + 6, y + 4), txt, fill=(0, 0, 0), font=font)
            y += getattr(font, "size", base_font.size if hasattr(base_font, "size") else 14) + 6
    except Exception:
        try:
            draw.multiline_text((l + 6, y + 4), shape.text_frame.text or "", fill=(0, 0, 0), font=base_font)
        except Exception:
            pass

def _render_picture(canvas, shape, dpi: int, offset=(0, 0)):
    if getattr(shape, "shape_type", None) != MSO_SHAPE_TYPE.PICTURE or not hasattr(shape, "image"):
        return
    box = _shape_box(shape, dpi, offset)
    if not box:
        return
    l, t, w, h = box
    try:
        pic = Image.open(io.BytesIO(shape.image.blob)).convert("RGB")
        pic = pic.resize((max(1, w), max(1, h)))
        canvas.paste(pic, (l, t))
    except Exception:
        pass

def _render_autoshape(draw, shape, dpi: int, offset=(0, 0)):
    if getattr(shape, "shape_type", None) != MSO_SHAPE_TYPE.AUTO_SHAPE:
        return
    box = _shape_box(shape, dpi, offset)
    if not box:
        return
    l, t, w, h = box
    try:
        fc = getattr(shape, "fill", None)
        color = (230, 230, 230)
        if fc and fc.type is not None and hasattr(fc, "fore_color") and getattr(fc, "fore_color", None):
            col = getattr(fc.fore_color, "rgb", None)
            if col is not None:
                color = (int(col[0]), int(col[1]), int(col[2]))
        draw.rectangle([l, t, l + w, t + h], fill=color, outline=(180, 180, 180))
    except Exception:
        draw.rectangle([l, t, l + w, t + h], outline=(180, 180, 180))

def _render_table(draw, shape, dpi: int, font, offset=(0, 0)):
    if getattr(shape, "shape_type", None) != MSO_SHAPE_TYPE.TABLE:
        return
    box = _shape_box(shape, dpi, offset)
    if not box:
        return
    l, t, w, h = box
    try:
        rows = shape.table.rows
        cols = shape.table.columns
        rh = max(1, h // max(1, len(rows)))
        cw = max(1, w // max(1, len(cols)))
        for r, _ in enumerate(rows):
            for c, _ in enumerate(cols):
                x0 = l + c * cw
                y0 = t + r * rh
                x1 = x0 + cw
                y1 = y0 + rh
                draw.rectangle([x0, y0, x1, y1], outline=(180, 180, 180))
                try:
                    cell = shape.table.cell(r, c)
                    txt = (cell.text or "").strip()
                    if txt:
                        draw.multiline_text((x0 + 4, y0 + 4), txt, fill=(0, 0, 0), font=font)
                except Exception:
                    pass
    except Exception:
        pass

def _render_group(canvas, draw, shape, dpi: int, font, offset=(0, 0)):
    if getattr(shape, "shape_type", None) != MSO_SHAPE_TYPE.GROUP:
        return
    gbox = _shape_box(shape, dpi, offset)
    base_off = (gbox[0], gbox[1]) if gbox else offset
    try:
        for child in shape.shapes:
            _render_one(canvas, draw, child, dpi, font, base_off)
    except Exception:
        pass

def _render_one(canvas, draw, shape, dpi: int, font, offset=(0, 0)):
    try:
        st = getattr(shape, "shape_type", None)
        if st == MSO_SHAPE_TYPE.GROUP:
            _render_group(canvas, draw, shape, dpi, font, offset)
            return
        if st == MSO_SHAPE_TYPE.PICTURE:
            _render_picture(canvas, shape, dpi, offset)
        elif st == MSO_SHAPE_TYPE.TABLE:
            _render_table(draw, shape, dpi, font, offset)
        elif st == MSO_SHAPE_TYPE.AUTO_SHAPE:
            _render_autoshape(draw, shape, dpi, offset)
        if getattr(shape, "has_text_frame", False):
            _render_textframe(draw, shape, dpi, font, offset)
    except Exception:
        pass

def pptx_to_pdf_basic(pptx_path: str | Path, out_pdf: str | Path, dpi: int = 150) -> str:
    pptx_path, out_pdf = Path(pptx_path), Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation(str(pptx_path))
    page_w_px = _emu_to_px(int(prs.slide_width), dpi)
    page_h_px = _emu_to_px(int(prs.slide_height), dpi)
    try:
        base_font = ImageFont.truetype("DejaVuSans.ttf", size=max(12, dpi // 11))
    except Exception:
        base_font = ImageFont.load_default()
    doc = fitz.open()
    for slide in prs.slides:
        img = Image.new("RGB", (page_w_px, page_h_px), "white")
        draw = ImageDraw.Draw(img)
        try:
            for shape in slide.shapes:
                _render_one(img, draw, shape, dpi, base_font, (0, 0))
        except Exception:
            pass
        b = io.BytesIO()
        img.save(b, format="JPEG", quality=85)
        page = doc.new_page(width=page_w_px, height=page_h_px)
        rect = fitz.Rect(0, 0, page_w_px, page_h_px)
        page.insert_image(rect, stream=b.getvalue())
    doc.save(str(out_pdf))
    doc.close()
    return str(out_pdf)
