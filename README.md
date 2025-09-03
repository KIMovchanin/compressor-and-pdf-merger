[Eng](#Eng) | [Rus](#Rus)


---

### Eng
# Compressor & PDF Merger v1.0.0

A fast, privacy-friendly **desktop tool (PyQt6)** for everyday file chores:

* 📄 **Merge** PDFs + Office docs (DOCX/XLSX/PPTX) + images into a single PDF (optionally normalized to **A4**).
* 🗜️ **Compress** PDFs (smart rasterization, metadata cleanup, “never larger than source” guard).
* 🔁 **Convert** PDF → Images (JPG/PNG), PDF → PPTX (slide snapshots), PDF → TXT (text extraction).
* 🖼️ **Batch image** resizing/compression and **format conversion** (JPEG/PNG/WebP/TIFF).
* 🎬 **Video compression** (H.264/H.265, CRF, presets, FPS cap, set height or scale %).
* 🎧 **Audio transcode** (Opus/AAC/MP3/FLAC), optional **EBU R128 (LUFS)** loudness normalization, filters.
* 🕘 **History** of actions in local SQLite; settings persisted between runs.

**Everything runs locally** — files are never uploaded anywhere.

---

## Table of Contents

* [What’s Inside (by tab)](#whats-inside-by-tab)

  * [PDF → Merge](#pdf--merge)
  * [PDF → Compress](#pdf--compress)
  * [PDF → Convert](#pdf--convert)
  * [Images](#images)
  * [Video](#video)
  * [Audio](#audio)
  * [History](#history)
  * [Settings](#settings)
* [Install (for end-users)](#install-for-end-users)
* [Quick Start](#quick-start)
* [System Requirements](#system-requirements)
* [External Tools](#external-tools)
* [Build From Source (dev)](#build-from-source-dev)

  * [Environment](#environment)
  * [Build EXE with PyInstaller](#build-exe-with-pyinstaller)
  * [Windows Installer (Inno Setup)](#windows-installer-inno-setup)
* [Where Data Is Stored](#where-data-is-stored)
* [FAQ](#faq)
* [Known Limitations](#known-limitations)
* [Roadmap](#roadmap)
* [License](#license)

---

## What’s Inside (by tab)

*Source code overview: UI under `src/compressor_and_pdf_merger/ui/…`, logic in `src/compressor_and_pdf_merger/services/…`, helpers in `core/` and `storage/`.*

### PDF → Merge

Files: `ui/tab_pdf_merge.py`, `services/pdf_merge.py`, `services/office_convert.py`, `services/pdf_utils.py`

* **Inputs**

  * PDF
  * Office docs (**DOC/DOCX, XLS/XLSX, PPT/PPTX**) → converted to PDF internally (DOCX via **mammoth → HTML → xhtml2pdf**, PPTX via **python-pptx**, XLSX via rendered tables).
  * Images (**JPG/PNG/WebP/TIFF/BMP**) → added as pages (EXIF rotation respected).
* **Ordering**: drag & drop in the list.
* **Output**: single PDF.
* **Options**:

  * **Normalize to A4** — all pages resized to A4 with white margins (margin size in mm).
* **Use cases**: combine scans, photos, lecture slides, and docs into one neat PDF.

> Note: Office→PDF conversion is “basic”—very complex layouts, rare fonts, or embedded objects may be simplified.

---

### PDF → Compress

Files: `ui/tab_pdf_compress.py`, `services/pdf_compress.py`

* **How it works**: pages can be **rasterized** via **PyMuPDF (fitz)**, then saved back with controlled image quality (**Pillow**).
* **Options**:

  * **Grayscale** (convert images to gray).
  * **Strip metadata/attachments** (via **pikepdf**).
  * **Never larger than source** — if the result grows, the original is kept.
* **Use cases**: significantly reduce size for email/printing/archiving.

---

### PDF → Convert

Files: `ui/tab_pdf_convert.py`, `services/pdf_convert.py`

* **Modes**:

  * **PDF → Images** (JPG/PNG) per page with DPI control.
  * **PDF → PPTX (snapshots)** — each page becomes a slide image.
  * **PDF → TXT** — text extraction (PyMuPDF).
* **Page ranges**: string like `1,3-5,10-` (spaces allowed).
  Examples: `5` (only page 5), `2-4` (2,3,4), `-3` (1..3), `10-` (10..end).

---

### Images

Files: `ui/tab_image.py`, `services/images.py`

* **Compression**: percentage slider.

  * JPEG → `quality` mapped from %;
  * PNG → compression/quantization;
  * WebP → `quality`.
* **Resize**: by percent or by target dimension (long edge/width/height).
* **Format convert**: **JPEG, PNG, WebP, TIFF**.
* **Metadata**: option to **remove EXIF** (GPS, camera, time).
* **Alpha**: converting to JPEG flattens transparency to white; PNG/WebP keep alpha.
* **Batch mode**: add multiple files/folders.

---

### Video

Files: `ui/tab_video.py`, `services/video.py`

* **Codecs**: **H.264 (libx264)** and **H.265/HEVC (libx265)**.
* **CRF** (quality): lower = better quality = larger file. Typical range **18–28**.
* **Preset**: `ultrafast … veryslow` (slower = better compression at same CRF).
* **Extras**:

  * **FPS cap** (e.g., 24/30) reduces size.
  * **Height in “p”** (e.g., 720p) keeps aspect ratio.
  * **Scale %** (25–100%) for quick downscaling.
  * **Audio**: AAC with bitrate (default 128k).
  * **faststart**, metadata stripping.
* **Size guards**: if output unexpectedly grows, fall back to the source (or enforce a minimum shrink ratio).
* **Filenames** include settings, e.g. `_crf24_slow_h264_720p_fps24`.

---

### Audio

Files: `ui/tab_audio.py`, `services/audio.py`

* **Codecs**: **Opus**, **AAC**, **MP3**, **FLAC**.
* **Modes**: **CBR** (fixed bitrate); MP3 also supports **VBR** (quality).
* **Params**: bitrate/quality, sample rate (44.1/48 kHz), channels (Auto/Mono/Stereo).
* **Normalization**: **EBU R128 (LUFS)** — target loudness level (e.g., −16 LUFS).
* **Filters**: **High-pass**, **Low-pass**, **trim silence**.
* **“Never larger than source”** protection available.

---

### History

Files: `ui/tab_history.py`, `storage/db.py`

* Keeps recent operations (up to 500): tab, action, input/output paths, timestamp.
* **Clear History** button.
* SQLite DB stored in user profile (see [Where Data Is Stored](#where-data-is-stored)).

---

### Settings

Files: `ui/tab_settings.py`, `services/settings.py`

* Default folders for images/PDF/video/audio.
* Paths to external tools: **ffmpeg**, **ffprobe** (and optional Ghostscript).
* Default OCR language (reserved for future).
* Window geometry persisted via **QSettings**.

---

## Install (for end-users)

1. Download `Compressor & PDF Merger_Setup_*.exe` from Releases.
2. Run the installer and choose an **install folder**.
3. Optionally tick **Create Desktop Shortcut**.
4. Launch the app after install.

> If video/audio tabs say *ffmpeg/ffprobe not found*, open **Settings** and set the paths, or install FFmpeg (e.g. via Windows Package Manager `winget`) and ensure it’s on `PATH`.

---

## Quick Start

1. Launch the app.
2. Pick a tab (e.g., **PDF → Merge**).
3. Click **Add…**, build a list, reorder if needed.
4. Set options (A4/margins, quality, etc.).
5. Choose **Save to** and hit **Start**.
6. Check **History** for results and logs.

---

## System Requirements

* **Windows 10/11 x64**
* No Python required for the installer build.
* For dev builds: **Python 3.13**, internet to install dependencies.

---

## External Tools

Some features call external binaries:

* **FFmpeg / FFprobe** — required for **Video** and **Audio** tabs.
  The app looks in `PATH`, common install locations, or bundled `vendor/ffmpeg/bin`, and also inside PyInstaller’s `_MEIPASS` when packaged.
* **Ghostscript** — optional; reserved for advanced PDF scenarios.

---

## Build From Source (dev)

### Environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel setuptools
pip install -r requirements.txt
```

Main libraries: **PyQt6, Pillow, PyMuPDF (fitz), pikepdf, python-pptx, mammoth, xhtml2pdf, reportlab, img2pdf, platformdirs**, etc.

> If `requirements.txt` was saved in UTF-16 by accident, re-save it as UTF-8 first.

### Build EXE with PyInstaller

```powershell
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "CompressorAndPDFMerger" ^
  --icon "src\compressor_and_pdf_merger\assets\media_tool_icon.ico" ^
  --paths "src" ^
  --add-data "src\compressor_and_pdf_merger\assets;compressor_and_pdf_merger\assets" ^
  --collect-all "fitz" --collect-all "PIL" --collect-all "pptx" --collect-all "mammoth" --collect-all "xhtml2pdf" --collect-all "reportlab" ^
  src\compressor_and_pdf_merger\main.py
```

**Result**: `dist/CompressorAndPDFMerger.exe`

Bundling FFmpeg (optional but robust):

```powershell
# Put binaries here:
# src\compressor_and_pdf_merger\vendor\ffmpeg\bin\ffmpeg.exe
# src\compressor_and_pdf_merger\vendor\ffmpeg\bin\ffprobe.exe

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "CompressorAndPDFMerger" ^
  --icon "src\compressor_and_pdf_merger\assets\media_tool_icon.ico" ^
  --paths "src" ^
  --add-data "src\compressor_and_pdf_merger\assets;compressor_and_pdf_merger\assets" ^
  --add-binary "src\compressor_and_pdf_merger\vendor\ffmpeg\bin\ffmpeg.exe;vendor/ffmpeg/bin" ^
  --add-binary "src\compressor_and_pdf_merger\vendor\ffmpeg\bin\ffprobe.exe;vendor/ffmpeg/bin" ^
  --collect-all "fitz" --collect-all "PIL" --collect-all "pptx" --collect-all "mammoth" --collect-all "xhtml2pdf" --collect-all "reportlab" ^
  src\compressor_and_pdf_merger\main.py
```

> Using a **src-layout**? The `--paths "src"` switch is important so imports like `compressor_and_pdf_merger.*` resolve.

### Windows Installer (Inno Setup)

* Script location: `installer\setup.iss` (or `setup_fixed.iss`).
* Features: choose **install folder**, optional **Desktop shortcut**, Start Menu shortcut, use app icon, supports **onefile**/**onedir** builds (toggle `#define OneFile`).

**Compile via IDE** or:

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

**IMPORTANT — AppId (GUID) escaping**

* Keep GUID **without braces** in `#define`:

  ```iss
  #define MyAppId "59C22CD6-E2C5-44E4-83C1-AD2B71B64023"
  ```
* In `[Setup]` produce literal braces with triple braces:

  ```iss
  AppId={{{#MyAppId}}}
  ```

  (Or hardcode as `AppId={{59C22CD6-E2C5-44E4-83C1-AD2B71B64023}}`.)
  This prevents Inno from treating `{…}` as a built-in constant.

Output will land in `installer\Output\…exe`.

---

## Where Data Is Stored

* **History (SQLite)**:
  Windows (typical):
  `%LOCALAPPDATA%\User\CompressorAndPDFMerger\history.sqlite3`
  (via `platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)` in `storage/db.py`)

* **Settings / window geometry**:
  Stored via **QSettings** under the app/vendor keys (registry or ini depending on platform).

---

## FAQ

**What CRF should I use?**
CRF is “constant quality”. Lower = better quality & bigger file. Try **23–24** for H.264, **25–28** for H.265. If still large, increase CRF.

**Do presets change quality?**
Indirectly. Slower preset yields **smaller size at the same CRF** (or same size at better quality), but takes longer to encode.

**H.264 vs H.265?**
H.265 is more efficient (smaller files) but slower and less universally supported. Choose **H.264** for maximum compatibility.

**PDF got larger after “compression”. Why?**
Vector-heavy PDFs can grow when rasterized. Enable **Never larger than source**. Increase compression (lower image quality) or avoid rasterizing certain pages (advanced controls planned).

**DOCX/XLSX/PPTX look “simplified” after merging to PDF.**
The basic converters (**mammoth/python-pptx/xhtml2pdf**) don’t replicate every Office feature. Install missing fonts in OS and simplify documents (rare effects, embedded objects) for better results.

**FFmpeg/ffprobe not found.**
Install FFmpeg and set paths in **Settings**, or bundle `ffmpeg.exe/ffprobe.exe` under `vendor/ffmpeg/bin` and include them via `--add-binary` in the build.

---

## Known Limitations

* Office → PDF conversion is “good enough” for typical docs but not a full MS Office renderer.
* Heavy vector PDFs may not shrink; use the guard or adjust options.
* Converting alpha images to JPEG will flatten transparency to white.
* Video/Audio tabs require FFmpeg/FFprobe.
* Large jobs take time; the UI provides progress/cancel.

---

## Roadmap

* OCR for PDFs (text recognition; default OCR language already planned in **Settings**).
* Finer PDF compression profiles (DPI/raster rules per page ranges).
* Batch recipes: extract audio, cut & join, etc.
* Global drag-and-drop for all tabs.
* Live preview for image/video settings.

---

## License

See [`LICENSE`](./LICENSE).

---

### Project Structure (short)

```
src/
  compressor_and_pdf_merger/
    main.py
    __init__.py
    core/
      detect.py               # find ffmpeg/ffprobe (PATH, winget, vendor, _MEIPASS)
    services/
      images.py               # image compress/resize/convert
      video.py                # video CRF/preset/codecs/FPS/scale/height
      audio.py                # codecs, LUFS normalization, filters
      pdf_merge.py            # merge, A4/margins
      pdf_compress.py         # raster + cleanup
      pdf_convert.py          # pdf→img/pptx/txt
      office_convert.py       # docx/xlsx/pptx → pdf (basic)
      pdf_utils.py            # helpers (which/run/tmp)
      safe_progress.py        # modal progress with cancel
      settings.py             # QSettings, defaults, tool paths
    storage/
      db.py                   # SQLite history (platformdirs)
    ui/
      main_window.py
      tab_*.py
      worker.py               # BatchWorker for background tasks
    assets/
      media_tool_icon.ico
```

---

### Rus
# Compressor & PDF Merger v1.0.0

Многофункциональный офлайн-инструмент на **PyQt6** для ежедневной работы с файлами:

* 📄 объединение **PDF / DOCX / XLSX / PPTX / изображений** в один PDF (с опцией приведения к **A4**);
* 🗜️ сжатие **PDF** (растрирование страниц, удаление метаданных);
* 🔁 конвертация **PDF → изображения (JPG/PNG)**, **PDF → PPTX (снимки слайдов)**, **PDF → TXT**;
* 🖼️ пакетное сжатие/изменение размера изображений и **конвертация форматов** (JPEG/PNG/WebP/TIFF);
* 🎬 сжатие видео (**H.264/H.265**, **CRF**, пресеты, ограничение FPS, изменение высоты, масштаб в %);
* 🎧 аудио-транскодирование (**Opus/AAC/MP3/FLAC**), нормализация **EBU R128 (LUFS)**, фильтры, обрезка тишины;
* 🕘 история действий с хранением в локальной базе **SQLite** и восстановлением настроек.

Работает локально, не отправляет файлы в сеть.

---

## Оглавление

* [Возможности по вкладкам](#возможности-по-вкладкам)

  * [PDF → Объединение](#pdf--объединение)
  * [PDF → Сжатие](#pdf--сжатие)
  * [PDF → Конвертация](#pdf--конвертация)
  * [Изображения](#изображения)
  * [Видео](#видео)
  * [Аудио](#аудио)
  * [История](#история)
  * [Настройки](#настройки)
* [Установка для пользователя](#установка-для-пользователя)
* [Быстрый старт](#быстрый-старт)
* [Системные требования](#системные-требования)
* [Внешние инструменты](#внешние-инструменты)
* [Сборка из исходников (dev)](#сборка-из-исходников-dev)

  * [Сборка EXE (PyInstaller)](#сборка-exe-pyinstaller)
  * [Инсталлятор (Inno Setup)](#инсталлятор-inno-setup)
* [Где хранится история и настройки](#где-хранится-история-и-настройки)
* [FAQ](#faq)
* [Ограничения и известные нюансы](#ограничения-и-известные-нюансы)
* [Дорожная карта](#дорожная-карта)
* [Лицензия](#лицензия)

---

## Возможности по вкладкам

Код вкладок находится в `src/compressor_and_pdf_merger/ui/*.py`, бизнес-логика — в `src/compressor_and_pdf_merger/services/*.py`.

### PDF → Объединение

Файл: `ui/tab_pdf_merge.py`, логика: `services/pdf_merge.py`, `services/office_convert.py`, `services/pdf_utils.py`

* **Вход**:

  * PDF;
  * офисные документы (**DOC/DOCX, XLS/XLSX, PPT/PPTX**) — конвертируются во внутренний PDF-поток `docx_to_pdf_basic/xlsx_to_pdf_basic/pptx_to_pdf_basic`;
  * изображения (**JPG, PNG, WEBP, TIFF, BMP**) — добавляются как страницы (учитывается EXIF-поворот).
* **Порядок** можно менять (drag-and-drop в списке).
* **Вывод**: единый PDF.
* **Опции вывода**:

  * «**Привести к A4**» — все страницы приводятся к A4 с белыми полями (задаётся отступ в мм).
* **Когда использовать**: собрать скан и фото-страницы, лекции/слайды и офисные файлы в один аккуратный PDF.

> ⚠️ Конвертация офисных форматов реализована без MS Office: DOCX через **mammoth → HTML → xhtml2pdf** (с подстановкой шрифта), XLSX — через отрисовку таблиц, PPTX — рендер элементов слайдов (**python-pptx**). Очень сложные макеты, нестандартные шрифты и спец-объекты могут упрощаться.

---

### PDF → Сжатие

Файл: `ui/tab_pdf_compress.py`, логика: `services/pdf_compress.py`

* **Как работает**: страницы при необходимости **растрируются** (через **PyMuPDF/fitz**) и сохраняются обратно с контролируемым качеством изображений (Pillow).
* **Опции**:

  * «**Ч/б (grayscale)**» — переводит изображения в оттенки серого;
  * «**Удалить метаданные/вложения**» — зачистка `docinfo/metadata/Names` (**pikepdf**);
  * «**Не больше исходного**» — если результат получился крупнее — сохраняется исходник (защита от «антисжатия»).
* **Когда использовать**: сделать PDF заметно легче для отправки, печати, архива.

---

### PDF → Конвертация

Файл: `ui/tab_pdf_convert.py`, логика: `services/pdf_convert.py`

* **Режимы**:

  * **PDF → Изображения** (**JPG/PNG**), постранично, с выбором DPI;
  * **PDF → PPTX (снимки)** — создаётся презентация, где каждый слайд — изображение страницы;
  * **PDF → TXT** — извлечение текста (через **PyMuPDF**).
* **Диапазон страниц**: строка вида `1,3-5,10-` (пробелы допустимы).
  Примеры:

  * `5` — только 5-я страница;
  * `2-4` — 2,3,4;
  * `-3` — с 1 по 3;
  * `10-` — с 10 до конца.

---

### Изображения

Файл: `ui/tab_image.py`, логика: `services/images.py`

* **Сжатие**: ползунок **%**. Для JPEG это маппится в `quality` (диапазон ограничен безопасными значениями), PNG — сжатие/квантование, WebP — `quality`.
* **Изменение размера**: по проценту либо по запрошенному параметру (длинная сторона/ширина/высота — см. диалоги вкладки).
* **Конвертация форматов**: **JPEG, PNG, WebP, TIFF** (кнопка «Формат…»), опционально с применением сжатия.
* **EXIF/метаданные**: опция **удаления** (геометки, дата, камера и т.д.).
* **Анимация/прозрачность**: для JPEG прозрачность «сплющивается» на белый фон; PNG/WebP сохраняют альфу.
* **Пакетный режим**: целые папки и списки файлов.

---

### Видео

Файл: `ui/tab_video.py`, логика: `services/video.py`

* **Кодеки**: **H.264** (`libx264`) и **H.265/HEVC** (`libx265`).
* **CRF** (качество): ниже — лучше качество/больше размер; типичный диапазон **18–28**.
* **Preset**: от `ultrafast` до `veryslow` (чем медленнее — тем выше эффективность/меньше размер).
* **Доп. параметры**:

  * **FPS**: ограничить выходные кадры/с (например, 24/30) — снижает вес;
  * **Высота в «p»**: резко задать целевую высоту **(например, 720p)** — пропорции сохраняются;
  * **Масштаб в %**: 25–100% от исходника (удобно для быстрой деградации размера);
  * **Аудио**: кодек **AAC** с битрейтом (по умолчанию 128k);
  * **Стрип метаданных**, **faststart** (перемотка онлайн) — включено в команде.
* **Гарантии размера**: в `compress_video_crf` предусмотрена защита `ensure_not_larger/min_shrink_ratio` — если файл внезапно вышел больше исходника, берётся исходный.
* **Имена файлов**: в суффиксе отражаются параметры: `crf<preset>_<codec>`, `_720p` или `_75pct`, `_fps24` и т.п.

---

### Аудио

Файл: `ui/tab_audio.py`, логика: `services/audio.py`

* **Кодеки**: **Opus**, **AAC**, **MP3**, **FLAC**.
* **Режимы**:

  * **CBR** (битрейт фиксированный);
  * Для MP3: **VBR** с качеством;
* **Параметры**:

  * **Битрейт** (для CBR), **качество (VBR)**;
  * **Частота дискретизации** (например, 44.1/48 кГц);
  * **Каналы**: Авто / Моно / Стерео;
* **Нормализация**: **EBU R128 (LUFS)** — приведёт громкость к целевому уровню (например, −16 LUFS).
* **Фильтры**: **High-pass**, **Low-pass** (срез НЧ/ВЧ), **обрезка тишины**.
* **Защита «не больше исходного»** — при необходимости.

---

### История

Файл: `ui/tab_history.py`, хранилище: `storage/db.py`

* Запоминает до 500 последних операций: вкладка, действие, путь исходника/результата, метка времени.
* Кнопка **Очистить историю**.
* База хранится в локальном профиле пользователя (см. раздел «Где хранится…»).

---

### Настройки

Файл: `ui/tab_settings.py`, логика: `services/settings.py`

* **Папки по умолчанию**: для изображений, PDF-операций, видео/аудио.
* **Пути к инструментам**: `ffmpeg`, `ffprobe`, (опционально) Ghostscript.
* **Язык OCR по умолчанию** (на будущее).
* **Геометрия окна** — состояние окна запоминается (QSettings).

---

## Установка для пользователя

1. Скачайте инсталлятор **Compressor & PDF Merger\_Setup\_…exe** (из раздела Releases).
2. Запустите и выберите **папку установки**.
3. По желанию поставьте галочку **«Создать ярлык на рабочем столе»**.
4. После установки можно сразу запустить приложение.

> Если при сжатии видео/аудио появится сообщение «не найден ffmpeg/ffprobe», зайдите во вкладку **Настройки** и укажите пути к EXE, либо установите FFmpeg через **winget**:
> `winget install -e --id Gyan.FFmpeg` (пример одного из поставщиков; подойдёт и любой другой официальный пакет FFmpeg).

---

## Быстрый старт

1. Откройте приложение.
2. Выберите нужную вкладку (например, **PDF → Объединение**).
3. Кнопкой **Добавить…** наберите файлы в список, упорядочьте их.
4. Задайте опции (A4/поля, качество и т.п.).
5. Укажите **путь сохранения** и нажмите **Старт**.
6. Результат и лог добавятся в **Историю**.

---

## Системные требования

* **Windows 10/11 x64**
* **Python не требуется**, если вы ставите готовый инсталлятор.
* Для сборки из исходников: **Python 3.13**, Visual C++ Build Tools (обычно не нужны для указанных библиотек), доступ в интернет для установки зависимостей.

---

## Внешние инструменты

Некоторые операции вызывают **внешние утилиты**:

* **FFmpeg / FFprobe** — видео и аудио (обязательны для этих функций).
  Поиск: в `PATH`, в стандартных каталогах `winget`, либо внутри папки сборки (см. `core/detect.py`).
* **Ghostscript** — не обязателен; может использоваться для расширенных PDF-сценариев в будущих версиях (путь можно указать в «Настройках»).

---

## Сборка из исходников (dev)

### Подготовка

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel setuptools

# Если requirements.txt сохранён в UTF-16, откройте/пересохраните в UTF-8.
pip install -r requirements.txt
```

> Основные зависимости: **PyQt6, Pillow, PyMuPDF (fitz), pikepdf, python-pptx, mammoth, xhtml2pdf, reportlab, img2pdf, platformdirs** и др.

### Сборка EXE (PyInstaller)

```
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "CompressorAndPDFMerger" ^
  --icon "src\compressor_and_pdf_merger\assets\media_tool_icon.ico" ^
  --paths "src" ^
  --add-data "src\compressor_and_pdf_merger\assets;compressor_and_pdf_merger\assets" ^
  --collect-all "fitz" --collect-all "PIL" --collect-all "pptx" --collect-all "mammoth" --collect-all "xhtml2pdf" --collect-all "reportlab" ^
  src\compressor_and_pdf_merger\main.py
```

Результат: `dist/CompressorAndPDFMerger.exe`.

> Если используете встроенный FFmpeg — добавьте `--add-binary` для `ffmpeg.exe/ffprobe.exe` и закладывайте их в `src\compressor_and_pdf_merger\vendor\ffmpeg\bin\`.

### Инсталлятор (Inno Setup)

1. Установите **Inno Setup 6**.
2. Используйте скрипт `installer\setup.iss` (или исправленный `setup_fixed.iss`), где:

   * включён выбор пути установки;
   * есть задача «**Создать ярлык на рабочем столе**»;
   * подключена иконка;
   * поддержаны сборки **onefile**/**onedir** (переключается директивой `#define OneFile`).
3. Скомпилировать:

   ```
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
   ```
4. Готовый установщик окажется в `installer\Output\...exe`.

---

## Где хранится история и настройки

* **История** — SQLite база:

  * Windows: обычно `%LOCALAPPDATA%\User\CompressorAndPDFMerger\history.sqlite3`
    (см. `storage/db.py`, используется `platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)`).
* **Настройки/геометрия окна** — через **QSettings**:

  * ключи в ветке приложения `User / CompressorAndPDFMerger` (реестровый или ini-бэкенд в зависимости от платформы).

---

## FAQ

**Зачем CRF, и какое значение выбрать?**
CRF — «постоянное качество». Ниже — лучше качество/больше размер. Для H.264 начинайте с **23–24**, для H.265 — **25–28**. Если слишком крупно — повышайте CRF (качество ниже).

**Preset влияет на качество?**
Косвенно: более медленный пресет даёт **меньший размер при том же CRF** (или то же качество при меньшем битрейте), но кодируется дольше.

**Что лучше: H.264 или H.265?**
H.265 эффективнее (меньше размер при том же качестве), но кодируется медленнее и старые устройства его хуже поддерживают. Для максимально совместимого результата используйте **H.264**.

**PDF стал больше после «сжатия». Почему?**
Бывает на «чистых» векторных PDF. Включите опцию **«Не больше исходного»** — она защитит от роста. Попробуйте увеличить степень сжатия (ниже качество изображений) или отключить растрирование для особо сложных страниц (в будущих версиях появится тонкая настройка).

**Док/таблица/слайд некрасиво сконвертировались в PDF.**
Механизмы `mammoth/xhtml2pdf/python-pptx` не покрывают все возможности MS Office. Установите нужные шрифты в ОС и упростите документ (сложные и редкие элементы, встроенные объекты, smart-art, эффекты) — результат улучшится.

**Не найден FFmpeg/FFprobe.**
Поставьте FFmpeg и укажите путь в «Настройках» **или** добавьте бинарники в `vendor/ffmpeg/bin` и соберите EXE с включением этих файлов (`--add-binary`).

---

## Ограничения и известные нюансы

* Сложные **DOCX/XLSX/PPTX** конвертируются в «базовом» виде (без полной поддержки всех эффектов/объектов).
* **PDF с большим количеством векторов** может после растрирования получиться больше; в таких случаях поможет отключение части опций или использование «Не больше исходного».
* **WebP/PNG** с альфой при конвертации в JPEG теряет прозрачность (фон — белый).
* Некоторым функциям нужны внешние утилиты (**FFmpeg/FFprobe**).
* Некоторые большие операции занимают время; в интерфейсе есть прогресс и отмена.

---

## Дорожная карта

* OCR для PDF (распознавание текста; настройка языка уже предусмотрена в `Settings`).
* Более тонкие пресеты PDF-сжатия (управление DPI/растрированием по диапазонам).
* Пакетные сценарии: «вытащить аудио», «вырезать фрагмент», «склеить видео».
* Поддержка drag-and-drop в основное окно для всех вкладок.
* Предпросмотр настроек для изображений/видео.

---

## Лицензия

См. файл `LICENSE`.

---

### Структура проекта (кратко)

```
src/
  compressor_and_pdf_merger/
    main.py                  # вход GUI
    __init__.py
    core/detect.py           # поиск ffmpeg/ffprobe (PATH, winget, vendor, _MEIPASS)
    services/                # бизнес-логика
      images.py              # сжатие/resize/конвертация
      video.py               # сжатие видео (CRF, preset, кодеки, FPS, scale/p-height)
      audio.py               # кодеки, нормализация, фильтры
      pdf_merge.py           # объединение, A4/поля
      pdf_compress.py        # сжатие PDF (растрирование, зачистка)
      pdf_convert.py         # pdf→img/pptx/txt, диапазоны страниц
      office_convert.py      # docx/xlsx/pptx → pdf (basic)
      pdf_utils.py           # which/run/tmp helpers
      safe_progress.py       # модальный прогресс с отменой
      settings.py            # QSettings, пути по умолчанию, инструменты
    storage/
      db.py                  # SQLite-история (platformdirs)
    ui/
      main_window.py         # вкладки, восстановление геометрии
      tab_*.py               # реализации вкладок
      worker.py              # BatchWorker для фоновых задач
    assets/
      media_tool_icon.ico    # иконка приложения
```

---

