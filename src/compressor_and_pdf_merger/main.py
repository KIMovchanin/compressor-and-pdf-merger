from compressor_and_pdf_merger.core.detect import find_ffmpeg
import subprocess, sys

ff = find_ffmpeg()
if not ff:
    print("FFmpeg не найден. Установите FFmpeg или добавьте его в PATH.")
    sys.exit(1)

subprocess.run([ff, "-version"])
