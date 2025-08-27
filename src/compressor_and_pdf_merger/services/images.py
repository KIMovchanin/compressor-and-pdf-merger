from pathlib import Path
import shutil

def compress_image_stub(src: str, out_dir: str, percent: int) -> str:
    src_path = Path(src)
    out_path = Path(out_dir) / f"{src_path.stem}_compressed{src_path.suffix}"
    shutil.copy(src_path, out_path)
    return str(out_path)
