# src/compressor_and_pdf_merger/core/detect.py
from __future__ import annotations
from pathlib import Path
import os
import sys
import shutil
import subprocess
from functools import lru_cache


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def _vendor_bin() -> Path:
    return _bundle_root() / "vendor" / "ffmpeg" / "bin"


def _norm(p: str | Path | None) -> str | None:
    if not p:
        return None
    q = Path(p)
    return str(q.resolve()) if q.exists() else None


def _which(name: str) -> str | None:
    return _norm(shutil.which(name))


def _win_extra_candidates(name: str) -> list[str]:
    home = Path.home()
    cands: list[Path] = []

    winget_root = home / r"AppData/Local/Microsoft/WinGet/Packages"
    if winget_root.exists():
        for d in winget_root.glob("**/ffmpeg*/**/bin"):
            exe = d / (name + ".exe")
            if exe.exists():
                cands.append(exe)

    scoop_root = home / "scoop/apps"
    if scoop_root.exists():
        for d in scoop_root.glob("ffmpeg*/current/bin"):
            exe = d / (name + ".exe")
            if exe.exists():
                cands.append(exe)

    choco_root = Path(r"C:\ProgramData\chocolatey\bin")
    if choco_root.exists():
        exe = choco_root / (name + ".exe")
        if exe.exists():
            cands.append(exe)

    return [str(x) for x in cands]


def _candidates(name: str) -> list[str]:
    ext = ".exe" if os.name == "nt" else ""
    bundle = _vendor_bin() / f"{name}{ext}"
    cands: list[str] = []
    cands.append(str(bundle))
    p = _which(name)
    if p:
        cands.append(p)
    if os.name == "nt":
        cands.extend(_win_extra_candidates(name))
    return cands


def _best(name: str) -> str | None:
    for c in _candidates(name):
        if Path(c).exists():
            return c
    return None


@lru_cache(maxsize=None)
def get_ffmpeg_path() -> str:
    p = _best("ffmpeg")
    if not p:
        raise FileNotFoundError("ffmpeg not found (vendor/ffmpeg/bin, PATH, or common install dirs)")
    return p


@lru_cache(maxsize=None)
def get_ffprobe_path() -> str:
    p = _best("ffprobe")
    if not p:
        raise FileNotFoundError("ffprobe not found (vendor/ffmpeg/bin, PATH, or common install dirs)")
    return p


def check_ffmpeg_ok(timeout: int = 5) -> bool:
    try:
        subprocess.run([get_ffmpeg_path(), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        subprocess.run([get_ffprobe_path(), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return True
    except Exception:
        return False
