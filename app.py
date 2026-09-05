from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import base64
import io
import PyPDF2
import json
import time
from datetime import datetime
import markdown
import bleach
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'

YOUR_API_KEY = os.getenv('OPENROUTER_API_KEY')
BOT_NAME = 'FleetIntel'

# ===== USER MODEL =====
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== CREATE TABLES =====
with app.app_context():
    db.create_all()

# ============================================================
# SAMPLE CSV DATA
# ============================================================
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

# ============================================================
# LANDING PAGE TEMPLATE
# ============================================================
LANDING_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FleetIntel — Asset Intelligence Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #f0f4fb;
            color: #0a1a2b;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

        /* HERO */
        .hero {
            padding: 60px 0 40px;
            text-align: center;
        }
        .hero h1 {
            font-size: 3.2rem;
            font-weight: 900;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }
        .hero h1 span { color: #1e3a5f; }
        .hero p {
            font-size: 1.2rem;
            color: #475569;
            max-width: 600px;
            margin: 16px auto 32px;
        }
        .hero .btn-primary {
            background: #1e3a5f;
            color: white;
            padding: 14px 40px;
            border-radius: 60px;
            text-decoration: none;
            font-weight: 700;
            display: inline-block;
            transition: 0.2s;
            border: none;
            font-size: 1rem;
            cursor: pointer;
        }
        .hero .btn-primary:hover { background: #0f2b4a; transform: translateY(-2px); }

        /* FEATURES */
        .features {
            padding: 40px 0 60px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
        }
        .feature-card {
            background: white;
            padding: 28px;
            border-radius: 20px;
            border: 1px solid #e9edf2;
            text-align: center;
            transition: 0.2s;
        }
        .feature-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px -8px rgba(0,0,0,0.06); }
        .feature-card .icon { font-size: 2.4rem; margin-bottom: 12px; }
        .feature-card h3 { font-weight: 700; margin-bottom: 8px; }
        .feature-card p { font-size: 0.95rem; color: #64748b; }

        /* SCREENSHOT PREVIEW */
        .preview {
            background: white;
            border-radius: 24px;
            padding: 24px;
            border: 1px solid #e9edf2;
            margin-bottom: 40px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.04);
        }
        .preview img {
            width: 100%;
            border-radius: 16px;
            border: 1px solid #e9edf2;
        }
        .preview .caption {
            text-align: center;
            padding: 12px 0 4px;
            color: #64748b;
            font-size: 0.9rem;
        }

        /* PRICING */
        .pricing {
            text-align: center;
            padding: 40px 0 60px;
        }
        .pricing h2 { font-size: 2.2rem; font-weight: 800; }
        .pricing .sub { color: #64748b; margin-bottom: 32px; }
        .pricing-card {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            border-radius: 24px;
            padding: 32px;
            border: 1px solid #e9edf2;
            box-shadow: 0 8px 24px rgba(0,0,0,0.04);
        }
        .pricing-card .price { font-size: 3rem; font-weight: 900; color: #0a1a2b; }
        .pricing-card .price span { font-size: 1rem; font-weight: 400; color: #64748b; }
        .pricing-card ul {
            list-style: none;
            text-align: left;
            margin: 24px 0;
        }
        .pricing-card ul li {
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .pricing-card ul li::before { content: "✓"; color: #1e3a5f; font-weight: 700; }
        .pricing-card .btn-primary {
            background: #1e3a5f;
            color: white;
            padding: 14px 40px;
            border-radius: 60px;
            text-decoration: none;
            font-weight: 700;
            display: inline-block;
            transition: 0.2s;
            border: none;
            font-size: 1rem;
            cursor: pointer;
            width: 100%;
        }
        .pricing-card .btn-primary:hover { background: #0f2b4a; }

        /* FOOTER */
        .footer {
            text-align: center;
            padding: 32px 0;
            border-top: 1px solid #e9edf2;
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .footer a { color: #1e3a5f; text-decoration: none; }

        @media (max-width: 768px) {
            .hero h1 { font-size: 2.2rem; }
            .features { grid-template-columns: 1fr; }
            .pricing-card { margin: 0 16px; }
        }
    </style>
</head>
<body>
    <div class="container">

        <!-- HERO -->
        <div class="hero">
            <h1>See exactly which machines are <span>costing you money</span></h1>
            <p>Upload your fleet data and get a live dashboard with maps, filters, and real-time loss metrics. Stop guessing — start fixing.</p>
            <a href="{{ url_for('register') }}" class="btn-primary">Try It Free — 14-Day Trial</a>
            <p style="margin-top:12px; font-size:0.85rem; color:#94a3b8;">No credit card required</p>
        </div>

        <!-- SCREENSHOT PREVIEW -->
        <div class="preview">
            <img src="https://raw.githubusercontent.com/LogicLegion/Fleetintel/main/Fleetintel0.png" alt="FleetIntel Dashboard Preview">
            <div class="caption">📊 Live dashboard with KPIs, table, and asset map</div>
        </div>

        <!-- FEATURES -->
        <div class="features">
            <div class="feature-card">
                <div class="icon">📊</div>
                <h3>12 Key Metrics</h3>
                <p>Volume, reject rate, uptime, daily loss, service days — all in one view.</p>
            </div>
            <div class="feature-card">
                <div class="icon">🗺️</div>
                <h3>Live Map</h3>
                <p>See all your assets on a map. Color-coded by status.</p>
            </div>
            <div class="feature-card">
                <div class="icon">🔍</div>
                <h3>Filters &amp; Search</h3>
                <p>Find what you need in seconds with region, status, and search filters.</p>
            </div>
            <div class="feature-card">
                <div class="icon">💰</div>
                <h3>Daily Loss Calculator</h3>
                <p>See exactly how much each machine is losing from rejects and downtime.</p>
            </div>
            <div class="feature-card">
                <div class="icon">📞</div>
                <h3>One-Click Call</h3>
                <p>Call your technician directly from the dashboard.</p>
            </div>
            <div class="feature-card">
                <div class="icon">📸</div>
                <h3>Export Reports</h3>
                <p>Download screenshots or full reports to share with your team.</p>
            </div>
        </div>

        <!-- PRICING -->
        <div class="pricing">
            <h2>Simple, transparent pricing</h2>
            <p class="sub">No hidden fees. Cancel anytime.</p>
            <div class="pricing-card">
                <div class="price">$199 <span>/ month</span></div>
                <p style="color:#475569; margin: 8px 0 16px;">Per location · Unlimited users</p>
                <ul>
                    <li>Unlimited assets</li>
                    <li>Live dashboard with maps</li>
                    <li>Filters, search, and sorting</li>
                    <li>Export reports and screenshots</li>
                    <li>14-day free trial</li>
                    <li>No contract — cancel anytime</li>
                </ul>
                <a href="{{ url_for('register') }}" class="btn-primary">Start Free Trial</a>
            </div>
        </div>

        <!-- FOOTER -->
        <div class="footer">
            <p>&copy; 2026 FleetIntel. Built with ❤️ in Canada. <a href="mailto:your-email@example.com">Contact</a></p>
        </div>

    </div>
</body>
</html>
"""

# ============================================================
# HTML TEMPLATES (LOGIN, REGISTER, DASHBOARD)
# ============================================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FleetIntel — Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #f0f4fb;
            padding: 20px;
        }
        .login-card {
            background: white;
            border-radius: 32px;
            padding: 48px 40px;
            max-width: 420px;
            width: 100%;
            box-shadow: 0 20px 45px -12px rgba(0,0,0,0.08);
            border: 1px solid #e9edf2;
            text-align: center;
        }
        .login-card h1 { font-size: 28px; font-weight: 800; color: #0a1a2b; }
        .login-card h1 span { color: #1e3a5f; }
        .login-card .sub { color: #64748b; font-size: 14px; margin: 8px 0 24px 0; }
        .login-card input { width: 100%; padding: 14px 16px; border: 1px solid #e2e8f0; border-radius: 14px; font-size: 15px; margin-bottom: 12px; }
        .login-card input:focus { outline: none; border-color: #1e3a5f; box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1); }
        .login-card button { width: 100%; padding: 14px; background: #1e3a5f; color: white; border: none; border-radius: 14px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.2s; }
        .login-card button:hover { background: #0f2b4a; }
        .login-card .footer-text { margin-top: 16px; font-size: 14px; color: #64748b; }
        .login-card .footer-text a { color: #1e3a5f; font-weight: 600; text-decoration: none; }
        .login-card .footer-text a:hover { text-decoration: underline; }
        .error { color: #dc2626; font-size: 14px; margin-bottom: 12px; background: #fef2f2; padding: 8px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>📊 <span>FleetIntel</span></h1>
        <p class="sub">Sign in to your account</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
        <p class="footer-text">Don't have an account? <a href="{{ url_for('register') }}">Register</a></p>
    </div>
</body>
</html>
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FleetIntel — Register</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #f0f4fb;
            padding: 20px;
        }
        .register-card {
            background: white;
            border-radius: 32px;
            padding: 48px 40px;
            max-width: 420px;
            width: 100%;
            box-shadow: 0 20px 45px -12px rgba(0,0,0,0.08);
            border: 1px solid #e9edf2;
            text-align: center;
        }
        .register-card h1 { font-size: 28px; font-weight: 800; color: #0a1a2b; }
        .register-card h1 span { color: #1e3a5f; }
        .register-card .sub { color: #64748b; font-size: 14px; margin: 8px 0 24px 0; }
        .register-card input { width: 100%; padding: 14px 16px; border: 1px solid #e2e8f0; border-radius: 14px; font-size: 15px; margin-bottom: 12px; }
        .register-card input:focus { outline: none; border-color: #1e3a5f; box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1); }
        .register-card button { width: 100%; padding: 14px; background: #1e3a5f; color: white; border: none; border-radius: 14px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.2s; }
        .register-card button:hover { background: #0f2b4a; }
        .register-card .footer-text { margin-top: 16px; font-size: 14px; color: #64748b; }
        .register-card .footer-text a { color: #1e3a5f; font-weight: 600; text-decoration: none; }
        .register-card .footer-text a:hover { text-decoration: underline; }
        .error { color: #dc2626; font-size: 14px; margin-bottom: 12px; background: #fef2f2; padding: 8px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="register-card">
        <h1>📊 <span>FleetIntel</span></h1>
        <p class="sub">Create your account</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Create Account</button>
        </form>
        <p class="footer-text">Already have an account? <a href="{{ url_for('login') }}">Sign In</a></p>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
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
        .hero-btn.outline {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.3);
        }
        .hero-btn.outline:hover { background: rgba(255,255,255,0.1); }
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
        .kpi-value { font-size: 2.2rem; font-weight
