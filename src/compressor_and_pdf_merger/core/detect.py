from __future__ import annotations
from pathlib import Path
import os, sys, shutil, platform

def find_ffmpeg() -> str | None:
    p = shutil.which("ffmpeg")
    if p:
        return p

    winget_path = Path.home() / r"AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0-full_build/bin/ffmpeg.exe"
    if winget_path.exists():
        return str(winget_path)

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    if platform.system() == "Windows":
        bundled = base / "vendor" / "ffmpeg" / "bin" / "ffmpeg.exe"
    else:
        bundled = base / "vendor" / "ffmpeg" / "ffmpeg"
    if bundled.exists():
        return str(bundled)

    return None
