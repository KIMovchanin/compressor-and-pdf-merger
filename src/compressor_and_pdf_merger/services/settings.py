from PyQt6.QtCore import QSettings, QByteArray
from compressor_and_pdf_merger.storage.db import APP_NAME, APP_AUTHOR

class Settings:
    _s = QSettings(APP_AUTHOR, APP_NAME)

    @classmethod
    def window_geometry(cls) -> QByteArray | None:
        val = cls._s.value("ui/window_geometry", None)
        if val is None:
            return None
        if isinstance(val, QByteArray):
            return val
        if isinstance(val, (bytes, bytearray)):
            return QByteArray(val)
        if isinstance(val, str):
            try:
                return QByteArray.fromBase64(val.encode("utf-8"))
            except Exception:
                return None

        cls._s.remove("ui/window_geometry")
        return None

    @classmethod
    def set_window_geometry(cls, data: QByteArray | bytes | bytearray) -> None:
        if not isinstance(data, QByteArray):
            data = QByteArray(data)
        cls._s.setValue("ui/window_geometry", data)

    @classmethod
    def images_default_dir(cls) -> str:
        return cls._s.value("images/default_out_dir", "", type=str)

    @classmethod
    def set_images_default_dir(cls, path: str) -> None:
        cls._s.setValue("images/default_out_dir", path)

    @classmethod
    def images_strip_meta(cls) -> bool:
        return cls._s.value("images/strip_meta", False, type=bool)

    @classmethod
    def set_images_strip_meta(cls, v: bool) -> None:
        cls._s.setValue("images/strip_meta", v)

    @classmethod
    def images_mode(cls) -> str:
        # "min" / "max" / "custom"
        return cls._s.value("images/mode", "min", type=str)

    @classmethod
    def set_images_mode(cls, mode: str) -> None:
        cls._s.setValue("images/mode", mode)

    @classmethod
    def images_percent(cls) -> int:
        return cls._s.value("images/percent", 20, type=int)

    @classmethod
    def set_images_percent(cls, p: int) -> None:
        cls._s.setValue("images/percent", int(p))

    @classmethod
    def clear_window_geometry(cls) -> None:
        cls._s.remove("ui/window_geometry")

