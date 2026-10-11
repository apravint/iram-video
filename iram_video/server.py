import os
import sys
import json
import mimetypes
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

RESOURCES_DIR = Path("/home/apravint/resources")
OUTPUTS_DIR = Path("/home/apravint")

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IRAM Video Studio — Autonomous AI Cinema & Animation Engine</title>
  <style>
    :root {
      --bg: #07090e;
      --card: #0e121a;
      --border: #1e2638;
      --accent: #00e5ff;
      --accent-glow: rgba(0, 229, 255, 0.25);
      --purple: #a855f7;
      --gold: #ffb703;
      --text: #f0f4f8;
      --muted: #8292a8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "JetBrains Mono", sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; }
    header { background: rgba(14, 18, 26, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); padding: 18px 36px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; }
    .brand { display: flex; align-items: center; gap: 14px; font-weight: 700; font-size: 20px; letter-spacing: -0.5px; }
    .badge { font-size: 11px; padding: 3px 8px; border-radius: 6px; background: rgba(0, 229, 255, 0.12); color: var(--accent); border: 1px solid rgba(0, 229, 255, 0.3); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    main { max-width: 1300px; margin: 0 auto; padding: 36px 24px; width: 100%; display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 32px; }
    @media (max-width: 980px) { main { grid-template-columns: 1fr; } }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 26px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); }
    h2 { font-size: 18px; font-weight: 600; margin-bottom: 18px; color: #fff; display: flex; align-items: center; gap: 10px; }
    .form-group { margin-bottom: 20px; }
    label { display: block; font-size: 13px; font-weight: 500; color: var(--muted); margin-bottom: 8px; }
    textarea, select, input { width: 100%; background: #07090e; border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; color: var(--text); font-size: 14px; transition: border 0.2s; outline: none; }
    textarea:focus, select:focus, input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
    textarea { resize: vertical; min-height: 105px; line-height: 1.5; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .chip { font-size: 12px; padding: 6px 12px; border-radius: 20px; background: #131924; border: 1px solid var(--border); color: #cbd5e1; cursor: pointer; transition: all 0.2s; }
    .chip:hover { border-color: var(--accent); color: var(--accent); background: rgba(0, 229, 255, 0.08); }
    .radio-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .radio-card { border: 1px solid var(--border); border-radius: 8px; padding: 12px; background: #090c13; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: all 0.2s; }
    .radio-card input { width: auto; accent-color: var(--accent); }
    .radio-card.active { border-color: var(--accent); background: rgba(0, 229, 255, 0.06); }
    .btn-generate { width: 100%; padding: 15px; border-radius: 8px; background: linear-gradient(135deg, #00e5ff 0%, #0088ff 100%); color: #000; font-weight: 700; font-size: 15px; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; box-shadow: 0 4px 18px rgba(0, 229, 255, 0.35); transition: opacity 0.2s; }
    .btn-generate:hover { opacity: 0.92; }
    .btn-generate:disabled { opacity: 0.4; cursor: not-allowed; }
    .video-preview-wrapper { width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; position: relative; }
    .video-preview-wrapper.shorts-mode { aspect-ratio: 9/16; max-height: 540px; margin: 0 auto; }
    video { width: 100%; height: 100%; object-fit: contain; }
    .status-box { margin-top: 18px; padding: 14px; border-radius: 8px; background: #090c13; border: 1px solid var(--border); font-size: 13px; font-family: monospace; color: var(--accent); min-height: 48px; display: flex; align-items: center; gap: 10px; }
    .spinner { border: 2px solid rgba(0, 229, 255, 0.2); border-top-color: var(--accent); border-radius: 50%; width: 16px; height: 16px; animation: spin 0.8s linear infinite; display: none; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🎬 IRAM Video Studio</span>
      <span class="badge">Cinema 24 FPS • Multi-Character • Foley SFX</span>
    </div>
    <div style="font-size: 13px; color: var(--muted);">IRAM OS v26.04 Local Hub</div>
  </header>

  <main>
    <div class="card">
      <h2>⚙️ Director & Production Console</h2>
      
      <div class="form-group">
        <label>Import from Structured JSON Blueprint:</label>
        <select id="jsonSelect">
          <option value="">-- Direct Text Prompt Only --</option>
        </select>
      </div>

      <div class="form-group">
        <label>Prompt / Screenplay Premise (English or தமிழ்):</label>
        <textarea id="promptInput" placeholder="Describe the scene, movie premise, or technical deep-dive...">The Quantum Anomaly: Sentient core awakening in orbital deep space</textarea>
        <div class="chips">
          <span class="chip" onclick="addChip('cyberpunk neon city, rain reflections')">🌃 Cyberpunk City</span>
          <span class="chip" onclick="addChip('orbital deep space, quantum core')">🌌 Deep Space</span>
          <span class="chip" onclick="addChip('24 FPS Hollywood scope, Hans Zimmer BRAAMs')">🎺 Hans Zimmer Score</span>
          <span class="chip" onclick="addChip('Rust vs Go concurrency race')">🦀 Mascot Duel</span>
        </div>
      </div>

      <div class="form-group">
        <label>Production Format:</label>
        <div class="radio-grid">
          <label class="radio-card active"><input type="radio" name="mode" value="real" checked> 🎥 Real YouTube Video (B-Roll, No Subtitles)</label>
          <label class="radio-card"><input type="radio" name="mode" value="film"> 🎭 Animated Feature Film</label>
          <label class="radio-card"><input type="radio" name="mode" value="cinema"> 🎬 Cinema Blockbuster Trailer</label>
          <label class="radio-card"><input type="radio" name="mode" value="shorts"> 📱 YouTube Shorts (9:16)</label>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;" class="form-group">
        <div>
          <label>Animated Mascot Cast:</label>
          <select id="charSelect">
            <option value="auto">Auto Selection</option>
            <option value="robot">Unit-7 (Sentient Robot)</option>
            <option value="presenter">Nova (Lead Architect)</option>
            <option value="ferris">Ferris (Rust Crab)</option>
            <option value="gopher">Gopher (Go Mascot)</option>
          </select>
        </div>
        <div>
          <label>Broadcast Language:</label>
          <select id="langSelect">
            <option value="en">English (Hollywood Dialogue)</option>
            <option value="ta">தமிழ் (Tamil Cinema)</option>
          </select>
        </div>
      </div>

      <button id="btnGen" class="btn-generate" onclick="startGeneration()">
        <span>🚀 Direct & Render Master Film</span>
      </button>

      <div class="status-box">
        <div class="spinner" id="spinner"></div>
        <span id="statusText">Ready to direct. Select options and click Render.</span>
      </div>
    </div>

    <div class="card">
      <h2>📽️ Master Broadcast Monitor</h2>
      <div class="video-preview-wrapper" id="previewWrap">
        <video id="videoPlayer" controls playsinline></video>
      </div>
      <div style="margin-top: 18px; display: flex; justify-content: space-between; align-items: center;">
        <span id="videoMeta" style="font-size: 13px; color: var(--muted);">No video loaded</span>
        <a id="downloadBtn" href="#" download style="font-size: 13px; color: var(--accent); text-decoration: none; display: none;">⬇️ Download Master MP4</a>
      </div>
    </div>
  </main>

  <script>
    async function loadResources() {
      try {
        const res = await fetch('/api/resources');
        const files = await res.json();
        const sel = document.getElementById('jsonSelect');
        files.forEach(f => {
          const opt = document.createElement('option');
          opt.value = f.path;
          opt.textContent = f.name + ' (' + f.title + ')';
          sel.appendChild(opt);
        });
      } catch (e) {
        console.error("Failed to load resources", e);
      }
    }
    loadResources();

    document.querySelectorAll('.radio-card').forEach(rc => {
      rc.addEventListener('click', () => {
        document.querySelectorAll('.radio-card').forEach(c => c.classList.remove('active'));
        rc.classList.add('active');
        rc.querySelector('input').checked = true;
        const mode = rc.querySelector('input').value;
        const wrap = document.getElementById('previewWrap');
        if (mode === 'shorts') {
          wrap.classList.add('shorts-mode');
        } else {
          wrap.classList.remove('shorts-mode');
        }
      });
    });

    function addChip(text) {
      const el = document.getElementById('promptInput');
      el.value = el.value.trim() ? el.value.trim() + ', ' + text : text;
    }

    async function startGeneration() {
      const btn = document.getElementById('btnGen');
      const spinner = document.getElementById('spinner');
      const statusText = document.getElementById('statusText');
      const prompt = document.getElementById('promptInput').value;
      const jsonDoc = document.getElementById('jsonSelect').value;
      const mode = document.querySelector('input[name="mode"]:checked').value;
      const character = document.getElementById('charSelect').value;
      const language = document.getElementById('langSelect').value;

      btn.disabled = true;
      spinner.style.display = 'block';
      statusText.textContent = "Writing screenplay & generating cinematic assets...";

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, jsonDoc, mode, character, language })
        });
        const data = await res.json();
        if (data.status === 'success') {
          statusText.textContent = "✓ Master Render Complete: " + data.filename;
          const vp = document.getElementById('videoPlayer');
          vp.src = '/video/' + encodeURIComponent(data.filename);
          vp.play();
          document.getElementById('videoMeta').textContent = data.filename + ' (' + data.duration + ')';
          const dl = document.getElementById('downloadBtn');
          dl.href = '/video/' + encodeURIComponent(data.filename);
          dl.style.display = 'inline';
        } else {
          statusText.textContent = "❌ Generation failed: " + (data.error || "Unknown error");
        }
      } catch (err) {
        statusText.textContent = "❌ Network error: " + err.message;
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    }
  </script>
</body>
</html>
"""

class VideoStudioHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
            return

        if path == "/api/resources":
            items = []
            if RESOURCES_DIR.exists():
                for f in sorted(RESOURCES_DIR.glob("*.json")):
                    try:
                        with open(f, "r") as jf:
                            data = json.load(jf)
                            title = data.get("title", f.name)
                    except Exception:
                        title = f.name
                    items.append({"name": f.name, "path": str(f.resolve()), "title": title})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(items).encode("utf-8"))
            return

        if path.startswith("/video/"):
            filename = path.replace("/video/", "")
            target_file = OUTPUTS_DIR / filename
            if not target_file.exists():
                # Check in current working dir
                target_file = Path.cwd() / filename

            if target_file.exists() and target_file.is_file():
                file_size = target_file.stat().st_size
                range_header = self.headers.get("Range")
                if range_header:
                    # Basic range request handling for video streaming
                    bytes_range = range_header.replace("bytes=", "").split("-")
                    start = int(bytes_range[0])
                    end = int(bytes_range[1]) if bytes_range[1] else file_size - 1
                    length = end - start + 1
                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    with open(target_file, "rb") as vf:
                        vf.seek(start)
                        self.wfile.write(vf.read(length))
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    with open(target_file, "rb") as vf:
                        self.wfile.write(vf.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            payload = json.loads(body.decode("utf-8"))

            prompt = payload.get("prompt", "AI Future")
            json_doc = payload.get("jsonDoc")
            mode = payload.get("mode", "film")
            char = payload.get("character", "auto")
            lang = payload.get("language", "en")

            # Build command line
            cmd = [sys.executable, "-m", "iram_video.cli"]
            if json_doc and Path(json_doc).exists():
                cmd.extend(["--from-json", str(json_doc)])
            else:
                cmd.append(prompt)

            if mode == "real":
                cmd.append("--real")
            elif mode == "film":
                cmd.append("--film")
            elif mode == "cinema":
                cmd.append("--cinema")
            elif mode == "shorts":
                cmd.append("--shorts")

            if char and char != "auto":
                cmd.extend(["--character", char])
            if lang:
                cmd.extend(["--lang", lang])

            # Output filename
            import re
            slug = re.sub(r"[^\w\s-]", "", prompt, flags=re.UNICODE).strip().lower()
            slug = re.sub(r"[-\s]+", "_", slug)[:35] or "web_render"
            out_name = f"{slug}_{mode}.mp4"
            out_file = OUTPUTS_DIR / out_name
            cmd.extend(["-o", str(out_file)])

            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "filename": out_name,
                    "duration": "Broadcast Ready"
                }).encode("utf-8"))
            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "error": e.stderr or str(e)
                }).encode("utf-8"))
            return

def start_server(port: int = 7860):
    server = HTTPServer(("0.0.0.0", port), VideoStudioHandler)
    print(f"\n🌐 [IRAM Video Studio] Running at http://localhost:{port}")
    print(f"🎬 Ready for browser-based video directing, mascot selection, and live playback.\n")
    server.serve_forever()
