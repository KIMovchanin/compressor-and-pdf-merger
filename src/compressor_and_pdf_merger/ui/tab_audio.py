from __future__ import annotations
from pathlib import Path
from typing import Optional
from os.path import isdir
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QFileDialog,
    QGroupBox, QLabel, QComboBox, QLineEdit, QMessageBox,
    QSpinBox, QDoubleSpinBox, QFormLayout, QCheckBox
)
from compressor_and_pdf_merger.services.audio import compress_audio
from compressor_and_pdf_merger.storage import db
from compressor_and_pdf_merger.services.settings import Settings


class AudioTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        root = QVBoxLayout(self)

        grp_enc = QGroupBox("Сжатие аудио")
        enc = QFormLayout()

        # Codec
        self.cmb_codec = QComboBox()
        self.cmb_codec.addItems(["Opus", "AAC", "MP3", "FLAC"])
        self.cmb_codec.setCurrentText("MP3")
        enc.addRow(QLabel("Кодек:"), self.cmb_codec)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["CBR", "VBR"])
        self.cmb_mode.setCurrentText("CBR")
        enc.addRow(QLabel("Режим битрейта:"), self.cmb_mode)

        # bitrate
        self.sp_bitrate = QSpinBox()
        self.sp_bitrate.setRange(1, 512)
        self.sp_bitrate.setSingleStep(8)
        self.sp_bitrate.setValue(96)
        enc.addRow(QLabel("Битрейт (кбит/с):"), self.sp_bitrate)

        # quality mp3
        self.sp_vbr_quality = QSpinBox()
        self.sp_vbr_quality.setRange(0, 9)  # 0 better, 9 worse
        self.sp_vbr_quality.setValue(2)
        self.sp_vbr_quality.setEnabled(False)
        enc.addRow(QLabel("VBR качество (MP3):"), self.sp_vbr_quality)

        # Sampling frequency
        self.cmb_sr = QComboBox()
        self.cmb_sr.addItems(["Авто", "44100", "48000"])
        self.cmb_sr.setCurrentText("48000")
        enc.addRow(QLabel("Частота (Гц):"), self.cmb_sr)

        # Channels
        self.cmb_channels = QComboBox()
        self.cmb_channels.addItems(["Авто", "Моно (1)", "Стерео (2)"])
        self.cmb_channels.setCurrentText("Стерео (2)")
        enc.addRow(QLabel("Каналы:"), self.cmb_channels)

        grp_enc.setLayout(enc)
        root.addWidget(grp_enc)

        grp_fx = QGroupBox("Нормализация и фильтры")
        fx = QFormLayout()

        # LUFS
        self.cb_norm = QCheckBox("Нормализовать громкость (EBU R128)")
        self.dsp_lufs = QDoubleSpinBox()
        self.dsp_lufs.setRange(-35.0, -5.0)
        self.dsp_lufs.setSingleStep(0.5)
        self.dsp_lufs.setDecimals(1)
        self.dsp_lufs.setValue(-16.0)
        self.dsp_lufs.setEnabled(False)
        self.cb_norm.toggled.connect(self.dsp_lufs.setEnabled)
        fx.addRow(self.cb_norm, self.dsp_lufs)

        # High-pass
        self.cb_hpass = QCheckBox("High-pass (срез низа)")
        self.sp_hpass = QSpinBox()
        self.sp_hpass.setRange(20, 500)
        self.sp_hpass.setValue(100)
        self.sp_hpass.setEnabled(False)
        self.cb_hpass.toggled.connect(self.sp_hpass.setEnabled)
        fx.addRow(self.cb_hpass, self.sp_hpass)

        # Low-pass
        self.cb_lpass = QCheckBox("Low-pass (срез верха)")
        self.sp_lpass = QSpinBox()
        self.sp_lpass.setRange(4000, 20000)
        self.sp_lpass.setValue(18000)
        self.sp_lpass.setEnabled(False)
        self.cb_lpass.toggled.connect(self.sp_lpass.setEnabled)
        fx.addRow(self.cb_lpass, self.sp_lpass)

        # Removing silence
        self.cb_trim = QCheckBox("Удалять тишину в начале/конце")
        fx.addRow(self.cb_trim)

        self.cb_ensure = QCheckBox("Не больше исходного файла")
        self.cb_ensure.setChecked(True)
        fx.addRow(self.cb_ensure)

        grp_fx.setLayout(fx)
        root.addWidget(grp_fx)

        row_btns = QHBoxLayout()
        self.btn_add = QPushButton("Добавить аудио")
        self.btn_remove = QPushButton("Удалить выбранное")
        self.btn_clear = QPushButton("Очистить список")
        row_btns.addWidget(self.btn_add)
        row_btns.addWidget(self.btn_remove)
        row_btns.addWidget(self.btn_clear)
        root.addLayout(row_btns)

        self.list = QListWidget()
        root.addWidget(self.list)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Папка для сохранения...")
        self.btn_out = QPushButton("Выбрать")
        out_row.addWidget(self.ed_out, 1)
        out_row.addWidget(self.btn_out)
        root.addLayout(out_row)

        if Settings and hasattr(Settings, "audio_default_dir"):
            default_dir = Settings.audio_default_dir() or ""
            if default_dir and not self.ed_out.text().strip():
                self.ed_out.setText(default_dir)

        self.btn_run = QPushButton("Сжать")
        root.addWidget(self.btn_run)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)
        self.btn_clear.clicked.connect(self.list.clear)
        self.btn_out.clicked.connect(self._on_choose_out)
        self.btn_run.clicked.connect(self._on_run)

        self.cmb_codec.currentTextChanged.connect(self._refresh_fields_enabled)
        self.cmb_mode.currentTextChanged.connect(self._refresh_fields_enabled)
        self._refresh_fields_enabled()


    def _refresh_fields_enabled(self):
        codec = self.cmb_codec.currentText().lower()
        mode = self.cmb_mode.currentText().lower()

        if codec == "flac":
            self.cmb_mode.setEnabled(False)
            self.sp_bitrate.setEnabled(False)
            self.sp_vbr_quality.setEnabled(False)
        elif codec == "mp3":
            self.cmb_mode.setEnabled(True)
            if mode == "vbr":
                self.sp_vbr_quality.setEnabled(True)
                self.sp_bitrate.setEnabled(False)
            else:
                self.sp_vbr_quality.setEnabled(False)
                self.sp_bitrate.setEnabled(True)
        else:
            self.cmb_mode.setEnabled(True)
            self.sp_bitrate.setEnabled(True)
            self.sp_vbr_quality.setEnabled(False)


    def _selected_files(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]


    def _get_files_and_outdir(self) -> tuple[list[str], str] | None:
        files = self._selected_files()
        if not files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте хотя бы один файл.")
            return None
        out_dir = self.ed_out.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Нет папки", "Выберите папку для сохранения.")
            return None
        if not isdir(out_dir):
            QMessageBox.warning(self, "Папка не найдена", "Указанная папка не существует.")
            return None
        return files, out_dir


    def _log_and_emit(self, text: str, src_name: str, out_path: str) -> None:
        db.add_history(tab="Аудио", action="Сжатие", src_name=src_name, out_path=out_path)
        self.entry_logged.emit(text)


    def _on_add(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбрать аудио", "",
            "Аудио (*.mp3 *.m4a *.aac *.flac *.wav *.ogg *.opus *.wma)"
        )
        for f in files:
            self.list.addItem(f)


    def _on_remove(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))


    def _on_choose_out(self):
        d = QFileDialog.getExistingDirectory(self, "Куда сохранить?", self.ed_out.text() or "")
        if d:
            self.ed_out.setText(d)
            if Settings and hasattr(Settings, "set_audio_default_dir"):
                Settings.set_audio_default_dir(d)


    def _on_run(self):
        data = self._get_files_and_outdir()
        if not data:
            return
        files, out_dir = data

        codec = self.cmb_codec.currentText().lower()
        mode = self.cmb_mode.currentText().lower()
        bitrate_kbps = int(self.sp_bitrate.value())
        vbr_quality = int(self.sp_vbr_quality.value()) if self.sp_vbr_quality.isEnabled() else None

        # sample rate
        sr_txt = self.cmb_sr.currentText()
        sample_rate = None if sr_txt == "Авто" else int(sr_txt)

        # channels
        ch_txt = self.cmb_channels.currentText()
        if ch_txt.startswith("Моно"):
            channels = 1
        elif ch_txt.startswith("Стерео"):
            channels = 2
        else:
            channels = None

        normalize_lufs = float(self.dsp_lufs.value()) if self.cb_norm.isChecked() else None
        highpass_hz = int(self.sp_hpass.value()) if self.cb_hpass.isChecked() else None
        lowpass_hz = int(self.sp_lpass.value()) if self.cb_lpass.isChecked() else None
        trim_silence = self.cb_trim.isChecked()
        ensure_not_larger = self.cb_ensure.isChecked()

        try:
            outp = compress_audio(
                files[0], out_dir,
                codec=codec,
                mode=mode,
                bitrate_kbps=bitrate_kbps,
                vbr_quality=vbr_quality if (codec == "mp3" and mode == "vbr") else None,
                sample_rate=sample_rate,
                channels=channels,
                normalize_lufs=normalize_lufs,
                highpass_hz=highpass_hz,
                lowpass_hz=lowpass_hz,
                trim_silence=trim_silence,
                ensure_not_larger=ensure_not_larger
            )

            name = Path(files[0]).name
            desc = [
                f"codec={self.cmb_codec.currentText()}",
                f"mode={self.cmb_mode.currentText()}",
            ]
            if self.sp_bitrate.isEnabled():
                desc.append(f"br={bitrate_kbps}k")
            if self.sp_vbr_quality.isEnabled():
                desc.append(f"vbr_q={vbr_quality}")
            if sample_rate:
                desc.append(f"sr={sample_rate}")
            if channels:
                desc.append(f"ch={channels}")
            if normalize_lufs is not None:
                desc.append(f"lufs={normalize_lufs}")
            if highpass_hz:
                desc.append(f"hp={highpass_hz}")
            if lowpass_hz:
                desc.append(f"lp={lowpass_hz}")
            if trim_silence:
                desc.append("trim")
            if ensure_not_larger:
                desc.append("≤src")

            text = f"Из вкладки «Аудио»: {'; '.join(desc)}\n\"{name}\" -> \"{outp}\""
            self._log_and_emit(text, name, outp)

            QMessageBox.information(self, "Готово", text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
