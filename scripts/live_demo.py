"""
Mizpah ML - Live Webcam Demo
=============================
Opens a browser-based webcam interface that captures your face
and scans it against the Supabase database via the Render API in real-time.

Usage:
  python scripts/live_demo.py

Then open http://localhost:9000 in your browser.
"""
import http.server
import json
import threading
import webbrowser
import urllib.request
import urllib.error
import socket
import os

PORT = 9000
API_URL = os.environ.get("MIZPAH_API_URL", "https://mizpah-ml.onrender.com")

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mizpah ML - Live Face Scanner</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', sans-serif;
    background: #0a0a0f;
    color: #e0e0e0;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Animated background */
  body::before {
    content: '';
    position: fixed;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(ellipse at 20% 50%, rgba(72, 50, 180, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(0, 200, 150, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 80%, rgba(200, 50, 100, 0.06) 0%, transparent 50%);
    animation: drift 20s ease-in-out infinite alternate;
    z-index: -1;
  }
  @keyframes drift {
    0% { transform: translate(0, 0) rotate(0deg); }
    100% { transform: translate(-30px, -20px) rotate(2deg); }
  }

  .container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 30px 20px;
  }

  /* Header */
  .header {
    text-align: center;
    margin-bottom: 30px;
  }
  .header h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7c5cfc, #00c896);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
  }
  .header p {
    color: #888;
    font-size: 0.9rem;
  }
  .api-badge {
    display: inline-block;
    margin-top: 8px;
    padding: 4px 12px;
    background: rgba(124, 92, 252, 0.15);
    border: 1px solid rgba(124, 92, 252, 0.3);
    border-radius: 20px;
    font-size: 0.75rem;
    color: #a78bfa;
    font-family: monospace;
  }

  /* Main grid */
  .main-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: start;
  }
  @media (max-width: 768px) {
    .main-grid { grid-template-columns: 1fr; }
  }

  /* Card style */
  .card {
    background: rgba(20, 20, 30, 0.8);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(20px);
  }
  .card-title {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #666;
    margin-bottom: 16px;
    font-weight: 600;
  }

  /* Video */
  .video-wrapper {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    background: #111;
    aspect-ratio: 4/3;
  }
  #webcam {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transform: scaleX(-1);
  }
  .video-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
  }
  .scan-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00c896, transparent);
    opacity: 0;
    transition: opacity 0.3s;
  }
  .scanning .scan-line {
    opacity: 1;
    animation: scanMove 1.5s ease-in-out infinite;
  }
  @keyframes scanMove {
    0% { top: 0; }
    50% { top: 100%; }
    100% { top: 0; }
  }
  .corner {
    position: absolute;
    width: 24px; height: 24px;
    border-color: #7c5cfc;
    border-style: solid;
    border-width: 0;
    transition: border-color 0.3s;
  }
  .corner.tl { top: 12px; left: 12px; border-top-width: 3px; border-left-width: 3px; border-radius: 4px 0 0 0; }
  .corner.tr { top: 12px; right: 12px; border-top-width: 3px; border-right-width: 3px; border-radius: 0 4px 0 0; }
  .corner.bl { bottom: 12px; left: 12px; border-bottom-width: 3px; border-left-width: 3px; border-radius: 0 0 0 4px; }
  .corner.br { bottom: 12px; right: 12px; border-bottom-width: 3px; border-right-width: 3px; border-radius: 0 0 4px 0; }
  .matched .corner { border-color: #00c896; }

  /* Hidden canvas for capture */
  #captureCanvas { display: none; }

  /* Controls */
  .controls {
    display: flex;
    gap: 10px;
    margin-top: 16px;
  }
  .btn {
    flex: 1;
    padding: 14px 20px;
    border: none;
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn:active { transform: scale(0.97); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

  .btn-scan {
    background: linear-gradient(135deg, #7c5cfc, #5a3fd6);
    color: white;
    box-shadow: 0 4px 20px rgba(124, 92, 252, 0.3);
  }
  .btn-scan:hover:not(:disabled) { box-shadow: 0 6px 30px rgba(124, 92, 252, 0.5); }

  .btn-enroll {
    background: linear-gradient(135deg, #00c896, #00a67a);
    color: white;
    box-shadow: 0 4px 20px rgba(0, 200, 150, 0.3);
  }
  .btn-enroll:hover:not(:disabled) { box-shadow: 0 6px 30px rgba(0, 200, 150, 0.5); }

  /* Mode selector */
  .mode-selector {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }
  .mode-btn {
    flex: 1;
    padding: 10px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    color: #888;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }
  .mode-btn.active {
    background: rgba(124, 92, 252, 0.15);
    border-color: rgba(124, 92, 252, 0.4);
    color: #a78bfa;
  }
  .mode-btn:hover { border-color: rgba(255,255,255,0.15); }
  .mode-label { font-size: 0.65rem; color: #555; margin-top: 2px; }

  /* Results panel */
  .result-panel {
    min-height: 300px;
  }
  .status-msg {
    text-align: center;
    padding: 60px 20px;
    color: #555;
    font-size: 0.9rem;
  }
  .status-msg .icon { font-size: 2.5rem; margin-bottom: 12px; }

  /* Match result */
  .match-result { animation: fadeUp 0.4s ease; }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .confidence-ring {
    width: 120px; height: 120px;
    margin: 0 auto 20px;
    position: relative;
  }
  .confidence-ring svg { transform: rotate(-90deg); }
  .confidence-ring circle {
    fill: none;
    stroke-width: 8;
    stroke-linecap: round;
  }
  .confidence-ring .bg { stroke: rgba(255,255,255,0.06); }
  .confidence-ring .fill { stroke: #00c896; transition: stroke-dashoffset 1s ease; }
  .confidence-value {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }
  .confidence-value .num { font-size: 1.8rem; font-weight: 700; color: #fff; }
  .confidence-value .pct { font-size: 0.8rem; color: #888; }

  .match-badge {
    text-align: center;
    margin-bottom: 20px;
  }
  .match-badge span {
    display: inline-block;
    padding: 4px 16px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
  }
  .badge-match { background: rgba(0,200,150,0.15); color: #00c896; border: 1px solid rgba(0,200,150,0.3); }
  .badge-nomatch { background: rgba(255,80,80,0.15); color: #ff5050; border: 1px solid rgba(255,80,80,0.3); }

  .profile-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .profile-item {
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
    padding: 10px 12px;
  }
  .profile-item.full { grid-column: 1 / -1; }
  .profile-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: #555; margin-bottom: 3px; }
  .profile-value { font-size: 0.85rem; color: #ddd; font-weight: 500; }

  .distance-bar {
    margin-top: 16px;
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border-radius: 8px;
  }
  .distance-bar .bar-track {
    height: 4px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    margin-top: 6px;
    position: relative;
  }
  .distance-bar .bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #00c896, #ffcc00, #ff5050);
    transition: width 0.8s ease;
  }

  /* Enroll form */
  .enroll-section { margin-top: 16px; }
  .input-group {
    margin-bottom: 10px;
  }
  .input-group label {
    display: block;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #666;
    margin-bottom: 4px;
  }
  .input-group input, .input-group select {
    width: 100%;
    padding: 10px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #ddd;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .input-group input:focus, .input-group select:focus {
    border-color: rgba(124, 92, 252, 0.5);
  }

  /* Log */
  .log-area {
    margin-top: 20px;
  }
  .log-entry {
    padding: 6px 0;
    font-size: 0.75rem;
    color: #555;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    font-family: monospace;
  }
  .log-entry.success { color: #00c896; }
  .log-entry.error { color: #ff5050; }
  .log-entry.info { color: #a78bfa; }
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>Mizpah ML - Live Face Scanner</h1>
    <p>Real-time face recognition against Supabase pgvector database</p>
    <div class="api-badge">API_URL_PLACEHOLDER</div>
  </div>

  <div class="main-grid">
    <!-- Left: Camera -->
    <div>
      <div class="card">
        <div class="card-title">Camera Feed</div>
        <div class="video-wrapper" id="videoWrapper">
          <video id="webcam" autoplay playsinline></video>
          <canvas id="captureCanvas"></canvas>
          <div class="video-overlay">
            <div class="scan-line"></div>
            <div class="corner tl"></div>
            <div class="corner tr"></div>
            <div class="corner bl"></div>
            <div class="corner br"></div>
          </div>
        </div>

        <div class="mode-selector">
          <button class="mode-btn active" data-mode="active" onclick="setMode('active')">
            <div>Active</div>
            <div class="mode-label">Medical Emergency</div>
          </button>
          <button class="mode-btn" data-mode="passive" onclick="setMode('passive')">
            <div>Passive</div>
            <div class="mode-label">Missing / Watchlist</div>
          </button>
        </div>

        <div class="controls">
          <button class="btn btn-scan" id="scanBtn" onclick="doScan()">Scan Face</button>
          <button class="btn btn-enroll" id="enrollBtn" onclick="toggleEnroll()">Enroll</button>
        </div>

        <!-- Enroll form (hidden by default) -->
        <div class="enroll-section" id="enrollSection" style="display:none;">
          <div class="input-group">
            <label>Person ID (UUID)</label>
            <input type="text" id="personId" placeholder="Auto-generated" />
          </div>
          <div class="input-group">
            <label>Profile Type</label>
            <select id="profileType">
              <option value="medical">Medical</option>
              <option value="watchlist">Watchlist</option>
              <option value="missing">Missing Person</option>
            </select>
          </div>
          <button class="btn btn-enroll" style="width:100%; margin-top:8px;" onclick="doEnroll()">
            Capture & Enroll
          </button>
        </div>
      </div>

      <!-- Log -->
      <div class="card" style="margin-top: 16px;">
        <div class="card-title">Activity Log</div>
        <div class="log-area" id="logArea">
          <div class="log-entry info">System ready. Waiting for camera...</div>
        </div>
      </div>
    </div>

    <!-- Right: Results -->
    <div>
      <div class="card result-panel" id="resultPanel">
        <div class="card-title">Scan Results</div>
        <div class="status-msg" id="statusMsg">
          <div class="icon">&#128247;</div>
          <div>Point the camera at a face and click <strong>Scan Face</strong></div>
        </div>
        <div id="resultContent" style="display:none;"></div>
      </div>
    </div>
  </div>
</div>

<script>
  const video = document.getElementById('webcam');
  const canvas = document.getElementById('captureCanvas');
  const ctx = canvas.getContext('2d');
  const wrapper = document.getElementById('videoWrapper');
  let currentMode = 'active';

  // Start webcam
  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      video.srcObject = stream;
      addLog('Camera started successfully', 'success');
    } catch (err) {
      addLog('Camera access denied: ' + err.message, 'error');
    }
  }

  function captureFrame() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
  }

  function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.mode === mode);
    });
    addLog('Mode set to: ' + mode, 'info');
  }

  function toggleEnroll() {
    const section = document.getElementById('enrollSection');
    const visible = section.style.display !== 'none';
    section.style.display = visible ? 'none' : 'block';
    if (!visible) {
      document.getElementById('personId').value = crypto.randomUUID();
    }
  }

  async function doScan() {
    const btn = document.getElementById('scanBtn');
    btn.disabled = true;
    btn.textContent = 'Scanning...';
    wrapper.classList.add('scanning');
    wrapper.classList.remove('matched');

    addLog('Capturing frame and sending to /scan...', 'info');
    const b64 = captureFrame();
    addLog('Image captured (' + (b64.length / 1024).toFixed(0) + ' KB base64)', 'info');

    try {
      const resp = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: b64, mode: currentMode })
      });
      const data = await resp.json();

      if (data.error) {
        addLog('Scan error: ' + data.error, 'error');
        showError(data.error);
      } else {
        addLog('Scan complete: matched=' + data.matched + ' confidence=' + data.confidence + '%', data.matched ? 'success' : 'info');
        showResult(data);
        if (data.matched) wrapper.classList.add('matched');
      }
    } catch (err) {
      addLog('Network error: ' + err.message, 'error');
      showError('Network error: ' + err.message);
    }

    wrapper.classList.remove('scanning');
    btn.disabled = false;
    btn.textContent = 'Scan Face';
  }

  async function doEnroll() {
    const personId = document.getElementById('personId').value || crypto.randomUUID();
    const profileType = document.getElementById('profileType').value;

    addLog('Capturing frame for enrollment...', 'info');
    const b64 = captureFrame();

    addLog('Enrolling: person_id=' + personId.substring(0, 8) + '... type=' + profileType, 'info');

    try {
      const resp = await fetch('/api/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: b64, person_id: personId, type: profileType })
      });
      const data = await resp.json();

      if (data.error) {
        addLog('Enrollment error: ' + data.error, 'error');
      } else if (data.success) {
        addLog('Enrolled! embedding_id=' + data.embedding_id, 'success');
        document.getElementById('personId').value = crypto.randomUUID();
      }
    } catch (err) {
      addLog('Network error: ' + err.message, 'error');
    }
  }

  function showResult(data) {
    const panel = document.getElementById('resultContent');
    const status = document.getElementById('statusMsg');
    status.style.display = 'none';
    panel.style.display = 'block';

    if (!data.matched) {
      panel.innerHTML = `
        <div class="match-result">
          <div class="confidence-ring">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle class="bg" cx="60" cy="60" r="52"/>
              <circle class="fill" cx="60" cy="60" r="52"
                stroke-dasharray="326.7" stroke-dashoffset="326.7" style="stroke: #ff5050;"/>
            </svg>
            <div class="confidence-value">
              <div class="num">0</div>
              <div class="pct">No Match</div>
            </div>
          </div>
          <div class="match-badge"><span class="badge-nomatch">NO MATCH FOUND</span></div>
          <div style="text-align:center; color:#666; font-size:0.85rem;">
            No matching face found in the database.<br>
            Try enrolling first, then scanning again.
          </div>
        </div>
      `;
      return;
    }

    const conf = data.confidence || 0;
    const circumference = 2 * Math.PI * 52;
    const offset = circumference * (1 - conf / 100);
    const profile = data.profile || {};

    let profileHTML = '';
    const fields = [
      { key: 'name', label: 'Name' },
      { key: 'type', label: 'Type' },
      { key: 'person_id', label: 'Person ID', full: true },
      { key: 'blood_type', label: 'Blood Type' },
      { key: 'emergency_contact', label: 'Emergency' },
    ];
    fields.forEach(f => {
      const val = profile[f.key];
      if (val) {
        profileHTML += `
          <div class="profile-item ${f.full ? 'full' : ''}">
            <div class="profile-label">${f.label}</div>
            <div class="profile-value">${val}</div>
          </div>`;
      }
    });
    if (profile.allergies && profile.allergies.length) {
      profileHTML += `
        <div class="profile-item full">
          <div class="profile-label">Allergies</div>
          <div class="profile-value">${profile.allergies.join(', ')}</div>
        </div>`;
    }
    if (profile.conditions && profile.conditions.length) {
      profileHTML += `
        <div class="profile-item full">
          <div class="profile-label">Conditions</div>
          <div class="profile-value">${profile.conditions.join(', ')}</div>
        </div>`;
    }

    const distPct = data.distance != null ? Math.min(100, (data.distance / 1.5) * 100) : 0;
    const strokeColor = conf >= 80 ? '#00c896' : conf >= 50 ? '#ffcc00' : '#ff5050';

    panel.innerHTML = `
      <div class="match-result">
        <div class="confidence-ring">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle class="bg" cx="60" cy="60" r="52"/>
            <circle class="fill" cx="60" cy="60" r="52"
              stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
              style="stroke: ${strokeColor};"/>
          </svg>
          <div class="confidence-value">
            <div class="num">${conf.toFixed(1)}</div>
            <div class="pct">Confidence</div>
          </div>
        </div>
        <div class="match-badge"><span class="badge-match">MATCH FOUND</span></div>
        <div class="profile-grid">${profileHTML}</div>
        <div class="distance-bar">
          <div class="profile-label">Vector Distance: ${data.distance != null ? data.distance.toFixed(4) : 'N/A'} / 1.5 threshold</div>
          <div class="bar-track"><div class="bar-fill" style="width:${distPct}%"></div></div>
        </div>
      </div>
    `;
  }

  function showError(msg) {
    const panel = document.getElementById('resultContent');
    const status = document.getElementById('statusMsg');
    status.style.display = 'none';
    panel.style.display = 'block';
    panel.innerHTML = `
      <div class="match-result" style="text-align:center; padding: 40px 20px;">
        <div style="font-size:2rem; margin-bottom:12px;">&#9888;</div>
        <div style="color:#ff5050; font-weight:600; margin-bottom:8px;">Error</div>
        <div style="color:#888; font-size:0.85rem;">${msg}</div>
      </div>
    `;
  }

  function addLog(msg, type = '') {
    const log = document.getElementById('logArea');
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + type;
    entry.textContent = `[${time}] ${msg}`;
    log.insertBefore(entry, log.firstChild);
    // Keep max 20 entries
    while (log.children.length > 20) log.removeChild(log.lastChild);
  }

  startCamera();
</script>
</body>
</html>
"""


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Serves the HTML page and proxies API calls to the Render ML service."""

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"  [{self.log_date_time_string()}] {args[0]}")

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            page = HTML_PAGE.replace('API_URL_PLACEHOLDER', API_URL)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(page.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ('/api/scan', '/api/enroll'):
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Determine the target API endpoint
            target = API_URL + self.path.replace('/api', '')
            print(f"  -> Proxying to {target}")

            try:
                req = urllib.request.Request(
                    target,
                    data=body,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = resp.read()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)

            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8', errors='replace')
                print(f"  -> API error {e.code}: {error_body[:200]}")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': f'ML API returned {e.code}: {error_body[:300]}'
                }).encode())

            except Exception as e:
                print(f"  -> Error: {e}")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': str(e)
                }).encode())
        else:
            self.send_response(404)
            self.end_headers()


def get_local_ip():
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'  # Fallback to localhost
    finally:
        s.close()
    return IP


def main():
    server = http.server.HTTPServer(('0.0.0.0', PORT), ProxyHandler)
    local_ip = get_local_ip()

    print("=" * 56)
    print("  MIZPAH ML - Live Webcam Demo")
    print("=" * 56)
    print(f"  Local URL:    http://localhost:{PORT}")
    if local_ip != '127.0.0.1':
        print(f"  Network URL:  http://{local_ip}:{PORT} (use on your phone)")
    print(f"  Remote API:   {API_URL}")
    print("=" * 56)
    print()
    print("  Your browser will open automatically.")
    print("  To stop the server, press Ctrl+C in this terminal.")
    print()

    # Open browser automatically
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.server_close()


if __name__ == '__main__':
    main()
