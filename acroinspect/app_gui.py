"""Servidor Web e Interfaz Gráfica de Usuario para AcroInspect."""

import http.server
import json
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

# Cargar dependencias locales
_vendor_dir = Path(__file__).resolve().parent.parent / ".vendor"
if _vendor_dir.is_dir() and str(_vendor_dir) not in sys.path:
    sys.path.insert(0, str(_vendor_dir))

from .extractor import AcroFormExtractor
from .comparator import AcroFormComparator

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AcroInspect - Inspector de Formularios PDF</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --success: #4ade80;
      --warning: #fbbf24;
      --danger: #f87171;
      --info: #818cf8;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    .container { max-width: 1200px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 32px; }
    header h1 { font-size: 2.2rem; font-weight: 800; color: #fff; margin-bottom: 8px; }
    header h1 span { color: var(--primary); }
    header p { color: var(--text-muted); font-size: 1.05rem; }

    /* Tabs */
    .tabs { display: flex; justify-content: center; gap: 12px; margin-bottom: 28px; }
    .tab-btn {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 12px 28px;
      border-radius: 9999px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .tab-btn:hover { color: #fff; border-color: var(--primary); }
    .tab-btn.active {
      background: var(--primary);
      color: #0f172a;
      border-color: var(--primary);
      box-shadow: 0 4px 14px rgba(56, 189, 248, 0.4);
    }

    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

    /* Cards */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .upload-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
    @media (max-width: 768px) { .upload-grid { grid-template-columns: 1fr; } }

    .dropzone {
      border: 2px dashed var(--card-border);
      border-radius: var(--radius);
      padding: 36px 20px;
      text-align: center;
      cursor: pointer;
      background: rgba(15, 23, 42, 0.6);
      transition: all 0.2s ease;
      position: relative;
    }
    .dropzone:hover, .dropzone.dragover {
      border-color: var(--primary);
      background: rgba(56, 189, 248, 0.05);
    }
    .dropzone input[type="file"] {
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      opacity: 0; cursor: pointer;
    }
    .dropzone-icon { font-size: 2.5rem; margin-bottom: 12px; color: var(--primary); }
    .file-name { margin-top: 10px; font-weight: bold; color: var(--primary); word-break: break-all; }

    .btn-action {
      display: block;
      width: 100%;
      background: linear-gradient(135deg, var(--primary), var(--primary-hover));
      color: #0f172a;
      border: none;
      border-radius: var(--radius);
      padding: 14px;
      font-size: 1.1rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.1s ease, box-shadow 0.2s ease;
      box-shadow: 0 4px 14px rgba(56, 189, 248, 0.3);
    }
    .btn-action:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(56, 189, 248, 0.45); }
    .btn-action:disabled { background: var(--card-border); color: var(--text-muted); cursor: not-allowed; transform: none; box-shadow: none; }

    /* Results */
    .summary-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-badge {
      flex: 1;
      min-width: 140px;
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 16px;
      text-align: center;
    }
    .stat-badge .num { font-size: 1.8rem; font-weight: 800; display: block; }
    .stat-badge .lbl { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

    .badge-match { color: var(--success); }
    .badge-mismatch { color: var(--warning); }
    .badge-missing { color: var(--danger); }
    .badge-extra { color: var(--info); }

    /* Tables */
    .table-container { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--card-border); }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { background: #0f172a; padding: 14px 18px; color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; border-bottom: 1px solid var(--card-border); }
    td { padding: 14px 18px; border-bottom: 1px solid var(--card-border); font-size: 0.95rem; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255, 255, 255, 0.02); }

    .tag {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    .tag-match { background: rgba(74, 222, 128, 0.15); color: var(--success); border: 1px solid rgba(74, 222, 128, 0.3); }
    .tag-mismatch { background: rgba(251, 191, 36, 0.15); color: var(--warning); border: 1px solid rgba(251, 191, 36, 0.3); }
    .tag-missing { background: rgba(248, 113, 113, 0.15); color: var(--danger); border: 1px solid rgba(248, 113, 113, 0.3); }
    .tag-extra { background: rgba(129, 140, 248, 0.15); color: var(--info); border: 1px solid rgba(129, 140, 248, 0.3); }

    .order-alert {
      background: rgba(251, 191, 36, 0.1);
      border: 1px solid rgba(251, 191, 36, 0.3);
      color: var(--warning);
      padding: 16px;
      border-radius: var(--radius);
      margin-bottom: 20px;
      font-size: 0.95rem;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Acro<span>Inspect</span></h1>
      <p>Extractor secuencial y comparador de variables de formularios AcroForm</p>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('tab-extract')">🔍 Extraer Variables</button>
      <button class="tab-btn" onclick="switchTab('tab-compare')">⚖️ Comparar 2 PDFs</button>
    </div>

    <!-- TAB: EXTRAER -->
    <div id="tab-extract" class="tab-content active">
      <div class="card">
        <div class="dropzone" id="dz-extract">
          <input type="file" id="file-extract" accept=".pdf" onchange="handleFileSelected(this, 'txt-extract')">
          <div class="dropzone-icon">📄</div>
          <h3>Selecciona o arrastra un archivo PDF</h3>
          <p style="color: var(--text-muted); margin-top: 6px;">El documento debe contener formulario AcroForm</p>
          <div id="txt-extract" class="file-name"></div>
        </div>
        <button id="btn-extract" class="btn-action" style="margin-top: 20px;" onclick="doExtract()" disabled>
          Extraer Variables del Formulario
        </button>
      </div>

      <div id="res-extract" class="card" style="display: none;">
        <h2 style="margin-bottom: 16px;">Campos Extraídos (<span id="count-extract">0</span>)</h2>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th style="width: 60px;">#</th>
                <th>Nombre de Variable</th>
                <th>Tipo de Campo</th>
                <th>Página</th>
                <th>Obligatorio</th>
                <th>Solo Lectura</th>
              </tr>
            </thead>
            <tbody id="tbody-extract"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB: COMPARAR -->
    <div id="tab-compare" class="tab-content">
      <div class="card">
        <div class="upload-grid">
          <div class="dropzone" id="dz-cmp1">
            <input type="file" id="file-cmp1" accept=".pdf" onchange="handleFileSelected(this, 'txt-cmp1')">
            <div class="dropzone-icon">1️⃣</div>
            <h3>PDF Base (Referencia)</h3>
            <p style="color: var(--text-muted); margin-top: 6px;">Estructura de variables esperada</p>
            <div id="txt-cmp1" class="file-name"></div>
          </div>
          <div class="dropzone" id="dz-cmp2">
            <input type="file" id="file-cmp2" accept=".pdf" onchange="handleFileSelected(this, 'txt-cmp2')">
            <div class="dropzone-icon">2️⃣</div>
            <h3>PDF a Comparar</h3>
            <p style="color: var(--text-muted); margin-top: 6px;">Documento a evaluar</p>
            <div id="txt-cmp2" class="file-name"></div>
          </div>
        </div>
        <button id="btn-compare" class="btn-action" onclick="doCompare()" disabled>
          Comparar Estructuras
        </button>
      </div>

      <div id="res-compare" class="card" style="display: none;">
        <h2 style="margin-bottom: 20px;">Resultado de la Comparación</h2>

        <div class="summary-bar">
          <div class="stat-badge">
            <span class="num badge-match" id="c-match">0</span>
            <span class="lbl">Coincidencias</span>
          </div>
          <div class="stat-badge">
            <span class="num badge-mismatch" id="c-mismatch">0</span>
            <span class="lbl">Discrepancias Tipo</span>
          </div>
          <div class="stat-badge">
            <span class="num badge-missing" id="c-missing">0</span>
            <span class="lbl">Faltantes en PDF 2</span>
          </div>
          <div class="stat-badge">
            <span class="num badge-extra" id="c-extra">0</span>
            <span class="lbl">Extra en PDF 2</span>
          </div>
        </div>

        <div id="order-box" style="display: none;" class="order-alert"></div>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Estado</th>
                <th>Nombre de Variable</th>
                <th>Tipo en PDF Base</th>
                <th>Tipo en PDF 2</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody id="tbody-compare"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }

    function handleFileSelected(input, labelId) {
      const file = input.files[0];
      const lbl = document.getElementById(labelId);
      if (file) {
        lbl.textContent = '✓ ' + file.name + ' (' + Math.round(file.size / 1024) + ' KB)';
      } else {
        lbl.textContent = '';
      }
      checkButtons();
    }

    function checkButtons() {
      const fExt = document.getElementById('file-extract').files[0];
      document.getElementById('btn-extract').disabled = !fExt;

      const fCmp1 = document.getElementById('file-cmp1').files[0];
      const fCmp2 = document.getElementById('file-cmp2').files[0];
      document.getElementById('btn-compare').disabled = !(fCmp1 && fCmp2);
    }

    async function fileToBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const b64 = reader.result.split(',')[1];
          resolve(b64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    async function doExtract() {
      const file = document.getElementById('file-extract').files[0];
      if (!file) return;

      const btn = document.getElementById('btn-extract');
      btn.disabled = true;
      btn.textContent = 'Analizando PDF...';

      try {
        const b64 = await fileToBase64(file);
        const resp = await fetch('/api/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: file.name, data: b64 })
        });
        const fields = await resp.json();

        const tbody = document.getElementById('tbody-extract');
        tbody.innerHTML = '';
        document.getElementById('count-extract').textContent = fields.length;

        fields.forEach(f => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>#${f.index}</strong></td>
            <td><code>${f.name}</code></td>
            <td><span class="tag tag-match">${f.field_type}</span></td>
            <td>${f.page || '-'}</td>
            <td>${f.required ? '⚠️ Sí' : 'No'}</td>
            <td>${f.read_only ? '🔒 Sí' : 'No'}</td>
          `;
          tbody.appendChild(tr);
        });

        document.getElementById('res-extract').style.display = 'block';
      } catch (err) {
        alert('Error extrayendo variables: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Extraer Variables del Formulario';
      }
    }

    async function doCompare() {
      const f1 = document.getElementById('file-cmp1').files[0];
      const f2 = document.getElementById('file-cmp2').files[0];
      if (!f1 || !f2) return;

      const btn = document.getElementById('btn-compare');
      btn.disabled = true;
      btn.textContent = 'Comparando documentos...';

      try {
        const [b64_1, b64_2] = await Promise.all([fileToBase64(f1), fileToBase64(f2)]);
        const resp = await fetch('/api/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name1: f1.name, data1: b64_1,
            name2: f2.name, data2: b64_2
          })
        });
        const rep = await resp.json();

        document.getElementById('c-match').textContent = rep.matching_fields.length;
        document.getElementById('c-mismatch').textContent = rep.type_mismatches.length;
        document.getElementById('c-missing').textContent = rep.missing_in_target.length;
        document.getElementById('c-extra').textContent = rep.extra_in_target.length;

        const orderBox = document.getElementById('order-box');
        if (rep.order_mismatches && rep.order_mismatches.length > 0) {
          orderBox.textContent = '⚠️ ' + rep.order_mismatches.join('\\n');
          orderBox.style.display = 'block';
        } else {
          orderBox.style.display = 'none';
        }

        const tbody = document.getElementById('tbody-compare');
        tbody.innerHTML = '';

        const appendRow = (statusTag, name, baseType, targetType, note) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${statusTag}</td>
            <td><code>${name}</code></td>
            <td>${baseType || '-'}</td>
            <td>${targetType || '-'}</td>
            <td style="color: var(--text-muted); font-size: 0.9rem;">${note}</td>
          `;
          tbody.appendChild(tr);
        };

        rep.type_mismatches.forEach(d => {
          appendRow('<span class="tag tag-mismatch">Tipo Diferente</span>', d.name, d.base_type, d.target_type, d.note);
        });
        rep.missing_in_target.forEach(d => {
          appendRow('<span class="tag tag-missing">Falta en PDF 2</span>', d.name, d.base_type, '-', d.note);
        });
        rep.extra_in_target.forEach(d => {
          appendRow('<span class="tag tag-extra">Extra en PDF 2</span>', d.name, '-', d.target_type, d.note);
        });
        rep.matching_fields.forEach(d => {
          appendRow('<span class="tag tag-match">Coincide</span>', d.name, d.base_type, d.target_type, 'Exacto');
        });

        document.getElementById('res-compare').style.display = 'block';
      } catch (err) {
        alert('Error en la comparación: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Comparar Estructuras';
      }
    }
  </script>
</body>
</html>
"""


class AcroInspectRequestHandler(http.server.BaseHTTPRequestHandler):
    """Manejador HTTP para la API de AcroInspect y la interfaz web."""

    def log_message(self, format, *args):
        # Silenciar logs ruidosos en la terminal
        pass

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            import base64
            import io

            payload = json.loads(body.decode("utf-8"))

            if url.path == "/api/extract":
                pdf_bytes = base64.b64decode(payload["data"])
                extractor = AcroFormExtractor(io.BytesIO(pdf_bytes))
                fields = [f.to_dict() for f in extractor.extract_fields()]

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(fields).encode("utf-8"))

            elif url.path == "/api/compare":
                pdf1_bytes = base64.b64decode(payload["data1"])
                pdf2_bytes = base64.b64decode(payload["data2"])

                ext1 = AcroFormExtractor(io.BytesIO(pdf1_bytes))
                ext2 = AcroFormExtractor(io.BytesIO(pdf2_bytes))

                report = AcroFormComparator.compare(
                    base_fields=ext1.extract_fields(),
                    target_fields=ext2.extract_fields(),
                    base_name=payload.get("name1", "PDF_1"),
                    target_name=payload.get("name2", "PDF_2"),
                )

                result = {
                  "base_pdf": report.base_pdf,
                  "target_pdf": report.target_pdf,
                  "total_base_fields": report.total_base_fields,
                  "total_target_fields": report.total_target_fields,
                  "is_identical": report.is_identical,
                  "matching_fields": [m.to_dict() for m in report.matching_fields],
                  "type_mismatches": [m.to_dict() for m in report.type_mismatches],
                  "missing_in_target": [m.to_dict() for m in report.missing_in_target],
                  "extra_in_target": [m.to_dict() for m in report.extra_in_target],
                  "order_mismatches": report.order_mismatches,
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def start_server(port: int = 8765, open_browser: bool = True):
    """Inicia el servidor web local interactivo."""
    handler = AcroInspectRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://127.0.0.1:{port}"
        print("=" * 65)
        print(f"🚀 AcroInspect UI ejecutándose en: {url}")
        print("   Presiona Ctrl + C en la terminal para detener el servidor.")
        print("=" * 65)

        if open_browser:
            threading.Timer(0.8, lambda: webbrowser.open(url)).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
