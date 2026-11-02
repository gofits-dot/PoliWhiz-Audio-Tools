\# PoliWhiz Audio Tools



A collection of free audio tools for language learners.



\## Current tool: Audio Splitter



\- Supports MP3, WAV and M4A.

\- Splits audio into 2–10 equal parts.

\- Allows downloading each resulting part.

\- Uses FFmpeg for audio processing.



\## Project structure



\- `web/` — frontend interface.

\- `backend/` — Python Flask backend.



\## Requirements



\- Python 3

\- FFmpeg and FFprobe



\## Local development



Install dependencies:



&#x20;   pip install -r backend/requirements.txt



Start the backend:



&#x20;   python backend/app.py



In a second PowerShell window, start the frontend:



&#x20;   python -m http.server 8000 --directory web



Open http://127.0.0.1:8000 in your browser.



\## Project status



Early development. The audio splitter has been tested locally.

