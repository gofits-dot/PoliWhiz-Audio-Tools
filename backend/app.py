
import os
import subprocess
import uuid
import json
import urllib.request
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://127.0.0.1:8080",
            "https://poliwhiz.com",
            "https://www.poliwhiz.com"
        ]
    }
})

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a"}
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB

app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

ADMIN_CHAT_ID = 1710023187

APK_URL = (
    "https://drive.google.com/file/d/"
    "1SHi6ckfkMSlqD0IUqY_T4i71BAqyiXZm/view?usp=drivesdk"
)


def send_telegram_notification():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        app.logger.error("TELEGRAM_BOT_TOKEN is not configured")
        return

    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": (
            "📥 Нажатие ссылки PoliWhiz Trial!\n\n"
            "Пользователь перешёл к скачиванию APK.\n"
            "Время события: "
            + datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        ),
    }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))

        if not result.get("ok"):
            raise RuntimeError("Telegram API rejected the notification")

        app.logger.info("Download click notification sent to administrator")

    except Exception:
        app.logger.exception("Failed to send Telegram notification")


def send_email_notification():
    api_key = os.environ.get("RESEND_API_KEY")

    if not api_key:
        app.logger.warning("RESEND_API_KEY is not configured")
        return

    payload = {
        "from": "PoliWhiz <onboarding@resend.dev>",
        "to": ["gofits@gmail.com"],
        "subject": "PoliWhiz Trial — переход к скачиванию",
        "text": (
            "Кто-то перешёл по ссылке для скачивания PoliWhiz Trial.\n"
            "Время события: "
            + datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        ),
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()

        app.logger.info("Download email notification sent successfully")

    except Exception:
        app.logger.exception("Failed to send download email notification")


def get_duration(file_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )

    duration = float(result.stdout.strip())

    if duration <= 0:
        raise ValueError("Audio duration is invalid")

    return duration


@app.route("/")
def home():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "home.html")


@app.route("/ru")
def home_ru():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "home_ru.html")


@app.route("/how_it_works_en.html")
def guide_en():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "how_it_works_en.html")


@app.route("/how_it_works_ru.html")
def guide_ru():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "how_it_works_ru.html")


@app.route("/images/<path:filename>")
def guide_images(filename):
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir / "images", filename)


@app.route("/splitter")
def splitter():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "index.html")


@app.route("/studio")
def studio():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "studio.html")


@app.route("/studio/ru")
def studio_ru():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "studio_ru.html")


@app.route("/studio/splitter")
def studio_splitter():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "studio_splitter.html")


@app.route("/studio/ru/splitter")
def studio_splitter_ru():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "studio_splitter_ru.html")


@app.route("/sitemap.xml")
def sitemap():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "sitemap.xml", mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(web_dir, "robots.txt", mimetype="text/plain")


@app.route("/yandex_0210c72dfc5030ec.html")
def yandex_verification():
    web_dir = Path(__file__).resolve().parent.parent / "web"
    return send_from_directory(
        web_dir,
        "yandex_0210c72dfc5030ec.html",
        mimetype="text/html"
    )


@app.route("/get-apk")
def get_apk():
    app.logger.info("APK link clicked")

    send_telegram_notification()
    send_email_notification()

    return redirect(APK_URL, code=302)


@app.route("/api/split", methods=["POST"])
def split_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio = request.files["audio"]

    if not audio.filename:
        return jsonify({"error": "No file selected"}), 400

    original_name = secure_filename(audio.filename)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Supported formats: MP3, WAV, M4A"}), 400

    try:
        parts_count = int(request.form.get("parts", "2"))
    except ValueError:
        return jsonify({"error": "Parts must be a number"}), 400

    if not 2 <= parts_count <= 10:
        return jsonify({"error": "Choose between 2 and 10 parts"}), 400

    operation_id = uuid.uuid4().hex
    operation_upload_dir = UPLOAD_DIR / operation_id
    operation_output_dir = OUTPUT_DIR / operation_id

    operation_upload_dir.mkdir(parents=True, exist_ok=True)
    operation_output_dir.mkdir(parents=True, exist_ok=True)

    input_path = operation_upload_dir / f"source{extension}"

    try:
        audio.save(input_path)

        duration = get_duration(input_path)
        segment_duration = duration / parts_count

        output_extension = extension

        for index in range(parts_count):
            start_time = index * segment_duration
            output_path = operation_output_dir / (
                f"part_{index + 1}{output_extension}"
            )

            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-i", str(input_path),
                "-ss", str(start_time),
                "-t", str(segment_duration),
                "-vn",
            ]

            if extension == ".mp3":
                command += ["-c:a", "libmp3lame", "-q:a", "2"]
            elif extension == ".wav":
                command += ["-c:a", "pcm_s16le"]
            else:
                command += ["-c:a", "aac", "-b:a", "192k"]

            command.append(str(output_path))

            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=600,
            )

        parts = [
            {
                "name": f"part_{index + 1}{output_extension}",
                "download_url": f"/api/download/{operation_id}/part_{index + 1}{output_extension}",
            }
            for index in range(parts_count)
        ]

        return jsonify({
            "operation_id": operation_id,
            "original_duration": duration,
            "parts_count": parts_count,
            "parts": parts,
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Audio processing timed out"}), 504

    except (subprocess.CalledProcessError, ValueError) as error:
        app.logger.warning("Audio processing failed: %s", error)
        return jsonify({"error": "Could not process this audio file"}), 400

    finally:
        if input_path.exists():
            input_path.unlink()

        try:
            operation_upload_dir.rmdir()
        except OSError:
            pass


@app.route("/api/download/<operation_id>/<filename>")
def download_part(operation_id, filename):
    if not operation_id.isalnum():
        return jsonify({"error": "Invalid operation ID"}), 400

    if filename not in {
        f"part_{index}{extension}"
        for index in range(1, 11)
        for extension in ALLOWED_EXTENSIONS
    }:
        return jsonify({"error": "Invalid filename"}), 400

    directory = OUTPUT_DIR / operation_id

    if not (directory / filename).is_file():
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(directory, filename, as_attachment=True)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "File is too large. Maximum size is 200 MB."}), 413


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )
