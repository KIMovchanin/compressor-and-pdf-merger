from __future__ import annotations
from pathlib import Path
import shutil
from typing import Optional
from PIL import Image, ImageOps, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

def percent_to_jpeg_quality(percent: int) -> Optional[int]:
    p = max(0, min(100, int(percent)))
    if p == 0:
        return None

    quality = 100 - round(p)
    return max(15, min(73, quality))


def has_alpha(img: Image.Image) -> bool:
    if img.mode in ("RGBA", "LA"):
        return True
    if img.mode == "P":
        return "transparency" in img.info
    return False


def safe_open(path: Path) -> Image.Image | None:
    try:
        img = Image.open(path)
        img.load()
        return img
    except Exception:
        return None


def compress_image(src: str, out_dir: str, percent: int) -> str:
    src_path = Path(src)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    img = safe_open(src_path)

    if img is None:
        raise RuntimeError(f"Не удалось открыть изображение: {src_path}")

    ext = src_path.suffix.lower() # расширение файла

    quality = percent_to_jpeg_quality(percent)
    # 1) 0% -> no changes
    if quality is None:
        out_path = out_dir_p / f"{src_path.stem}_compressed{src_path.suffix}"
        shutil.copy2(src_path, out_path)
        return str(out_path)

    # 2) JPEG / JPG
    if ext in {".jpg", ".jpeg"}:
        out_path = out_dir_p / f"{src_path.stem}_compressed.jpg"
        ImageOps.exif_transpose(img).convert("RGB").save(
            out_path,
            format="JPEG",
            quality=quality,
            optimaze=True,
            progressive=True,
        )
        return str(out_path)

    # 3) WEBP → lossy WebP
    if ext == ".webp":
        out_webp = out_dir_p / f"{src_path.stem}_compressed.webp"
        try:
            ImageOps.exif_transpose(img).convert("RGB").save(
                out_webp, format="WEBP",
                quality=quality,
                method=6 # 0 - быстро, но плохое сжатие. 6 - долго, то качественно
            )
            return str(out_webp)
        except Exception:
            # fallback: если webp-энкодер споткнулся - сохраняем JPEG
            out_jpg = out_dir_p / f"{src_path.stem}_compressed.jpg"
            ImageOps.exif_transpose(img).convert("RGB").save(
                out_jpg, format="JPEG", quality=quality, optimize=True, progressive=True
            )
            return str(out_jpg)

    # 4) PNG / BMP / TIFF
    if ext in {".png", ".bmp", ".tif", ".tiff"}:
        if not has_alpha(img):
            out_path = out_dir_p / f"{src_path.stem}_compressed.jpg"
            ImageOps.exif_transpose(img).convert("RGB").save(
                out_path,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            return str(out_path)
        else:
            out_path = out_dir_p / f"{src_path.stem}_compressed.png"
            img_rgba = ImageOps.exif_transpose(img).convert("RGBA")
            img_q = img_rgba.quantize()
            img_q.save(out_path, format="PNG", optimize=True)
            return str(out_path)

    # 5) Anything else
    out_path = out_dir_p / f"{src_path.stem}_compressed.jpg"
    ImageOps.exif_transpose(img).convert("RGB").save(
        out_path,
        format="JPEG",
        optimize=True,
        progressive=True,
    )
    return str(out_path)


def resize_image(src: str, out_dir: str, *, scale_percent: int) -> str:
    p = max(1, int(scale_percent))  # защита от 0 и мусора
    src_path = Path(src)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    img = safe_open(src_path)
    if img is None:
        raise RuntimeError(f"Не удалось открыть изображение: {src_path}")

    w, h = img.size
    new_w = max(1, (w * p) // 100)
    new_h = max(1, (h * p) // 100)

    img2 = ImageOps.exif_transpose(img).resize((new_w, new_h), Image.Resampling.LANCZOS)

    ext = src_path.suffix.lower()

    if ext in {".jpg", ".jpeg"}:
        out_path = out_dir_p / f"{src_path.stem}_resized.jpg"
        img2.convert("RGB").save(
            out_path,
            format="JPEG",
            quality=85,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
        )
        return str(out_path)

    if ext == ".webp":
        out_path = out_dir_p / f"{src_path.stem}_resized.webp"
        img2.convert("RGB").save(out_path, format="WEBP", quality=85, method=6)
        return str(out_path)

    if ext in {".png", ".bmp", ".tif", ".tiff"}:
        if not has_alpha(img2):
            out_path = out_dir_p / f"{src_path.stem}_resized.jpg"
            img2.convert("RGB").save(
                out_path,
                format="JPEG",
                quality=85,
                optimize=True,
                progressive=True,
                subsampling="4:2:0",
            )
            return str(out_path)
        else:
            out_path = out_dir_p / f"{src_path.stem}_resized.png"
            img2.save(out_path, format="PNG", optimize=True)
            return str(out_path)

    out_path = out_dir_p / f"{src_path.stem}_resized.jpg"
    img2.convert("RGB").save(
        out_path,
        format="JPEG",
        quality=85,
        optimize=True,
        progressive=True,
        subsampling="4:2:0",
    )
    return str(out_path)