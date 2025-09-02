from __future__ import annotations
from pathlib import Path
import io, os, shutil
import fitz
from PIL import Image, ImageOps
import pikepdf
from .pdf_utils import tmp_path


def _safe_strip_metadata(pdf: pikepdf.Pdf, also_names: bool = True) -> None:
    try:
        di = getattr(pdf, "docinfo", None)
        if di:
            for k in list(di.keys()):
                try:
                    del di[k]
                except Exception:
                    pass
        if "/Info" in pdf.trailer:
            pdf.trailer["/Info"] = pikepdf.Dictionary()
    except Exception:
        pass
    try:
        if "/Metadata" in pdf.Root:
            del pdf.Root["/Metadata"]
    except Exception:
        pass
    if also_names:
        try:
            if "/Names" in pdf.Root:
                del pdf.Root["/Names"]
        except Exception:
            pass


def _flatten_to_rgb(im: Image.Image, grayscale: bool) -> Image.Image:
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im.convert("RGB"), mask=im.split()[-1])
        im = bg
    elif im.mode == "P":
        im = im.convert("RGB")
    elif im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if grayscale and im.mode != "L":
        im = ImageOps.grayscale(im)
    return im


def _jpeg_bytes(im: Image.Image, quality: int) -> bytes:
    bio = io.BytesIO()
    im.save(bio, format="JPEG", quality=int(quality), optimize=True, progressive=True)
    return bio.getvalue()


def _rasterize_pdf(src_pdf: str | Path, out_pdf: str | Path, dpi: int, quality: int, grayscale: bool, strip_metadata: bool) -> None:
    src = fitz.open(str(src_pdf))
    out = fitz.open()
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)
    cs = fitz.csGRAY if grayscale else fitz.csRGB
    for p in src:
        rect = p.rect
        pix = p.get_pixmap(matrix=mat, colorspace=cs, alpha=False)
        mode = "L" if grayscale else "RGB"
        im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        im = _flatten_to_rgb(im, grayscale)
        jpg = _jpeg_bytes(im, quality)
        new = out.new_page(width=rect.width, height=rect.height)
        new.insert_image(rect, stream=jpg)
    tmp = tmp_path(".pdf")
    out.save(str(tmp), deflate=True)
    out.close()
    src.close()
    if strip_metadata:
        with pikepdf.open(tmp) as pdf:
            _safe_strip_metadata(pdf, also_names=True)
            pdf.save(str(out_pdf), compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        Path(tmp).unlink(missing_ok=True)
    else:
        if Path(out_pdf).exists():
            Path(out_pdf).unlink()
        os.replace(tmp, out_pdf)


def compress_pdf(
    src: str | Path,
    out_pdf: str | Path,
    *,
    mode: str = "lossless",
    target_dpi: int = 144,
    jpeg_quality: int = 75,
    grayscale: bool = False,
    strip_metadata: bool = True,
    ensure_not_larger: bool = True,
    min_shrink_ratio: float = 0.98,
    target_percent: int | None = None,
) -> str:
    src_p = Path(src)
    out_p = Path(out_pdf)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if mode == "lossless":
        with pikepdf.open(src_p) as pdf:
            if strip_metadata:
                _safe_strip_metadata(pdf, also_names=True)
            pdf.save(str(out_p), compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        if ensure_not_larger and out_p.stat().st_size >= int(src_p.stat().st_size * min_shrink_ratio):
            shutil.copyfile(src_p, out_p)
        return str(out_p)

    if mode != "images":
        raise ValueError("Unknown mode: " + mode)

    if target_percent and 1 <= target_percent < 100:
        src_size = src_p.stat().st_size
        target_max = int(src_size * (target_percent / 100.0))
        best = None
        best_sz = None
        dpi = int(target_dpi)
        q = int(jpeg_quality)
        for _ in range(8):
            trial = tmp_path(".pdf")
            _rasterize_pdf(src_p, trial, dpi=dpi, quality=q, grayscale=grayscale, strip_metadata=strip_metadata)
            sz = trial.stat().st_size
            if best is None or sz < best_sz:
                best, best_sz = trial, sz
            if sz <= target_max:
                break
            dpi = max(72, int(dpi * 0.85))
            q = max(40, q - 7)
        if best is None:
            shutil.copyfile(src_p, out_p)
            return str(out_p)
        if ensure_not_larger and best_sz >= int(src_p.stat().st_size * min_shrink_ratio):
            shutil.copyfile(src_p, out_p)
            Path(best).unlink(missing_ok=True)
            return str(out_p)
        if out_p.exists():
            out_p.unlink()
        os.replace(best, out_p)
        return str(out_p)

    tmp = tmp_path(".pdf")
    _rasterize_pdf(src_p, tmp, dpi=int(target_dpi), quality=int(jpeg_quality), grayscale=grayscale, strip_metadata=strip_metadata)
    if ensure_not_larger and tmp.stat().st_size >= int(src_p.stat().st_size * min_shrink_ratio):
        shutil.copyfile(src_p, out_p)
        Path(tmp).unlink(missing_ok=True)
    else:
        if out_p.exists():
            out_p.unlink()
        os.replace(tmp, out_p)
    return str(out_p)
