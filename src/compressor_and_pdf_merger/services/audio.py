from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json, shutil, subprocess, os


def _which(bin_name: str) -> str:
    p = shutil.which(bin_name)
    if not p:
        raise RuntimeError(f"Не найден исполняемый файл: {bin_name}. Проверьте установку и PATH.")
    return p


def _run(cmd: list[str], tool: str) -> None:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        raise RuntimeError(f"Не удалось запустить {tool}: {e}") from e
    if p.returncode != 0:
        err = (p.stderr or p.stdout or "").splitlines()
        raise RuntimeError(f"{tool} завершился с ошибкой ({p.returncode}):\n" + "\n".join(err[:40]))


@dataclass(frozen=True)
class AudioInfo:
    codec: str
    sample_rate: int
    channels: int
    duration: float
    bit_rate: Optional[int]  # bps


def probe_audio(path: str | Path) -> AudioInfo:
    ffprobe = _which("ffprobe")
    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
        "-show_entries", "format=duration,bit_rate",
        "-of", "json", str(path)
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffprobe error:\n{p.stderr or p.stdout}")
    data = json.loads(p.stdout)
    st = data["streams"][0]
    fmt = data.get("format", {})
    sr = int(st.get("sample_rate", 0) or 0)
    ch = int(st.get("channels", 0) or 0)
    br = st.get("bit_rate") or fmt.get("bit_rate")
    br = int(br) if br and str(br).isdigit() else None
    dur = float(fmt.get("duration", 0.0) or 0.0)
    return AudioInfo(st.get("codec_name", ""), sr, ch, dur, br)


def compress_audio(
    src: str | Path,
    out_dir: str | Path,
    *,
    codec: str = "opus",
    mode: str = "cbr",
    bitrate_kbps: int = 96,
    vbr_quality: Optional[int] = None,
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    normalize_lufs: Optional[float] = None,
    highpass_hz: Optional[int] = None,
    lowpass_hz: Optional[int] = None,
    trim_silence: bool = False,
    ensure_not_larger: bool = True,
    min_shrink_ratio: float = 0.98,
    step_kbps: int = 16,
) -> str:

    ffmpeg = _which("ffmpeg")
    src_p = Path(src)
    out_p = Path(out_dir); out_p.mkdir(parents=True, exist_ok=True)

    _ = probe_audio(src_p)

    af = []
    if normalize_lufs is not None:
        af.append(f"loudnorm=I={normalize_lufs}:LRA=11:TP=-1.5")
    if highpass_hz:
        af.append(f"highpass=f={int(highpass_hz)}")
    if lowpass_hz:
        af.append(f"lowpass=f={int(lowpass_hz)}")
    if trim_silence:
        af.append(
            "silenceremove="
            "start_periods=1:start_duration=0.2:start_threshold=-50dB:"
            "stop_periods=1:stop_duration=0.8:stop_threshold=-50dB"
        )
    af_opts = ["-af", ",".join(af)] if af else []

    ac_opts: list[str] = []
    if sample_rate: ac_opts += ["-ar", str(int(sample_rate))]
    if channels:    ac_opts += ["-ac", str(int(channels))]

    c = codec.lower()

    if c == "opus":
        out_file = out_p / f"{src_p.stem}_opus_{bitrate_kbps}k.opus"
    elif c == "aac":
        out_file = out_p / f"{src_p.stem}_aac_{bitrate_kbps}k.m4a"
    elif c == "mp3":
        out_file = out_p / f"{src_p.stem}_mp3_{bitrate_kbps}k.mp3"
    elif c == "flac":
        out_file = out_p / f"{src_p.stem}_flac.flac"
    else:
        raise ValueError(f"Неизвестный кодек: {codec}")

    tmp = out_file.with_name(out_file.stem + ".__tmp__" + out_file.suffix)

    def make_cmd(kbps: int, force_mp3_cbr: bool = False) -> list[str]:
        common = [ffmpeg, "-y", "-i", str(src_p), *af_opts, *ac_opts]
        if c == "opus":
            vbr_flag = "on" if mode == "vbr" else "off"
            return common + [
                "-c:a", "libopus",
                "-b:a", f"{kbps}k",
                "-vbr", vbr_flag,
                "-compression_level", "10",
                "-application", "voip" if (channels == 1) else "audio",
                "-f", "opus",
                str(tmp),
            ]
        elif c == "aac":
            return common + [
                "-c:a", "aac",
                "-b:a", f"{kbps}k",
                "-f", "mp4",
                str(tmp),
            ]
        elif c == "mp3":
            if mode == "vbr" and not force_mp3_cbr and vbr_quality is not None:
                return common + [
                    "-c:a", "libmp3lame",
                    "-q:a", str(int(vbr_quality)),
                    "-f", "mp3",
                    str(tmp),
                ]
            else:
                return common + [
                    "-c:a", "libmp3lame",
                    "-b:a", f"{kbps}k",
                    "-f", "mp3",
                    str(tmp),
                ]
        elif c == "flac":
            return common + [
                "-c:a", "flac",
                "-compression_level", "8",
                "-f", "flac",
                str(tmp),
            ]
        else:
            raise ValueError(c)

    cmd = make_cmd(bitrate_kbps)
    _run(cmd, "ffmpeg")

    if ensure_not_larger and c in {"opus", "aac", "mp3"}:
        src_size = src_p.stat().st_size
        out_size = tmp.stat().st_size if tmp.exists() else 0
        target_max = int(src_size * min_shrink_ratio)

        cur_kbps = bitrate_kbps
        while out_size >= target_max and cur_kbps > 32:
            cur_kbps = max(32, cur_kbps - step_kbps)
            cmd = make_cmd(cur_kbps, force_mp3_cbr=(c == "mp3"))
            _run(cmd, "ffmpeg")
            out_size = tmp.stat().st_size

    if out_file.exists():
        out_file.unlink()
    os.replace(tmp, out_file)
    return str(out_file)
