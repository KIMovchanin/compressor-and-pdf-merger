from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional
import os
import fitz
from PIL import Image
from .pdf_utils import tmp_path


IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def _exif_rotate_deg(path: Path) -> int:
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            if not exif:
                return 0
            val = exif.get(274, 1)
            if val == 3:
                return 180
            if val == 6:
                return 270
            if val == 8:
                return 90
            return 0
    except Exception:
        return 0


def merge_any_to_pdf(
    inputs: Iterable[str | Path],
    out_pdf: str | Path,
    page_ranges: Optional[dict[str, str]] = None,
    keep_outlines: bool = True,
    linearize: bool = True,
    fit_to_a4: bool = True,
    fit_margin_mm: float = 0.0,
) -> str:
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    mm_to_pt = 72.0 / 25.4
    margin = float(fit_margin_mm) * mm_to_pt
    a4 = fitz.paper_rect("a4")
    dst = fitz.open()
    for it in inputs:
        p = Path(it)
        if not p.exists():
            raise FileNotFoundError(p)
        ext = p.suffix.lower()
        if ext == ".pdf":
            src = fitz.open(str(p))
            rng = (page_ranges or {}).get(str(p)) or (page_ranges or {}).get(p.name)
            pages = list(range(len(src)))
            if rng:
                idxs = []
                total = len(src)
                for part in rng.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    if "-" in part:
                        a, b = part.split("-", 1)
                        s = max(1, int(a)) if a else 1
                        e = total if not b else max(1, int(b))
                        idxs.extend([i - 1 for i in range(s, e + 1)])
                    else:
                        idxs.append(max(1, int(part)) - 1)
                pages = [i for i in idxs if 0 <= i < total]
            if fit_to_a4:
                for i in pages:
                    page = src[i]
                    new = dst.new_page(width=a4.width, height=a4.height)
                    new.draw_rect(a4, color=(1, 1, 1), fill=(1, 1, 1))
                    inner = fitz.Rect(a4.x0 + margin, a4.y0 + margin, a4.x1 - margin, a4.y1 - margin)
                    r = page.rect
                    s = min(inner.width / r.width, inner.height / r.height)
                    w = r.width * s
                    h = r.height * s
                    left = inner.x0 + (inner.width - w) / 2.0
                    top = inner.y0 + (inner.height - h) / 2.0
                    target = fitz.Rect(left, top, left + w, top + h)
                    new.show_pdf_page(target, src, i)
            else:
                dst.insert_pdf(src)
            src.close()
        elif ext in IMAGE_EXT:
            rot = _exif_rotate_deg(p)
            pix = fitz.Pixmap(str(p))
            iw, ih = pix.width, pix.height
            if rot in (90, 270):
                iw, ih = ih, iw
            if fit_to_a4:
                new = dst.new_page(width=a4.width, height=a4.height)
                new.draw_rect(a4, color=(1, 1, 1), fill=(1, 1, 1))
                inner = fitz.Rect(a4.x0 + margin, a4.y0 + margin, a4.x1 - margin, a4.y1 - margin)
                s = min(inner.width / iw, inner.height / ih)
                w = iw * s
                h = ih * s
                left = inner.x0 + (inner.width - w) / 2.0
                top = inner.y0 + (inner.height - h) / 2.0
                rect = fitz.Rect(left, top, left + w, top + h)
                new.insert_image(rect, filename=str(p), rotate=rot)
            else:
                new = dst.new_page(width=iw, height=ih)
                rect = fitz.Rect(0, 0, iw, ih)
                new.insert_image(rect, filename=str(p), rotate=rot)
        else:
            raise RuntimeError(f"Тип файла не поддерживается без внешних программ: {p.name}")
    tmp = tmp_path(".pdf")
    dst.save(str(tmp))
    dst.close()
    os.replace(tmp, out_pdf)
    if not out_pdf.exists() or out_pdf.stat().st_size == 0:
        raise RuntimeError("Итоговый файл не создан")
    return str(out_pdf)
