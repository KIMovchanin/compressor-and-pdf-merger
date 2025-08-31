from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Callable, Optional, Literal
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


def _colors_from_percent(percent: int) -> int:
    p = max(0, min(100, int(percent)))
    return max(16, min(256, int(256 - p * (256 - 16) / 100)))


def compress_image(src: str, out_dir: str, percent: int, *, strip_metadata: bool = False) -> str:
    src_path = Path(src)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    img = safe_open(src_path)

    if img is None:
        raise RuntimeError(f"Не удалось открыть изображение: {src_path}")

    ext = src_path.suffix.lower()
    quality = percent_to_jpeg_quality(percent)

    image = ImageOps.exif_transpose(img)

    # 1) 0% -> no changes
    if quality is None:
        out_path = out_dir_p / f"{src_path.stem}_compressed{src_path.suffix}"
        if not strip_metadata:
            shutil.copy2(src_path, out_path)
            return str(out_path)

        if ext in {".jpg", ".jpeg"}:
            image.convert("RGB").save(
                out_path,
                format="JPEG",
                quality=95,
                optimize=True,
                progressive=True,
                subsampling="4:2:0",
                **_meta_kwargs(img, strip=True),
            )

        elif ext == ".webp":
            image.save(
                out_path,
                format="WEBP",
                lossless=True,
                method=6,
                **_meta_kwargs(img, strip=True),
            )

        elif ext == ".png":
            image.save(
                out_path,
                format="PNG",
                optimize=True,
                compress_level=9,
                **_meta_kwargs(img, strip=True),
            )

        elif ext in {".tif", ".tiff"}:
            image.save(
                out_path,
                format="TIFF",
                compression="tiff_lzw",
                **_meta_kwargs(img, strip=True),
            )

        else:
            image.convert("RGB").save(
                out_path,
                format="JPEG",
                quality=95,
                optimize=True,
                progressive=True,
                subsampling="4:2:0",
                **_meta_kwargs(img, strip=True),
            )
        return str(out_path)

    # 2) JPEG / JPG
    if ext in {".jpg", ".jpeg"}:
        out_path = out_dir_p / f"{src_path.stem}_compressed.jpg"
        image.convert("RGB").save(
            out_path,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
            **_meta_kwargs(img, strip=strip_metadata),
        )
        return str(out_path)

    # 3) WEBP → lossy WebP
    if ext == ".webp":
        out_path = out_dir_p / f"{src_path.stem}_compressed.webp"
        image.convert("RGB").save(
            out_path,
            format="WEBP",
            quality=max(1, min(95, int(quality))),
            method=6,
            **_meta_kwargs(img, strip=strip_metadata),
        )
        return str(out_path)

    # 4) PNG
    if ext == ".png":
        out_path = out_dir_p / f"{src_path.stem}_compressed.png"
        if percent > 0:
            if has_alpha(image):
                a = image.getchannel("A")
                rgb = image.convert("RGB")
                colors = _colors_from_percent(percent)
                pal = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
                pal_rgba = pal.convert("RGBA")
                pal_rgba.putalpha(a)
                pal_rgba.save(
                    out_path, format="PNG",
                    optimize=True,
                    compress_level=9,
                    **_meta_kwargs(img, strip=strip_metadata),
                )
            else:
                colors = _colors_from_percent(percent)
                pal = image.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
                pal.save(
                    out_path,
                    format="PNG",
                    optimize=True,
                    compress_level=9,
                    **_meta_kwargs(img, strip=strip_metadata),
                )
        else:
            image.save(
                out_path,
                format="PNG",
                optimize=True,
                compress_level=9,
                **_meta_kwargs(img, strip=strip_metadata),
            )
        return str(out_path)

    # 5) TIFF / TIF
    if ext in {".tif", ".tiff"}:
        out_path = out_dir_p / f"{src_path.stem}_compressed.tiff"
        save_img = image
        save_kwargs = {"format": "TIFF", "compression": "tiff_lzw", **_meta_kwargs(img, strip=strip_metadata)}

        if percent > 0 and not has_alpha(image):
            colors = _colors_from_percent(percent)
            pal = image.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
            save_img = pal

        if "exif" in save_kwargs:
            del save_kwargs["exif"]

        save_img.save(out_path, **save_kwargs)
        return str(out_path)

    # 6) Anything else
    out_path = out_dir_p / f"{src_path.stem}_compressed{src_path.suffix}"
    image.save(
        out_path,
        **_meta_kwargs(img, strip=strip_metadata),
    )
    return str(out_path)


def resize_image(src: str, out_dir: str, *, scale_percent: int, strip_metadata: bool = False) -> str:
    p = max(1, int(scale_percent))
    src_path = Path(src)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    img = safe_open(src_path)
    if img is None:
        raise RuntimeError(f"Не удалось открыть изображение: {src_path}")

    image = ImageOps.exif_transpose(img)

    w, h = image.size
    new_w = max(1, (w * p) // 100)
    new_h = max(1, (h * p) // 100)
    image_resize = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    ext = src_path.suffix.lower()
    # 1) JPEG
    if ext in {".jpg", ".jpeg"}:
        out_path = out_dir_p / f"{src_path.stem}_resized.jpg"
        image_resize.convert("RGB").save(
            out_path,
            format="JPEG",
            quality=85,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
            **_meta_kwargs(img, strip=strip_metadata),
        )
        return str(out_path)

    # 2) WEBP
    if ext == ".webp":
        out_path = out_dir_p / f"{src_path.stem}_resized.webp"
        image_resize.convert("RGB").save(
            out_path,
            format="WEBP",
            quality=85,
            method=6,
            **_meta_kwargs(img, strip=strip_metadata),
        )
        return str(out_path)

    # 3) PNG
    if ext == ".png":
        out_path = out_dir_p / f"{src_path.stem}_resized.png"
        image_resize.save(
            out_path,
            format="PNG",
            optimize=True,
            compress_level=9,
            **_meta_kwargs(img, strip=strip_metadata),
        )
        return str(out_path)

    # 4) TIFF
    if ext in {".tif", ".tiff"}:
        out_path = out_dir_p / f"{src_path.stem}_resized.tiff"
        kwargs = {"format": "TIFF", "compression": "tiff_lzw", **_meta_kwargs(img, strip=strip_metadata)}
        if "exif" in kwargs:
            del kwargs["exif"]
        image_resize.save(out_path, **kwargs)
        return str(out_path)

    # 5) anything else
    out_path = out_dir_p / f"{src_path.stem}_resized{src_path.suffix}"
    image_resize.save(out_path, **_meta_kwargs(img, strip=strip_metadata))
    return str(out_path)

TargetFmt = Literal["jpeg", "png", "webp", "tiff"]

@dataclass
class ConvertOptions:
    target: TargetFmt
    apply_percent: Optional[int] = None
    strip_metadata: bool = False
    jpeg_progressive: bool = True
    jpeg_subsampling: str = "4:2:0"
    webp_lossless: bool = False
    tiff_compression: str = "tiff_lzw"


# to get EXIF/ICC
def _meta_kwargs(img: Image.Image, strip: bool) -> dict:
    if strip:
        return {}
    kw = {}
    if "exif" in img.info:
        kw["exif"] = img.info["exif"]
    if "icc_profile" in img.info:
        kw["icc_profile"] = img.info["icc_profile"]
    return kw


# for transparency to white
def _flatten_to_rgb(img: Image.Image, bg=(255, 255, 255)) -> Image.Image:
    if img.mode in ("RGBA", "LA") or has_alpha(img):
        base = Image.new("RGB", img.size, bg)
        base.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        return base
    return img.convert("RGB")


# anim detect
def _is_animated(img: Image.Image) -> bool:
    return bool(getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1)


def _to_jpeg(img: Image.Image, out_path: Path, quality: int, opts: ConvertOptions) -> None:
    exif_kw = {}
    if not opts.strip_metadata:
        exif_bytes = _exif_without_orientation(img)
        if exif_bytes:
            exif_kw["exif"] = exif_bytes
        if "icc_profile" in img.info:
            exif_kw["icc_profile"] = img.info["icc_profile"]

    ImageOps.exif_transpose(_flatten_to_rgb(img)).save(
        out_path,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=opts.jpeg_progressive,
        subsampling=opts.jpeg_subsampling,
        **exif_kw,
    )

def _to_png(img: Image.Image, out_path: Path, opts: ConvertOptions, apply_percent: Optional[int] = None) -> None:
    image = ImageOps.exif_transpose(img)

    if apply_percent is not None and not has_alpha(image):
        p = max(0, min(100, int(apply_percent)))
        colors = max(16, min(256, int(256 - p * (256 - 16) / 100)))
        pal = image.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        pal.save(
            out_path,
            format="PNG",
            optimize=True,
            compress_level=9,
            **_meta_kwargs(img, strip=opts.strip_metadata),
        )
        return

    image.save(
        out_path,
        format="PNG",
        optimize=True,
        compress_level=9,
        **_meta_kwargs(img, strip=opts.strip_metadata),
    )

def _to_webp(img: Image.Image, out_path: Path, quality: Optional[int], opts: ConvertOptions) -> None:
    meta_kw = {}
    if not opts.strip_metadata and "icc_profile" in img.info:
        meta_kw["icc_profile"] = img.info["icc_profile"]

    if opts.webp_lossless:
        ImageOps.exif_transpose(img).save(
            out_path,
            format="WEBP",
            lossless=True,
            method=6,
            **meta_kw,
        )
    else:
        q = 80 if quality is None else max(1, min(95, int(quality)))
        ImageOps.exif_transpose(_flatten_to_rgb(img)).save(
            out_path,
            format="WEBP",
            quality=q,
            method=6,
            **meta_kw,
        )

def _to_tiff(img: Image.Image, out_path: Path, opts: ConvertOptions) -> None:
    comp = opts.tiff_compression if opts.tiff_compression in ("tiff_lzw", "raw") else "tiff_lzw"
    ImageOps.exif_transpose(img).save(
        out_path,
        format="TIFF",
        compression=comp,
        **({"icc_profile": img.info["icc_profile"]} if not opts.strip_metadata and "icc_profile" in img.info else {}),
    )

ORIENTATION_TAG = 274  # EXIF Orientation

def _exif_without_orientation(img: Image.Image) -> bytes | None:
    try:
        exif = img.getexif()
        if ORIENTATION_TAG in exif:
            del exif[ORIENTATION_TAG]
        data = exif.tobytes()
        return data if data else None
    except Exception:
        return None


def convert_image_format(src: str, out_dir: str, options: ConvertOptions, *, on_animated_confirm: Optional[Callable[[], bool]] = None) -> str:
    src_path = Path(src)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)

    img = safe_open(src_path)
    if img is None:
        raise RuntimeError(f"Не удалось открыть: {src_path}")

    if _is_animated(img):
        if on_animated_confirm is not None:
            if not on_animated_confirm():
                raise RuntimeError("Пользователь отменил обработку анимации")
        try:
            img.seek(0) # first frame
        except Exception:
            pass

    suffix_map = {"jpeg": ".jpg", "png": ".png", "webp": ".webp", "tiff": ".tiff"}
    ext = suffix_map.get(options.target, ".jpg")
    out_path = out_dir_p / f"{src_path.stem}_to{options.target}{ext}"

    q: Optional[int] = None
    if options.apply_percent is not None:
        q = percent_to_jpeg_quality(options.apply_percent)
        if q is None:
            q = 73

    target = options.target
    if target == "jpeg":
        _to_jpeg(img, out_path, quality=q if q is not None else 95, opts=options)
    elif target == "png":
        _to_png(img, out_path, opts=options, apply_percent=options.apply_percent)
    elif target == "webp":
        _to_webp(img, out_path, quality=q, opts=options)
    elif target == "tiff":
        _to_tiff(img, out_path, opts=options)
    else:
        raise ValueError(f"Неизвестный формат: {target}")

    return str(out_path)

