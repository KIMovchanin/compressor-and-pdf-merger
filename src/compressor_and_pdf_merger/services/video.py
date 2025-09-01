from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, subprocess, shutil
from typing import Optional


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
    ffprobe = ffprobe_bin or _which("ffprobe")
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
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "ffmpeg error")


def _ensure_even(x: int) -> int:
    return x if x % 2 == 0 else x - 1


def _scaled_by_height(info: VideoInfo, target_h: int) -> tuple[int, int]:
    h = max(1, min(target_h, info.height or target_h))
    w = int(round((info.width * h) / max(1, info.height)))
    return _ensure_even(max(2, w)), _ensure_even(max(2, h))


def compress_video_crf(src: str, out_dir: str, *, crf: int = 28, preset: str = "slow", codec: str = "h265",
                       audio_bitrate: str = "128k", strip_metadata: bool = True, target_fps: float | None = None,
                       target_height_p: int | None = None, scale_percent: int | None = None, ffmpeg_bin: Optional[str] = None) -> str:

    ffmpeg = ffmpeg_bin or _which("ffmpeg")
    src_p = Path(src)
    out_p = Path(out_dir); out_p.mkdir(parents=True, exist_ok=True)

    info = probe_video(src)
    vcodec = "libx265" if codec.lower() in ("h265", "hevc") else "libx264"
    vtag = ["-tag:v", "hvc1"] if vcodec == "libx265" else []
    common_flags = ["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    meta_flags = ["-map_metadata", "-1"] if strip_metadata else []

    vf_parts: list[str] = []
    if target_height_p:
        new_w, new_h = _scaled_by_height(info, max(1, target_height_p))
        vf_parts.append(f"scale={new_w}:{new_h}")
    elif scale_percent:
        p = max(1, scale_percent) / 100.0
        new_w = _ensure_even(max(2, int((info.width or 2) * p)))
        new_h = _ensure_even(max(2, int((info.height or 2) * p)))
        vf_parts.append(f"scale={new_w}:{new_h}")

    vf_opts = ["-vf", ",".join(vf_parts)] if vf_parts else []

    fps_opts: list[str] = []
    if target_fps is not None:
        base_fps = info.fps if info.fps > 0 else target_fps
        tfps = max(1.0, min(float(target_fps), float(base_fps)))
        fps_opts = ["-r", f"{tfps:.3f}"]

    out_file = out_p / f"{src_p.stem}_{codec}crf{crf}.mp4"
    cmd = [
        ffmpeg, "-y",
        "-i", str(src_p),
        *meta_flags,
        *fps_opts,
        *vf_opts,
        "-c:v", vcodec,
        "-preset", preset,
        "-crf", str(crf),
        *vtag,
        *common_flags,
        "-c:a", "aac", "-b:a",
        audio_bitrate,
        str(out_file)
    ]
    _run_ffmpeg(cmd)
    return str(out_file)


def resize_video_percent(src: str, out_dir: str, *, percent: int, ffmpeg_bin: Optional[str] = None) -> str:
    p = max(1, percent) / 100.0
    info = probe_video(src)
    new_w = _ensure_even(max(2, int(info.width * p)))
    new_h = _ensure_even(max(2, int(info.height * p)))

    ffmpeg = ffmpeg_bin or _which("ffmpeg")
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

    ffmpeg = ffmpeg_bin or _which("ffmpeg")
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
