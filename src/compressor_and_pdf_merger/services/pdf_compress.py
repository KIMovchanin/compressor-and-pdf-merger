from __future__ import annotations
from pathlib import Path
import os, shutil, pikepdf
from .pdf_utils import which, run, tmp_path


def _linearize(path: Path) -> None:
    qpdf = which("qpdf") or which("qpdf.exe")
    if not qpdf:
        return
    tmp = tmp_path(".pdf")
    os.replace(path, tmp)
    run([qpdf, "--linearize", str(tmp), str(path)], "qpdf")
    tmp.unlink(missing_ok=True)


def _safe_strip_metadata(pdf: pikepdf.Pdf, *, also_names: bool = True) -> None:
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
) -> str:
    src_p = Path(src)
    out_p = Path(out_pdf)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if mode == "lossless":
        with pikepdf.open(src_p) as pdf:
            if strip_metadata:
                _safe_strip_metadata(pdf, also_names=True)
            pdf.save(
                str(out_p),
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                linearize=False,
            )

        _linearize(out_p)

        if ensure_not_larger and out_p.stat().st_size >= int(src_p.stat().st_size * min_shrink_ratio):
            shutil.copyfile(src_p, out_p)

        return str(out_p)

    elif mode == "images":
        gs = which("gswin64c") or which("gswin32c") or which("gs")
        if not gs:
            raise RuntimeError("Для режима «С картинками» нужен Ghostscript (gs). Установите и добавьте в PATH.")

        tmp = tmp_path(".pdf")
        args = [
            gs, "-dSAFER", "-dBATCH", "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-dDownsampleColorImages=true", f"-dColorImageResolution={int(target_dpi)}",
            "-dDownsampleGrayImages=true",  f"-dGrayImageResolution={int(target_dpi)}",
            "-dDownsampleMonoImages=true",  f"-dMonoImageResolution={int(target_dpi)}",
            "-dDetectDuplicateImages=true",
            "-dAutoRotatePages=/None",
            "-dColorConversionStrategy=/LeaveColorUnchanged",
            "-dEncodeColorImages=true", "-dEncodeGrayImages=true", "-dEncodeMonoImages=true",
            f"-dJPEGQ={int(jpeg_quality)}",
            "-sOutputFile=" + str(tmp),
            str(src_p),
        ]
        if grayscale:
            # Перевод в серый
            args.insert(-2, "-sColorConversionStrategy=Gray")
            args.insert(-2, "-dProcessColorModel=/DeviceGray")

        run(args, "ghostscript")

        if ensure_not_larger and tmp.stat().st_size >= int(src_p.stat().st_size * min_shrink_ratio):
            shutil.copyfile(src_p, out_p)
            tmp.unlink(missing_ok=True)
        else:
            if out_p.exists():
                out_p.unlink()
            os.replace(tmp, out_p)

        return str(out_p)

    else:
        raise ValueError(f"Unknown mode: {mode}")
