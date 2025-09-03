from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, subprocess, shutil, os
from typing import Optional
from compressor_and_pdf_merger.core.detect import get_ffmpeg_path, get_ffprobe_path


def _which(bin_name: str) -> str:
    p = shutil.which(bin_name)
    if not p:
        raise RuntimeError(f"Не найден исполняемый файл: {bin_name}. Проверьте установку FFmpeg/FFprobe и PATH.")
    return p


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: float
    vcodec: str
    has_audio: bool
    duration: float


def probe_video(src: str, *, ffprobe_bin: Optional[str] = None) -> VideoInfo:
    ffprobe = ffprobe_bin or get_ffprobe_path()
    cmd = [
        ffprobe, "-v", "error",
        "-print_format", "json",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,codec_name",
        "-show_entries", "format=duration",
        src
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "ffprobe error")

    data = json.loads(res.stdout)
    v = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}

    def _fps(fr: str) -> float:
        # avg_frame_rate like "30000/1001" → 29.97
        if not fr or fr == "0/0":
            return 0.0
        num, den = fr.split("/")
        den = float(den) if float(den) != 0 else 1.0
        return float(num) / den

    width  = int(v.get("width") or 0)
    height = int(v.get("height") or 0)
    fps    = _fps(v.get("avg_frame_rate") or "")
    vcodec = str(v.get("codec_name") or "")
    duration = float(fmt.get("duration") or 0)

    has_audio = False
    try:
        res_a = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", src],
            capture_output=True, text=True
        )
        has_audio = (res_a.returncode == 0) and (res_a.stdout.strip() != "")
    except Exception:
        pass

    return VideoInfo(width=width, height=height, fps=fps, vcodec=vcodec, has_audio=has_audio, duration=duration)


def _run_ffmpeg(cmd: list[str]) -> None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        raise RuntimeError(f"Не удалось запустить ffmpeg: {e}") from e

    if proc.returncode != 0:
        stderr_lines = (proc.stderr or proc.stdout or "").splitlines()
        msg = "\n".join(stderr_lines[:20])
        raise RuntimeError(f"FFmpeg завершился с ошибкой (код {proc.returncode}):\n{msg}")


def _ensure_even(x: int) -> int:
    return x if x % 2 == 0 else x - 1


def _scaled_by_height(info: VideoInfo, target_h: int) -> tuple[int, int]:
    h = max(1, min(target_h, info.height or target_h))
    w = int(round((info.width * h) / max(1, info.height)))
    return _ensure_even(max(2, w)), _ensure_even(max(2, h))


_PRESET_ORDER = [
    "ultrafast","superfast","veryfast","faster","fast",
    "medium","slow","slower","veryslow"
]

def _bump_preset(preset: str, target: str = "slower") -> str:
    if preset not in _PRESET_ORDER or target not in _PRESET_ORDER:
        return preset
    i = _PRESET_ORDER.index(preset)
    j = _PRESET_ORDER.index(target)
    return _PRESET_ORDER[j] if i < j else preset  # если текущий быстрее — двинем к "slower"

def compress_video_crf(
    src: str,
    out_dir: str,
    *,
    crf: int = 28,
    preset: str = "slow",
    codec: str = "h265",
    audio_bitrate: str = "128k",
    strip_metadata: bool = True,
    target_fps: float | None = None,
    target_height_p: int | None = None,
    scale_percent: int | None = None,
    ffmpeg_bin: Optional[str] = None,
    # Новые параметры-гарантии
    ensure_not_larger: bool = True,
    min_shrink_ratio: float = 0.98,
    retry_crf_step: int = 3,
    max_crf: int = 35,
    bump_to_preset: str = "slower"
) -> str:
    ffmpeg = ffmpeg_bin or get_ffmpeg_path()
    src_p = Path(src)
    out_p = Path(out_dir); out_p.mkdir(parents=True, exist_ok=True)
    info = probe_video(src, ffprobe_bin=get_ffprobe_path())

    tfps = None
    if target_fps:
        base_fps = info.fps if info.fps > 0 else target_fps
        tfps = max(1.0, min(float(target_fps), base_fps))

    new_w = new_h = None
    if target_height_p:
        new_w, new_h = _scaled_by_height(info, max(1, int(target_height_p)))
    elif scale_percent:
        p = max(1, int(scale_percent)) / 100.0
        new_w = _ensure_even(max(2, int((info.width or 2)  * p)))
        new_h = _ensure_even(max(2, int((info.height or 2) * p)))

    vcodec = "libx265" if codec.lower() in ("h265", "hevc") else "libx264"
    vtag = ["-tag:v", "hvc1"] if vcodec == "libx265" else []
    common_flags = ["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    meta_flags = ["-map_metadata", "-1"] if strip_metadata else []

    vf_parts = []
    if new_w and new_h:
        vf_parts.append(f"scale={new_w}:{new_h}")
    vf_opts = ["-vf", ",".join(vf_parts)] if vf_parts else []
    fps_opts = ["-r", f"{tfps:.3f}"] if tfps else []

    def build_cmd(out_path: Path, crf_val: int, preset_val: str) -> list[str]:
        return [
            ffmpeg, "-y",
            "-i", str(src_p),
            *fps_opts,
            *vf_opts,
            *meta_flags,
            "-c:v", vcodec,
            "-preset", preset_val,
            "-crf", str(crf_val),
            *vtag,
            *common_flags,
            "-c:a", "aac", "-b:a", audio_bitrate,
            str(out_path)
        ]

    suffix = f"crf{crf}_{preset}_{'hevc' if vcodec=='libx265' else 'h264'}"
    if new_h: suffix += f"_{new_h}p"
    elif scale_percent: suffix += f"_{scale_percent}pct"
    if tfps: suffix += f"_fps{int(tfps)}"

    final_file = out_p / f"{src_p.stem}_{suffix}.mp4"
    tmp_file   = out_p / f"{src_p.stem}_{suffix}.tmp.mp4"

    try:
        cmd = build_cmd(tmp_file, crf, preset)
        _run_ffmpeg(cmd)
    except Exception as e:
        if tmp_file.exists():
            try: tmp_file.unlink()
            except: pass
        raise

    src_size = src_p.stat().st_size
    out_size = tmp_file.stat().st_size if tmp_file.exists() else 0

    if ensure_not_larger and src_size > 0:
        target_max = int(src_size * min_shrink_ratio)
        try_crf = crf
        try_preset = preset

        first_retry = True
        while out_size >= target_max and try_crf < max_crf:
            try:
                if tmp_file.exists():
                    tmp_file.unlink()
            except: pass

            if first_retry:
                new_preset = _bump_preset(try_preset, bump_to_preset)
                first_retry = False
                if new_preset != try_preset:
                    try_preset = new_preset
                else:
                    try_crf += retry_crf_step
            else:
                try_crf += retry_crf_step

            cmd = build_cmd(tmp_file, try_crf, try_preset)
            _run_ffmpeg(cmd)
            out_size = tmp_file.stat().st_size

    try:
        if final_file.exists():
            final_file.unlink()
        os.replace(tmp_file, final_file)
    except Exception:
        import shutil as _sh
        _sh.copyfile(tmp_file, final_file)
        try: tmp_file.unlink()
        except: pass

    return str(final_file)


def resize_video_percent(src: str, out_dir: str, *, percent: int, ffmpeg_bin: Optional[str] = None) -> str:
    p = max(1, percent) / 100.0
    info = probe_video(src)
    new_w = _ensure_even(max(2, int(info.width * p)))
    new_h = _ensure_even(max(2, int(info.height * p)))

    ffmpeg = ffmpeg_bin or get_ffmpeg_path()
    src_p = Path(src)
    out_p = Path(out_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    out_file = out_p / f"{src_p.stem}_scale{percent}.mp4"

    vf = f"scale={new_w}:{new_h}"
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src_p),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-crf", "23",
        "-preset",
        "medium",
        "-movflags",
        "+faststart",
        "-c:a",
        "copy",
        str(out_file)
    ]
    _run_ffmpeg(cmd)
    return str(out_file)


def change_fps_down(src: str, out_dir: str, *, target_fps: float, ffmpeg_bin: Optional[str] = None) -> str:
    info = probe_video(src)
    tfps = min(float(target_fps), info.fps if info.fps > 0 else target_fps)

    ffmpeg = ffmpeg_bin or get_ffmpeg_path()
    src_p = Path(src)
    out_p = Path(out_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    out_file = out_p / f"{src_p.stem}_fps{int(tfps)}.mp4"

    cmd = [
        ffmpeg, "-y",
        "-i", str(src_p),
        "-r", f"{tfps:.3f}",
        "-c:v", "libx264", "-crf", "23", "-preset", "medium",
        "-movflags", "+faststart",
        "-c:a", "copy",
        str(out_file)
    ]
    _run_ffmpeg(cmd)
    return str(out_file)
