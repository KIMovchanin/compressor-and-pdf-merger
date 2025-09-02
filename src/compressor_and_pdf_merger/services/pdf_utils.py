from __future__ import annotations
import shutil, subprocess, tempfile, os
from pathlib import Path
from typing import Optional


def which(name: str) -> Optional[str]:
    return shutil.which(name)


def require(name: str) -> str:
    p = which(name)
    if not p:
        raise RuntimeError(f"Не найден инструмент: {name}. Установите или укажите путь в настройках.")
    return p


def run(cmd: list[str], tool: str) -> None:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        raise RuntimeError(f"Не удалось запустить {tool}: {e}") from e
    if p.returncode != 0:
        err = (p.stderr or p.stdout or "").strip()
        raise RuntimeError(f"{tool} завершился с ошибкой ({p.returncode}):\n{err[:4000]}")


def tmp_path(suffix: str) -> Path:
    fd, p = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return Path(p)
