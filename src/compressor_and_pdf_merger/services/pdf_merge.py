from __future__ import annotations
from pathlib import Path
from typing import Iterable, Optional
import img2pdf, pikepdf, os
from .pdf_utils import which, run, tmp_path
import fitz

OFFICE_EXT = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".odt", ".odp", ".ods"}
IMAGE_EXT  = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}

def _images_to_pdf(img_paths: list[Path]) -> Path:
    out = tmp_path(".pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in img_paths]))
    return out

def _office_to_pdf(path: Path) -> Path:
    soffice = which("soffice") or which("soffice.exe")
    if not soffice:
        raise RuntimeError("LibreOffice не найден. Поставьте LibreOffice и добавьте soffice в PATH.")
    out_dir = tmp_path(".d")
    out_dir.unlink(missing_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(path)]
    run(cmd, "LibreOffice")
    out_pdf = out_dir / (path.stem + ".pdf")
    if not out_pdf.exists():
        cands = list(out_dir.glob("*.pdf"))
        if not cands:
            raise RuntimeError("LibreOffice не создал PDF из файла: " + str(path))
        out_pdf = cands[0]
    return out_pdf

def _single_to_pdf(path: Path) -> Path:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return path
    if ext in IMAGE_EXT:
        return _images_to_pdf([path])
    if ext in OFFICE_EXT:
        return _office_to_pdf(path)
    raise RuntimeError(f"Неподдерживаемый тип: {ext}")

def _linearize_inplace(path: Path) -> None:
    qpdf = which("qpdf") or which("qpdf.exe")
    if not qpdf:
        return
    tmp = tmp_path(".pdf")
    os.replace(path, tmp)
    run([qpdf, "--linearize", str(tmp), str(path)], "qpdf")
    tmp.unlink(missing_ok=True)

def _fit_pdf_to_a4(in_pdf: Path, out_pdf: Path, margin_mm: float = 0.0) -> None:
    mm_to_pt = 72.0 / 25.4
    margin = float(margin_mm) * mm_to_pt
    a4 = fitz.paper_rect("a4")

    src = fitz.open(str(in_pdf))
    dst = fitz.open()

    for pno in range(len(src)):
        page = src[pno]
        new = dst.new_page(width=a4.width, height=a4.height)
        new.draw_rect(a4, color=(1, 1, 1), fill=(1, 1, 1))
        inner = fitz.Rect(a4.x0 + margin, a4.y0 + margin, a4.x1 - margin, a4.y1 - margin)

        src_rect = page.rect
        if src_rect.width <= 0 or src_rect.height <= 0:
            continue
        scale = min(inner.width / src_rect.width, inner.height / src_rect.height)
        w = src_rect.width * scale
        h = src_rect.height * scale
        left = inner.x0 + (inner.width - w) / 2.0
        top  = inner.y0 + (inner.height - h) / 2.0
        target = fitz.Rect(left, top, left + w, top + h)

        new.show_pdf_page(target, src, pno)

    dst.save(str(out_pdf))
    src.close()
    dst.close()

def merge_any_to_pdf(
    inputs: Iterable[str | Path],
    out_pdf: str | Path,
    page_ranges: Optional[dict[str, str]] = None,
    keep_outlines: bool = True,
    linearize: bool = True,
    fit_to_a4: bool = False,
    fit_margin_mm: float = 0.0,
) -> str:
    page_ranges = page_ranges or {}
    tmp_pdfs: list[Path] = []

    for it in inputs:
        p = Path(it)
        if not p.exists():
            raise FileNotFoundError(p)
        if p.suffix.lower() in IMAGE_EXT:
            tmp_pdfs.append(_images_to_pdf([p]))
        else:
            tmp_pdfs.append(_single_to_pdf(p))

    out_pdf = Path(out_pdf)
