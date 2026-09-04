from flask import Flask
import os

app = Flask(__name__)

# ===== SAMPLE CSV DATA (for the demo button) =====
SAMPLE_CSV = """Store,Address,City,Province,1 Day TX,7 Day Reject %,7 Day Uptime %,Last PM Date,Latitude,Longitude,Phone
Super C 5917,2125 bl Roland-Therrien,Longueuil,QC,4,1.4,57.1,2026-01-15,45.53,-73.51,450-555-0199
Loblaws 1051,1980 Ogilvie Rd.,Gloucester,ON,4,4.1,73.0,2026-02-01,45.45,-75.65,613-555-0153
Metro 742,425 Bloor St W,Toronto,ON,7,4.8,89.9,2026-01-28,43.66,-79.40,416-555-0188
Metro 235,1161 Barton Street E.,Hamilton,ON,7,9.0,98.5,2026-02-10,43.25,-79.82,905-555-0178
Zehrs 550,821 Niagara St. North,Welland,ON,9,7.7,100.0,2026-01-18,43.01,-79.25,905-555-0144
Loblaws 1016,3040 Wonderland Rd S.,London,ON,6,13.4,99.4,2026-02-05,42.94,-81.29,519-555-0166
Metro 702,250 The East Mall,Etobicoke,ON,4,4.6,86.4,2026-02-10,43.63,-79.57,416-555-0122
Super C 5928,1515 Boulevard Marcel-Laurin,Saint-laurent,QC,4,2.2,65.0,2026-01-22,45.53,-73.70,514-555-0111
Super C 5919,8330 boul. Taschereau,Brossard,QC,3,1.0,61.9,2026-01-10,45.47,-73.45,450-555-0133
Super C 5930,3050 Blvd. Portland,Sherbrooke,QC,3,0.6,61.9,2026-02-08,45.41,-71.88,819-555-0144
Loblaws 1170,363 Rideau St.,Ottawa,ON,5,5.3,84.3,2026-01-30,45.42,-75.69,613-555-0155
Zehrs 554,50 4th Avenue,Orangeville,ON,5,9.4,59.5,2026-02-02,43.92,-80.10,519-555-0166
Metro 159,333 King St. E,Gananoque,ON,4,1.6,86.7,2026-02-12,44.33,-76.17,613-555-0177
Food Basics 674,6770 Mcleod Road,Niagara Falls,ON,5,1.1,91.3,2026-02-03,43.09,-79.09,905-555-0188
Safeway 4848,850 KEEWATIN STREET,Winnipeg,MB,5,1.7,53.5,2026-02-06,49.88,-97.16,204-555-0199
Maxi & CIE 8675,8305 Avenue papineau,Montreal,QC,7,2.4,66.3,2026-01-25,45.56,-73.58,514-555-0200
Metro 153,73 Main St. W,Picton,ON,1,5.7,28.3,2026-01-14,44.01,-77.14,613-555-0211
Safeway 4912,20871 Fraser Highway,Langley,BC,12,2.4,100.0,2026-02-15,49.10,-122.61,604-555-0222
Safeway 4966,1780 E Broadway,Vancouver,BC,13,2.0,99.9,2026-02-20,49.26,-123.07,604-555-0233
The Real Canadian Superstore 1559,32136 Lougheed Highway,Mission,BC,6,3.0,100.0,2026-02-18,49.14,-122.30,604-555-0244
Maxi 8635,355 Rue Principale,Lachute,QC,6,3.9,72.4,2026-01-12,45.65,-74.38,450-555-0255
Food Basics 843,1070 Majr Mackenzie Dr E,Richmond Hill,ON,6,9.8,98.0,2026-02-07,43.88,-79.44,905-555-0266
Metro 135,400 Bayfield St,Barrie,ON,8,7.2,99.9,2026-02-11,44.39,-79.69,705-555-0277
Food Basics 904,227 Vodden Street,Brampton,ON,12,2.6,99.9,2026-02-14,43.70,-79.76,905-555-0288
Metro 800,40 Eglinton Square,Scarborough,ON,10,2.5,99.9,2026-02-19,43.73,-79.28,416-555-0299"""


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fleet Intelligence LIVE</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #f0f4fb;
            padding: 20px 16px;
            color: #0a1a2b;
        }
        .container { max-width: 1440px; margin: 0 auto; }

        /* ---- HERO ---- */
        .hero-header {
            background: linear-gradient(145deg, #0f2b4a 0%, #1a3a60 50%, #0f2b4a 100%);
            border-radius: 40px;
            padding: 2.2rem 2.8rem;
            margin-bottom: 2rem;
            color: white;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 20px 40px -12px rgba(10, 30, 60, 0.3);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .hero-left h1 {
            font-size: 2.2rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            gap: 14px;
            flex-wrap: wrap;
            letter-spacing: -0.02em;
        }
        .hero-left h1 i { color: #f0b90b; }
        .live-pulse {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.2);
            backdrop-filter: blur(4px);
            padding: 6px 16px;
            border-radius: 40px;
            font-size: 0.75rem;
            font-weight: 700;
            color: #86efac;
            border: 1px solid rgba(34, 197, 94, 0.3);
            letter-spacing: 0.3px;
            text-transform: uppercase;
        }
        .live-pulse::before {
            content: "";
            width: 8px;
            height: 8px;
            background: #22c55e;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 100% { opacity: 0.2; transform: scale(1.4); } }
        .hero-left .subtitle {
            color: #b0c8e5;
            margin-top: 6px;
            font-size: 0.95rem;
            font-weight: 400;
        }
        .hero-right { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
        .hero-btn {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255,255,255,0.15);
            padding: 10px 22px;
            border-radius: 40px;
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.25s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
        }
        .hero-btn:hover { background: rgba(255,255,255,0.2); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
        .hero-btn.primary {
            background: linear-gradient(135deg, #f0b90b, #f5c947);
            color: #0a1a2b;
            border: none;
            font-weight: 700;
        }
        .hero-btn.primary:hover { background: linear-gradient(135deg, #f5c947, #f0b90b); }

        /* ---- UPLOAD CARD ---- */
        .upload-card {
            max-width: 900px;
            margin: 0 auto 2.5rem auto;
            background: white;
            border-radius: 32px;
            padding: 2.5rem 3rem;
            text-align: center;
            box-shadow: 0 20px 45px -12px rgba(0,0,0,0.08);
            border: 1px solid rgba(255,255,255,0.7);
            backdrop-filter: blur(8px);
            transition: all 0.3s;
        }
        .upload-card h2 {
            font-size: 1.8rem;
            font-weight: 800;
            color: #0a1a2b;
            margin-bottom: 4px;
        }
        .upload-card p { color: #64748b; margin-bottom: 20px; font-size: 1rem; }
        .upload-button {
            background: #f1f5f9;
            border: 2px dashed #cbd5e1;
            border-radius: 24px;
            padding: 2.2rem;
            cursor: pointer;
            display: inline-block;
            transition: all 0.3s;
            width: 100%;
            max-width: 400px;
        }
        .upload-button:hover { background: #e8edf5; border-color: #94a3b8; transform: scale(1.01); }
        .upload-button i { font-size: 2.5rem; color: #1e3a5f; margin-bottom: 8px; }
        .upload-button strong { font-size: 1.1rem; color: #0a1a2b; }
        .upload-button small { display: block; color: #94a3b8; margin-top: 4px; }
        .demo-btn-wrapper {
            margin-top: 18px;
            display: flex;
            gap: 14px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .demo-btn {
            padding: 14px 32px;
            border-radius: 60px;
            border: none;
            font-weight: 800;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }
        .demo-btn:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.15); }
        .demo-btn.sample {
            background: linear-gradient(135deg, #f0b90b, #f5c947);
            color: #0a1a2b;
        }
        .demo-btn.screenshot {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
        }
        .divider { display: flex; align-items: center; gap: 16px; margin: 16px 0; color: #94a3b8; font-size: 0.85rem; }
        .divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: #e2e8f0; }
        #fileStatus { margin-top: 12px; color: #475569; font-weight: 500; }

        /* ---- DASHBOARD ---- */
        #dashboard { display: none; }
        #dataTimestamp {
            background: #e8edf5;
            padding: 8px 20px;
            border-radius: 40px;
            display: inline-block;
            margin-bottom: 24px;
            font-weight: 600;
            color: #1e3a5f;
            font-size: 0.9rem;
        }

        /* ---- KPI GRID ---- */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 28px;
        }
        .kpi-card {
            background: white;
            border-radius: 24px;
            padding: 20px 16px;
            border: 1px solid #e9edf2;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            transition: all 0.25s;
        }
        .kpi-card:hover { transform: translateY(-4px); box-shadow: 0 12px 28px -8px rgba(0,0,0,0.06); }
        .kpi-label {
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .kpi-value { font-size: 2.2rem; font-weight: 900; color: #0a1a2b; }
        .kpi-loss { color: #dc2626; }
        .kpi-green { color: #10b981; }
        .kpi-blue { color: #2563eb; }
        .kpi-yellow { color: #f59e0b; }

        /* ---- FILTERS ---- */
        .filters {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 28px;
            align-items: flex-end;
            background: white;
            padding: 18px 22px;
            border-radius: 24px;
            border: 1px solid #e9edf2;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        }
        .filter-group { display: flex; flex-direction: column; gap: 6px; min-width: 120px; flex: 1; }
        .filter-group label { font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.3px; }
        select, input, button {
            padding: 10px 14px;
            border-radius: 14px;
            font-size: 0.85rem;
            border: 1px solid #e2e8f0;
            background: white;
            transition: all 0.2s;
        }
        select:focus, input:focus { border-color: #1e3a5f; outline: none; box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1); }
        button {
            background: #1e3a5f;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        button:hover { background: #0f2b4a; transform: translateY(-1px); }
        .reset-btn { background: #f1f5f9; color: #1e293b; border: 1px solid #e2e8f0; }
        .reset-btn:hover { background: #e2e8f0; }

        /* ---- TABLE ---- */
        .table-wrapper {
            background: white;
            border-radius: 24px;
            overflow-x: auto;
            max-height: 480px;
            border: 1px solid #e9edf2;
            margin-bottom: 28px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.8rem; min-width: 1200px; }
        th {
            background: #f8fafc;
            padding: 14px 12px;
            font-weight: 700;
            border-bottom: 2px solid #e2e8f0;
            position: sticky;
            top: 0;
            text-align: left;
            color: #1e293b;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        td { padding: 12px 12px; border-bottom: 1px solid #f1f5f9; }
        .critical-row { background-color: #fef2f2; border-left: 4px solid #dc2626; }
        .warning-row { background-color: #fffbeb; border-left: 4px solid #f59e0b; }
        .good-row { background-color: #f0fdf4; border-left: 4px solid #10b981; }
        .offline-row { background-color: #f1f5f9; border-left: 4px solid #6b7280; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 40px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .badge-critical { background: #fee2e2; color: #dc2626; }
        .badge-warning { background: #fef3c7; color: #f59e0b; }
        .badge-good { background: #dcfce7; color: #10b981; }
        .badge-offline { background: #e2e8f0; color: #6b7280; }

        /* ---- MAP ---- */
        .map-container {
            background: white;
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 28px;
            border: 1px solid #e9edf2;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        }
        .map-container h3 { font-weight: 700; color: #0a1a2b; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
        #map { height: 400px; border-radius: 16px; z-index: 1; }
        .map-legend {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 14px;
            font-size: 0.8rem;
            font-weight: 500;
            flex-wrap: wrap;
        }
        .map-legend-dot { display: inline-block; width: 14px; height: 14px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }

        /* ---- DEMO MODAL ---- */
        #demoModal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 9999;
            justify-content: center;
            align-items: center;
            padding: 20px;
            backdrop-filter: blur(4px);
        }
        .modal-content {
            background: white;
            border-radius: 32px;
            max-width: 900px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            padding: 28px;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-close {
            position: sticky;
            top: 0;
            float: right;
            background: #f1f5f9;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 1.2rem;
            cursor: pointer;
            z-index: 10;
            transition: 0.2s;
        }
        .modal-close:hover { background: #e2e8f0; }
        .modal-content h2 { margin-bottom: 4px; }
        .modal-content .sub { color: #64748b; margin-bottom: 16px; }
        .screenshot-grid {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .screenshot-item {
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            overflow: hidden;
            background: #f8fafc;
        }
        .screenshot-item img {
            width: 100%;
            display: block;
        }
        .screenshot-item .caption {
            padding: 8px 12px;
            font-size: 0.8rem;
            color: #64748b;
            text-align: center;
            background: white;
        }
        .modal-footer { margin-top: 20px; text-align: center; }
        .modal-footer button {
            background: #1e3a5f;
            color: white;
            padding: 10px 32px;
            border-radius: 40px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }
        .modal-footer button:hover { background: #0f2b4a; }

        /* ---- TOAST ---- */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #0a1a2b;
            color: white;
            padding: 14px 28px;
            border-radius: 60px;
            font-size: 0.9rem;
            font-weight: 500;
            z-index: 1000;
            display: none;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }

        /* ---- RESPONSIVE ---- */
        @media (max-width: 768px) {
            .hero-header { flex-direction: column; text-align: center; padding: 1.5rem; }
            .kpi-grid { grid-template-columns: repeat(2, 1fr); }
            .filters { flex-direction: column; }
            .filter-group { min-width: 100%; }
            .upload-card { padding: 1.5rem; }
            .demo-btn-wrapper { flex-direction: column; align-items: center; }
            .demo-btn { width: 100%; justify-content: center; }
        }
    </style>
</head>
<body>

<div class="container">

    <!-- HERO HEADER -->
    <div class="hero-header">
        <div class="hero-left">
            <h1><i class="fas fa-chart-line"></i> Fleet Intelligence <span class="live-pulse">LIVE</span></h1>
            <div class="subtitle">Real-time asset performance &amp; predictive analytics</div>
        </div>
        <div class="hero-right">
            <button class="hero-btn" id="uploadBtn"><i class="fas fa-upload"></i> Upload CSV</button>
            <button class="hero-btn primary" id="screenshotBtn"><i class="fas fa-camera"></i> Screenshot</button>
            <button class="hero-btn primary" id="reportBtn"><i class="fas fa-file-pdf"></i> Report</button>
        </div>
    </div>

    <input type="file" id="csvFile" accept=".csv" style="display:none;">

    <!-- UPLOAD CARD -->
    <div class="upload-card" id="uploadCard">
        <h2><i class="fas fa-cloud-upload-alt" style="color:#1e3a5f;"></i> Upload Your Fleet Data</h2>
        <p>Upload a CSV file with your asset data</p>
        <div class="upload-button" id="uploadBtn2">
            <i class="fas fa-file-csv"></i>
            <strong>Choose File</strong>
            <small>or drag &amp; drop</small>
        </div>

        <div class="divider"><span>or</span></div>

        <div class="demo-btn-wrapper">
            <button class="demo-btn screenshot" id="viewDemoBtn">
                <i class="fas fa-image"></i> View Demo Screenshots
            </button>
            <button class="demo-btn sample" id="loadSampleBtn">
                <i class="fas fa-rocket"></i> Load Sample Data
            </button>
        </div>

        <div id="fileStatus"></div>
    </div>

    <!-- DASHBOARD -->
    <div id="dashboard">
        <div id="dataTimestamp"></div>

        <!-- KPI Grid -->
        <div class="kpi-grid" id="kpiGrid">
            <div class="kpi-card"><div class="kpi-label">📊 Total Assets</div><div class="kpi-value kpi-blue" id="kpiTotal">0</div></div>
            <div class="kpi-card"><div class="kpi-label">🔴 Critical</div><div class="kpi-value" id="kpiCritical" style="color:#dc2626;">0</div></div>
            <div class="kpi-card"><div class="kpi-label">🟡 Warning</div><div class="kpi-value" id="kpiWarning" style="color:#f59e0b;">0</div></div>
            <div class="kpi-card"><div class="kpi-label">💸 Daily Loss</div><div class="kpi-value kpi-loss" id="kpiLoss">$0</div></div>
        </div>

        <!-- Filters -->
        <div class="filters">
            <div class="filter-group"><label>Region</label><select id="regionFilter"><option value="all">All</option></select></div>
            <div class="filter-group"><label>Status</label><select id="statusFilter"><option value="all">All</option><option value="critical">Critical</option><option value="warning">Warning</option><option value="good">Good</option><option value="offline">Offline</option></select></div>
            <div class="filter-group"><label>Search</label><input type="text" id="searchInput" placeholder="Search assets..."></div>
            <button id="resetBtn" class="reset-btn"><i class="fas fa-undo"></i> Reset</button>
        </div>

        <!-- Table -->
        <div class="table-wrapper">
            <table id="dataTable">
                <thead><tr><th>Asset</th><th>Address</th><th>City</th><th>Region</th><th>Status</th><th>Volume</th><th>Reject%</th><th>Uptime%</th><th>Est. Revenue</th><th>Daily Loss</th><th>Service Days</th><th>Call</th></tr></thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>

        <!-- Map -->
        <div class="map-container">
            <h3><i class="fas fa-map-pin" style="color:#1e3a5f;"></i> Asset Location Map</h3>
            <div id="map"></div>
            <div class="map-legend">
                <span><span class="map-legend-dot" style="background:#dc2626;"></span> Critical</span>
                <span><span class="map-legend-dot" style="background:#f59e0b;"></span> Warning</span>
                <span><span class="map-legend-dot" style="background:#10b981;"></span> Good</span>
                <span><span class="map-legend-dot" style="background:#6b7280;"></span> Offline</span>
            </div>
        </div>
    </div>
</div>

<!-- ===== DEMO MODAL ===== -->
<div id="demoModal">
    <div class="modal-content">
        <button class="modal-close" onclick="closeDemo()">✕</button>
        <h2>📸 Dashboard Preview</h2>
        <p class="sub">Here's what the dashboard looks like with real data</p>

        <div class="screenshot-grid">
            <div class="screenshot-item">
                <img src="Fleetintel0.png" alt="Dashboard screenshot 1 - KPI Cards and Table View">
                <div class="caption">📊 KPI Cards &amp; Table View</div>
            </div>
            <div class="screenshot-item">
                <img src="Fleetintel1.png" alt="Dashboard screenshot 2 - Map View with Color-Coded Markers">
                <div class="caption">🗺️ Map View with Color-Coded Markers</div>
            </div>
        </div>

        <div class="modal-footer">
            <button onclick="closeDemo()">Close</button>
        </div>
    </div>
</div>

<div id="toast" class="toast"></div>

<script>
    // ============================================================
    // FLEET INTELLIGENCE DASHBOARD — WITH SAMPLE DATA & DEMO MODAL
    // ============================================================

    let allData = [];
    let currentSort = { column: 'loss', direction: 'desc' };
    let map = null;

    const TRANSACTION_VALUE = 5;

    // ===== HELPERS =====
    function showToast(msg) {
        let t = document.getElementById('toast');
        t.textContent = msg;
        t.style.display = 'block';
        setTimeout(() => t.style.display = 'none', 3000);
    }

    function getStatus(r) {
        let rej = parseFloat(r.Reject7Day) || 0;
        let uptime = parseFloat(r.Uptime7Day) || 100;
        if (r.KioskState === 'Offline' || uptime < 10) return 'Offline';
        if (rej >= 8) return 'Critical';
        if (rej >= 4) return 'Warning';
        return 'Good';
    }

    function getStatusBadge(r) {
        let s = getStatus(r);
        const map = {
            'Critical': '<span class="badge badge-critical">Critical</span>',
            'Warning': '<span class="badge badge-warning">Warning</span>',
            'Offline': '<span class="badge badge-offline">Offline</span>',
            'Good': '<span class="badge badge-good">Good</span>'
        };
        return map[s] || map['Good'];
    }

    function getVolume(r) { return parseFloat(r.Tx1Day) || 0; }
    function getReject(r) { return parseFloat(r.Reject7Day) || 0; }
    function getUptime(r) { return parseFloat(r.Uptime7Day) || 100; }
    function getEstRevenue(r) { return getVolume(r) * TRANSACTION_VALUE; }

    function calcLoss(r) {
        let vol = getVolume(r);
        let rej = getReject(r);
        let uptime = getUptime(r);
        return (vol * (rej / 100) * TRANSACTION_VALUE) + (vol * ((100 - uptime) / 100) * 4);
    }

    function getRegion(r) { return r.Province || r.State || 'Unknown'; }

    function getDaysSinceService(r) {
        let d = r.LastPM || '';
        if (!d || d === '—') return null;
        try {
            let parts = d.match(/(\\d{2})\\/(\\d{2})\\/(\\d{2})/);
            if (parts) {
                let date = new Date(2000 + parseInt(parts[3]), parseInt(parts[1]) - 1, parseInt(parts[2]));
                return Math.ceil((new Date() - date) / 86400000);
            }
        } catch (e) {}
        return null;
    }

    function getPhoneNumber(r) { return r.Phone || r['Store Phone Number'] || ''; }
    function escapeHtml(s) { if (!s) return ''; return s.replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[m]); }

    // ===== PARSE CSV =====
    function parseCSV(text) {
        const lines = text.split(/\\r?\\n/);
        if (lines.length < 2) return false;
        let headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
        let data = [];
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            let row = {}, col = 0, cur = '', inQ = false;
            for (let ch of lines[i]) {
                if (ch === '"') inQ = !inQ;
                else if (ch === ',' && !inQ) {
                    row[headers[col]] = cur.trim().replace(/"/g, '');
                    cur = '';
                    col++;
                } else cur += ch;
            }
            if (col < headers.length) row[headers[col]] = cur.trim().replace(/"/g, '');
            if (Object.keys(row).length) data.push(row);
        }
        if (!data.length) return false;
        allData = data.map(row => ({
            Store: row.Store || row['Store Name'] || 'Unknown',
            Address: row.Address || '',
            City: row.City || '',
            Province: row.State || row.Province || '',
            KioskState: row['Kiosk State'] || row.State || 'Attract',
            Tx1Day: row['1 Day TX'] || row.Volume || '0',
            Tx7Day: row['7 Day TX'] || '0',
            Reject7Day: row['7 Day Reject %'] || row.Reject7Day || '0',
            Uptime7Day: row['7 Day Uptime %'] || row.Uptime || '100',
            LastPM: row['Last PM Date'] || row['Last Service Date'] || '',
            Phone: row['Store Phone Number'] || row.Phone || '',
            Latitude: row.Latitude || '',
            Longitude: row.Longitude || ''
        }));
        return true;
    }

    // ===== FILTERS & SORT =====
    function filterData() {
        let f = [...allData];
        let region = document.getElementById('regionFilter')?.value || 'all';
        if (region !== 'all') f = f.filter(r => getRegion(r) === region);
        let status = document.getElementById('statusFilter')?.value || 'all';
        if (status !== 'all') f = f.filter(r => getStatus(r).toLowerCase() === status);
        let search = document.getElementById('searchInput')?.value.toLowerCase() || '';
        if (search) f = f.filter(r =>
            (r.Store || '').toLowerCase().includes(search) ||
            (r.City || '').toLowerCase().includes(search) ||
            (r.Address || '').toLowerCase().includes(search)
        );
        return f;
    }

    function sortData(d) {
        return [...d].sort((a, b) => {
            let va = calcLoss(a), vb = calcLoss(b);
            return currentSort.direction === 'desc' ? vb - va : va - vb;
        });
    }

    // ===== RENDER =====
    function renderAll() {
        if (!allData.length) return;
        let f = filterData();
        f = sortData(f);

        const total = f.length;
        const crit = f.filter(r => getStatus(r) === 'Critical').length;
        const warn = f.filter(r => getStatus(r) === 'Warning').length;
        const tLoss = f.reduce((s, r) => s + calcLoss(r), 0);

        document.getElementById('kpiTotal').textContent = total;
        document.getElementById('kpiCritical').textContent = crit;
        document.getElementById('kpiWarning').textContent = warn;
        document.getElementById('kpiLoss').textContent = '$' + tLoss.toFixed(0);

        const tbody = document.getElementById('tableBody');
        if (!f.length) { tbody.innerHTML = '<tr><td colspan="12">No assets found</td></tr>'; return; }

        tbody.innerHTML = f.map(r => {
            const name = r.Store || '—';
            const phone = getPhoneNumber(r);
            const callBtn = phone ? `<button class="call-btn" style="background:#e8edf5;border:none;padding:4px 10px;border-radius:30px;cursor:pointer;" onclick="window.location.href='tel:${phone}'">📞</button>` : '—';
            const loss = calcLoss(r);
            const reject = getReject(r);
            const uptime = getUptime(r);
            const revenue = getEstRevenue(r);
            const status = getStatus(r);
            const serviceDays = getDaysSinceService(r);
            const rowClass = status === 'Critical' ? 'critical-row' : status === 'Warning' ? 'warning-row' : status === 'Offline' ? 'offline-row' : 'good-row';

            return `<tr class="${rowClass}">
                <td><strong>${escapeHtml(name)}</strong></td>
                <td>${escapeHtml(r.Address || '—')}</td>
                <td>${escapeHtml(r.City || '—')}</td>
                <td>${escapeHtml(getRegion(r))}</td>
                <td>${getStatusBadge(r)}</td>
                <td>${getVolume(r)}</td>
                <td style="color:${reject>=8?'#dc2626':reject>=4?'#f59e0b':'#10b981'}; font-weight:600;">${reject.toFixed(1)}%</td>
                <td style="color:${uptime<80?'#dc2626':uptime<95?'#f59e0b':'#10b981'}; font-weight:600;">${uptime.toFixed(1)}%</td>
                <td>$${revenue.toFixed(0)}</td>
                <td style="color:#dc2626; font-weight:700;">$${loss.toFixed(0)}</td>
                <td>${serviceDays !== null ? serviceDays + 'd' : '—'}</td>
                <td>${callBtn}</td>
            </tr>`;
        }).join('');

        updateMap(f);
        populateFilters();
    }

    // ===== MAP =====
    function updateMap(data) {
        if (map) map.remove();
        map = L.map('map').setView([56.1304, -106.3468], 4);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: 'OSM' }).addTo(map);
        let bounds = [];
        data.forEach(r => {
            let lat = parseFloat(r.Latitude);
            let lng = parseFloat(r.Longitude);
            if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                let s = getStatus(r);
                let color = s === 'Critical' ? '#dc2626' : s === 'Warning' ? '#f59e0b' : s === 'Offline' ? '#6b7280' : '#10b981';
                L.circleMarker([lat, lng], { radius: 9, fillColor: color, color: '#fff', weight: 2, opacity: 1 })
                    .addTo(map)
                    .bindPopup(`<b>${escapeHtml(r.Store)}</b><br>Loss: $${calcLoss(r).toFixed(0)}`);
                bounds.push([lat, lng]);
            }
        });
        if (bounds.length) map.fitBounds(bounds);
        else map.fitBounds([[42, -79], [50, -60]]);
        setTimeout(() => map.invalidateSize(), 100);
    }

    // ===== FILTERS SETUP =====
    function populateFilters() {
        if (!allData.length) return;
        const regions = [...new Set(allData.map(r => getRegion(r)))].filter(r => r && r !== 'Unknown');
        const sel = document.getElementById('regionFilter');
        const current = sel.value;
        sel.innerHTML = '<option value="all">All</option>' + regions.sort().map(p => `<option value="${p}">${p}</option>`).join('');
        if ([...sel.options].some(o => o.value === current)) sel.value = current;
    }

    // ===== SCREENSHOT & REPORT =====
    function takeScreenshot() {
        if (!allData.length) return showToast('No data');
        showToast('Capturing...');
        html2canvas(document.getElementById('dashboard')).then(canvas => {
            let link = document.createElement('a');
            link.download = 'dashboard_' + Date.now() + '.png';
            link.href = canvas.toDataURL();
            link.click();
            showToast('Screenshot saved');
        }).catch(() => showToast('Failed'));
    }

    function downloadReport() {
        if (!allData.length) return showToast('No data');
        showToast('Generating report...');
        html2canvas(document.getElementById('dashboard'), { scale: 2, backgroundColor: '#f0f4fb' }).then(canvas => {
            let link = document.createElement('a');
            link.download = 'fleet_report_' + Date.now() + '.png';
            link.href = canvas.toDataURL();
            link.click();
            showToast('Report saved');
        }).catch(() => showToast('Failed'));
    }

    // ============================================================
    // MODAL FUNCTIONS
    // ============================================================
    function openDemo() {
        document.getElementById('demoModal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeDemo() {
        document.getElementById('demoModal').style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================

    document.addEventListener('DOMContentLoaded', function() {

        // ---- Demo Modal ----
        document.getElementById('viewDemoBtn').addEventListener('click', openDemo);
        document.getElementById('demoModal').addEventListener('click', function(e) {
            if (e.target === this) closeDemo();
        });
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeDemo();
        });

        // ---- Upload buttons ----
        document.getElementById('uploadBtn').addEventListener('click', () => document.getElementById('csvFile').click());
        document.getElementById('uploadBtn2').addEventListener('click', () => document.getElementById('csvFile').click());

        // ---- File upload ----
        document.getElementById('csvFile').addEventListener('change', function(e) {
            if (!e.target.files || !e.target.files[0]) return;
            const file = e.target.files[0];
            document.getElementById('fileStatus').textContent = 'Loading: ' + file.name;
            if (!file.name.endsWith('.csv')) { showToast('Please upload a CSV file'); return; }
            const reader = new FileReader();
            reader.onload = function(ev) {
                if (parseCSV(ev.target.result)) {
                    document.getElementById('uploadCard').style.display = 'none';
                    document.getElementById('dashboard').style.display = 'block';
                    document.getElementById('dataTimestamp').textContent = '📅 ' + new Date().toLocaleString() + ' — ' + allData.length + ' assets';
                    populateFilters();
                    renderAll();
                    showToast('Loaded ' + allData.length + ' assets');
                } else showToast('Invalid CSV format');
            };
            reader.readAsText(file);
        });

        // ---- Load Sample Data ----
        document.getElementById('loadSampleBtn').addEventListener('click', function() {
            fetch('/load-sample')
                .then(response => response.text())
                .then(csvData => {
                    if (parseCSV(csvData)) {
                        document.getElementById('uploadCard').style.display = 'none';
                        document.getElementById('dashboard').style.display = 'block';
                        document.getElementById('dataTimestamp').textContent = '📅 ' + new Date().toLocaleString() + ' — Sample Data — ' + allData.length + ' assets';
                        populateFilters();
                        renderAll();
                        showToast('🚀 Sample data loaded!');
                    } else {
                        showToast('Failed to load sample data');
                    }
                })
                .catch(() => showToast('Error loading sample data'));
        });

        // ---- Reset ----
        document.getElementById('resetBtn').addEventListener('click', function() {
            document.getElementById('regionFilter').value = 'all';
            document.getElementById('statusFilter').value = 'all';
            document.getElementById('searchInput').value = '';
            renderAll();
        });

        // ---- Live filters ----
        document.getElementById('searchInput').addEventListener('input', renderAll);
        document.getElementById('regionFilter').addEventListener('change', renderAll);
        document.getElementById('statusFilter').addEventListener('change', renderAll);

        // ---- Screenshot & Report ----
        document.getElementById('screenshotBtn').addEventListener('click', takeScreenshot);
        document.getElementById('reportBtn').addEventListener('click', downloadReport);

        console.log('🚀 Fleet Intelligence Dashboard loaded');
    });
</script>
</body>
</html>
"""


@app.route('/')
def home():
    return HTML_TEMPLATE


@app.route('/load-sample')
def load_sample():
    return SAMPLE_CSV


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
