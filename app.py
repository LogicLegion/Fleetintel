from flask import Flask, render_template_string, request, redirect, url_for, jsonify, make_response, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from datetime import datetime

app = Flask(__name__)

# --- 1. SECURITY: No fallback secret key. It MUST be set in Render. ---
if not os.getenv('FLASK_SECRET_KEY'):
    raise ValueError("No FLASK_SECRET_KEY set for Flask application. Did you set environment variables?")
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# --- 2. DATABASE: Handle Render's postgres:// prefix (Heroku/Render compatibility) ---
db_url = os.getenv('DATABASE_URL', 'sqlite:///users.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'
login_manager.login_message_category = 'info'

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
# ANONYMIZED SAMPLE CSV DATA (Industrial/Universal Fleet)
# ============================================================
SAMPLE_CSV = """Asset ID,Location Name,Address,City,Region,1 Day TX,Fault Rate %,Uptime %,Last Service Date,Latitude,Longitude,Phone
TRK-104,Main Depot,100 Industrial Way,Edmonton,AB,14,1.2,98.5,2026-01-15,53.54,-113.49,780-555-0199
FORK-22,Warehouse B,450 Logistics Blvd,Calgary,AB,6,4.1,85.0,2026-02-01,51.04,-114.07,403-555-0153
EV-88,Downtown Hub,120 8th Ave SW,Calgary,AB,22,0.5,99.9,2026-01-28,51.04,-114.07,403-555-0188
TRK-209,North Route,8800 156 St NW,Edmonton,AB,9,9.0,72.5,2026-02-10,53.55,-113.62,780-555-0178
FORK-45,South Terminal,3040 50 Ave,Red Deer,AB,2,13.4,60.4,2026-02-05,52.26,-113.81,403-555-0144
EV-99,East Mall,250 East Rd,Edmonton,AB,16,2.6,99.5,2026-02-14,53.45,-113.41,780-555-0122
TRK-310,West Depot,1515 West Blvd,Vancouver,BC,11,1.0,91.9,2026-01-10,49.26,-123.11,604-555-0133
FORK-12,Port Facility,3050 Port Rd,Victoria,BC,5,5.7,78.3,2026-02-08,48.42,-123.36,250-555-0144
EV-12,Retail Park,363 Retail Ave,Mississauga,ON,19,0.2,99.8,2026-01-30,43.58,-79.64,905-555-0155
TRK-888,Central Hub,50 4th Avenue,Toronto,ON,8,7.4,69.5,2026-02-02,43.65,-79.38,416-555-0166"""

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
        body { font-family: 'Inter', sans-serif; background: #f0f4fb; color: #0a1a2b; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        .hero { padding: 60px 0 40px; text-align: center; }
        .hero h1 { font-size: 3.2rem; font-weight: 900; letter-spacing: -0.02em; line-height: 1.1; }
        .hero h1 span { color: #1e3a5f; }
        .hero p { font-size: 1.2rem; color: #475569; max-width: 600px; margin: 16px auto 32px; }
        .hero .btn-primary { background: #1e3a5f; color: white; padding: 14px 40px; border-radius: 60px; text-decoration: none; font-weight: 700; display: inline-block; transition: 0.2s; border: none; font-size: 1rem; cursor: pointer; }
        .hero .btn-primary:hover { background: #0f2b4a; transform: translateY(-2px); }
        .features { padding: 40px 0 60px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .feature-card { background: white; padding: 28px; border-radius: 20px; border: 1px solid #e9edf2; text-align: center; transition: 0.2s; }
        .feature-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px -8px rgba(0,0,0,0.06); }
        .feature-card .icon { font-size: 2.4rem; margin-bottom: 12px; }
        .feature-card h3 { font-weight: 700; margin-bottom: 8px; }
        .feature-card p { font-size: 0.95rem; color: #64748b; }
        .preview { background: white; border-radius: 24px; padding: 24px; border: 1px solid #e9edf2; margin-bottom: 40px; box-shadow: 0 8px 24px rgba(0,0,0,0.04); }
        .preview img { width: 100%; border-radius: 16px; border: 1px solid #e9edf2; }
        .preview .caption { text-align: center; padding: 12px 0 4px; color: #64748b; font-size: 0.9rem; }
        .pricing { text-align: center; padding: 40px 0 60px; }
        .pricing h2 { font-size: 2.2rem; font-weight: 800; }
        .pricing .sub { color: #64748b; margin-bottom: 32px; }
        .pricing-card { max-width: 400px; margin: 0 auto; background: white; border-radius: 24px; padding: 32px; border: 1px solid #e9edf2; box-shadow: 0 8px 24px rgba(0,0,0,0.04); }
        .pricing-card .price { font-size: 3rem; font-weight: 900; color: #0a1a2b; }
        .pricing-card .price span { font-size: 1rem; font-weight: 400; color: #64748b; }
        .pricing-card ul { list-style: none; text-align: left; margin: 24px 0; }
        .pricing-card ul li { padding: 8px 0; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; gap: 10px; }
        .pricing-card ul li::before { content: "✓"; color: #1e3a5f; font-weight: 700; }
        .pricing-card .btn-primary { background: #1e3a5f; color: white; padding: 14px 40px; border-radius: 60px; text-decoration: none; font-weight: 700; display: inline-block; transition: 0.2s; border: none; font-size: 1rem; cursor: pointer; width: 100%; }
        .pricing-card .btn-primary:hover { background: #0f2b4a; }
        .footer { text-align: center; padding: 32px 0; border-top: 1px solid #e9edf2; color: #94a3b8; font-size: 0.9rem; }
        .footer a { color: #1e3a5f; text-decoration: none; }
        @media (max-width: 768px) { .hero h1 { font-size: 2.2rem; } .features { grid-template-columns: 1fr; } .pricing-card { margin: 0 16px; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>See exactly which machines are <span>costing you money</span></h1>
            <p>Upload your fleet data and get a live dashboard with maps, filters, and real-time loss metrics. Stop guessing — start fixing.</p>
            <a href="{{ url_for('register') }}" class="btn-primary">Try It Free — 14-Day Trial</a>
            <p style="margin-top:12px; font-size:0.85rem; color:#94a3b8;">No credit card required</p>
        </div>

        <div class="preview">
            <img src="https://raw.githubusercontent.com/LogicLegion/Fleetintel/main/Fleetintel0.png" alt="FleetIntel Dashboard Preview">
            <div class="caption">📊 Live dashboard with KPIs, table, and asset map</div>
        </div>
        <div class="preview">
            <img src="https://raw.githubusercontent.com/LogicLegion/Fleetintel/main/Fleetintel1.png" alt="FleetIntel Dashboard Map View">
            <div class="caption">🗺️ Interactive map with color-coded asset status</div>
        </div>

        <div class="features">
            <div class="feature-card"><div class="icon">📊</div><h3>12 Key Metrics</h3><p>Volume, fault rate, uptime, daily loss, service days — all in one view.</p></div>
            <div class="feature-card"><div class="icon">🗺️</div><h3>Live Map</h3><p>See all your assets on a map. Color-coded by status.</p></div>
            <div class="feature-card"><div class="icon">🔍</div><h3>Filters &amp; Search</h3><p>Find what you need in seconds with region, status, and search filters.</p></div>
            <div class="feature-card"><div class="icon">💰</div><h3>Daily Loss Calculator</h3><p>See exactly how much each machine is losing from faults and downtime.</p></div>
            <div class="feature-card"><div class="icon">📞</div><h3>One-Click Call</h3><p>Call your technician directly from the dashboard.</p></div>
            <div class="feature-card"><div class="icon">📸</div><h3>Export Reports</h3><p>Download screenshots or full reports to share with your team.</p></div>
        </div>

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

        <div class="footer">
            <p>&copy; 2026 FleetIntel. Built with ❤️ in Canada.</p>
            <p>
                <a href="mailto:jjaaluk@gmail.com">✉️ Contact</a> ·
                <a href="https://fleetintel.onrender.com" target="_blank">Live Demo</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

# ============================================================
# HTML TEMPLATES (LOGIN, REGISTER)
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
        body { font-family: 'Inter', sans-serif; min-height: 100vh; display: flex; justify-content: center; align-items: center; background: #f0f4fb; padding: 20px; }
        .login-card { background: white; border-radius: 32px; padding: 48px 40px; max-width: 420px; width: 100%; box-shadow: 0 20px 45px -12px rgba(0,0,0,0.08); border: 1px solid #e9edf2; text-align: center; }
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
        .info { color: #1e3a5f; font-size: 14px; margin-bottom: 12px; background: #eff6ff; padding: 8px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>📊 <span>FleetIntel</span></h1>
        <p class="sub">Sign in to your account</p>
        {% for msg in get_flashed_messages() %}<div class="info">{{ msg }}</div>{% endfor %}
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username or Email" required autocomplete="username">
            <input type="password" name="password" placeholder="Password" required autocomplete="current-password">
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
        body { font-family: 'Inter', sans-serif; min-height: 100vh; display: flex; justify-content: center; align-items: center; background: #f0f4fb; padding: 20px; }
        .register-card { background: white; border-radius: 32px; padding: 48px 40px; max-width: 420px; width: 100%; box-shadow: 0 20px 45px -12px rgba(0,0,0,0.08); border: 1px solid #e9edf2; text-align: center; }
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
            <input type="text" name="username" placeholder="Username" required autocomplete="username">
            <input type="email" name="email" placeholder="Email" required autocomplete="email">
            <input type="password" name="password" placeholder="Password" required autocomplete="new-password" minlength="6">
            <button type="submit">Create Account</button>
        </form>
        <p class="footer-text">Already have an account? <a href="{{ url_for('login') }}">Sign In</a></p>
    </div>
</body>
</html>
"""

# ============================================================
# DASHBOARD TEMPLATE
# ⚠️  PASTE YOUR ORIGINAL DASHBOARD_TEMPLATE STRING HERE ⚠️
# ============================================================
# DASHBOARD_TEMPLATE = """
# ... your original dashboard HTML ...
# """


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template_string(LANDING_TEMPLATE)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if not identifier or not password:
            return render_template_string(LOGIN_TEMPLATE, error="Please enter both username/email and password")

        # Accept username OR email, case-insensitive
        user = User.query.filter(
            (db.func.lower(User.username) == identifier.lower()) |
            (db.func.lower(User.email) == identifier.lower())
        ).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            # Prevent open-redirect: only allow relative paths
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))

        return render_template_string(LOGIN_TEMPLATE, error="Invalid username, email, or password")

    return render_template_string(LOGIN_TEMPLATE, error=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if not username or not email or not password:
            return render_template_string(REGISTER_TEMPLATE, error="All fields are required")
        if len(password) < 6:
            return render_template_string(REGISTER_TEMPLATE, error="Password must be at least 6 characters")

        # Case-insensitive duplicate checks
        if User.query.filter(db.func.lower(User.username) == username.lower()).first():
            return render_template_string(REGISTER_TEMPLATE, error="Username already taken")
        if User.query.filter(db.func.lower(User.email) == email).first():
            return render_template_string(REGISTER_TEMPLATE, error="Email already registered")

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))

    return render_template_string(REGISTER_TEMPLATE, error=None)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/load-sample')
@login_required
def load_sample():
    response = make_response(SAMPLE_CSV)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'inline; filename=sample_fleet.csv'
    return response


@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'bot_name': BOT_NAME})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
