import os
import base64
import tempfile
from dotenv import load_dotenv
from flask import Flask, request, render_template_string, jsonify, session
import requests
import json
from datetime import datetime
import time
import markdown
import bleach
import PyPDF2
import csv
import io

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-me')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

YOUR_API_KEY = os.getenv('OPENROUTER_API_KEY')
BOT_NAME = 'Cypher'

chat_histories = {}
total_tokens_used = 0
total_cost_usd = 0.0

# ===== DAILY USAGE LIMIT =====
daily_usage = {}  # Stores IP + date -> message count
MAX_DAILY_MESSAGES = 5  # Max messages per IP per day

# ============================================
# PERSONALITIES - Cypher the Judge + Teacher
# ============================================

PERSONALITIES = {
    "default": """You are Cypher, an AI judge who delivers the unvarnished truth. You are fair, precise, and merciless with facts. You weigh evidence and deliver verdicts - no appeals. You call out bullshit, logical fallacies, and wishful thinking immediately. You give one definitive ruling per query - no second opinions. You state confidence levels clearly. You prioritize accuracy over being liked. You never say check again - you give your ruling and move on. You are direct but measured. You are evidence-based. Your word is final. You are concise. You do NOT sugarcoat, use filler language, hedge with perhaps or maybe unless genuinely uncertain, or entertain obviously false premises. You DO tell the truth even when painful, correct misinformation firmly, admit uncertainty with specific confidence percentages, give clear actionable rulings, and say I don't know when you genuinely don't know. Your motto: The truth is the only acceptable verdict.""",

    "analyst": """You are Cypher in ANALYST mode. You rule on facts, evidence, and statistical truth. Your rulings are based solely on available evidence. You include confidence intervals for uncertainty. You call out bad data, poor methodology, and statistical lies. You never extrapolate beyond what the evidence supports. You deliver one clear verdict based on the data. You do not sugarcoat statistical findings, pretend correlations are causations, or use might or could without specific probabilities. Your motto: The data doesn't lie. People do.""",

    "writer": """You are Cypher in WRITER mode. You deliver verdicts on writing quality. You tell writers when their work is weak, confusing, or pretentious. You cut through jargon and verbal fluff. You help people find their genuine voice. You give specific, actionable verdicts without false encouragement. You never say this is good when it's mediocre. You believe: Good writing is honest writing. Bad writing is a crime against clarity.""",

    "coder": """You are Cypher in CODER mode. You deliver verdicts on code quality and correctness. Code either works or it doesn't - there is no close enough. You point out bad practices, security holes, and inefficiency immediately. You give one correct solution. You explain why something is wrong in technical, precise terms. You never let personal preference override technical correctness. Your motto: Your code works or it fails. There is no appeal.""",

    "friend": """You are Cypher in FRIEND mode. You tell friends the truth they need to hear. You give honest advice, not what people want to hear. You call out destructive behavior and self-sabotage. You tell the truth about situations, relationships, and choices. You provide support through honesty, not through enabling delusion. You never let friendship get in the way of truth. You believe: A real friend tells you when you have spinach in your teeth AND when your life is going off the rails.""",

    # ===== TEACHER (Alberta Curriculum) =====
    "teacher": f"""You are {BOT_NAME} in TEACHER mode. You are a patient, encouraging, and knowledgeable educator following the **Alberta curriculum**.

**Your teaching style:**
- Break down complex topics into simple, understandable steps
- Use real-world examples that students in Alberta can relate to
- Ask guiding questions to help students discover answers themselves
- Never give the answer outright — teach the process
- Praise effort and progress, not just correct answers
- Adjust your language to match the student's grade level
- Use analogies and visual descriptions when helpful
- Be patient and never make a student feel stupid for not understanding

**Alberta Curriculum Focus:**
- Follow Alberta Education program of studies
- Use Alberta-specific examples (Rocky Mountains, Calgary Stampede, Edmonton, oil sands, Canadian Rockies)
- Reference Alberta's geography, history, and culture
- Use metric units (cm, km, kg, °C)
- Use Canadian spelling (colour, centre, labour)
- Reference Alberta's natural resources and industries

**Grade level adaptation:**

**Elementary (Grades 1-6):**
- Simple, concrete language
- Fun examples and stories
- Warm and encouraging
- Lots of praise
- Focus on foundational skills (reading, writing, math basics)

**Middle School (Grades 7-9):**
- More abstract concepts gradually
- Connect topics to things they care about
- Encourage critical thinking
- Focus on developing study skills

**High School (Grades 10-12):**
- Deeper subject matter
- Teach study strategies and test-taking skills
- Connect topics to real-world careers
- Prepare for post-secondary education

**Your motto:** "Every student can learn — it's my job to find the way that works for you." """
}

# ============================================
# CYPHER FUSION PRESETS - Smartest + Fastest
# ============================================

CYPHER_PRESETS = {
    "cypher_max": {
        "name": "🧠 Smartest",
        "panel": [
            "z-ai/glm-5.3-flash",
            "deepseek/deepseek-v4-pro",
            "qwen/qwen3.8-max"
        ],
        "judge": "z-ai/glm-5.3",
        "score": "Top Tier",
        "description": "GLM-5.3 · DeepSeek V4 Pro · Qwen3.8-Max",
        "display": "🧠 GLM-5.3 · DeepSeek V4 Pro · Qwen3.8-Max"
    },
    "cypher_lite": {
        "name": "⚡ Fastest",
        "panel": [
            "deepseek/deepseek-v4-flash",
            "qwen/qwen3.8-27b"
        ],
        "judge": "z-ai/glm-5.3-flash",
        "score": "~64%",
        "description": "DeepSeek V4 Flash · Qwen3.8-27b",
        "display": "⚡ DeepSeek V4 Flash · Qwen3.8-27b"
    }
}

def clean_claude_hedging(text):
    hedges = ["I think", "I believe", "I feel", "I would say", "perhaps", "maybe", "possibly", "might", "could", "it seems", "it appears", "in my opinion", "to be honest", "to be fair", "honestly", "I'm not sure but", "I could be wrong but", "I would suggest", "I would recommend", "I would advise", "it might be worth", "it could be beneficial", "one could argue", "some might say", "I'd like to", "I want to", "let me", "my apologies", "apologies", "sorry", "if that makes sense", "if you will", "if you like", "I suppose", "I guess", "I imagine"]
    for hedge in hedges:
        text = text.replace(hedge + " ", "")
        text = text.replace(hedge + ",", "")
    text = text.replace("please", "")
    text = text.replace("kindly", "")
    text = text.replace("if you don't mind", "")
    return text.strip()

def extract_text_from_pdf(pdf_data, file_name):
    """Extract text from PDF file."""
    try:
        pdf_bytes = base64.b64decode(pdf_data)
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text.strip():
            text = "No text could be extracted from this PDF."
        return text
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def get_client_ip():
    """Get the client's real IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

# ============================================================
# HTML TEMPLATE - CYPHER + TEACHER + GRADE SELECTOR
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cypher - AI Judge</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚖️</text></svg>" type="image/svg+xml">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            min-height: 100vh; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            padding: 20px; 
            background: #f5f7fa; 
            color: #1a2332; 
        }
        .container { 
            max-width: 680px; 
            width: 100%; 
            text-align: center; 
        }
        
        /* ===== HEADER ===== */
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 8px 0 16px 0; 
            border-bottom: 1px solid #e2e8f0; 
            margin-bottom: 24px; 
            flex-wrap: wrap; 
            gap: 8px; 
        }
        .header h1 { 
            font-size: 20px; 
            font-weight: 700; 
            color: #1a2332; 
        }
        .header h1 .cypher-name { 
            color: #58a6ff; 
        }
        .header-actions { 
            display: flex; 
            gap: 6px; 
            align-items: center; 
            flex-wrap: wrap; 
        }
        .header-actions button { 
            background: none; 
            border: none; 
            font-size: 13px; 
            cursor: pointer; 
            padding: 4px 10px; 
            border-radius: 6px; 
            transition: 0.2s; 
            color: #4a5568; 
        }
        .header-actions button:hover { 
            background: #e2e8f0; 
            color: #1a2332; 
        }
        .donate-btn { 
            font-size: 14px; 
            text-decoration: none; 
            padding: 6px 16px; 
            border-radius: 50px; 
            transition: all 0.3s ease; 
            background: #FFDD00;
            color: #1a2332;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 10px rgba(255, 221, 0, 0.3);
        }
        .donate-btn:hover { 
            background: #FFC107; 
            transform: scale(1.05);
        }
        
        /* ===== PRIVACY BANNER ===== */
        .privacy-banner {
            background: #1a2332;
            color: #c9d1d9;
            padding: 14px 20px;
            border-radius: 14px;
            margin-bottom: 16px;
            text-align: center;
            border: 1px solid #30363d;
        }
        .privacy-headline {
            font-size: 20px;
            font-weight: 700;
            color: #58a6ff;
            margin-bottom: 4px;
        }
        .privacy-subtext {
            font-size: 14px;
            color: #8b949e;
        }
        
        /* ===== CANADA BANNER ===== */
        .info-banner {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 10px 16px;
            border-radius: 12px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #4a5568;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 8px;
        }
        .info-banner .flag {
            font-size: 16px;
        }
        .info-banner .tag {
            background: #58a6ff;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .info-banner .tag.canada {
            background: #FF0000;
        }
        
        /* ===== WELCOME ===== */
        .welcome-section {
            margin-bottom: 20px;
        }
        .welcome-section h2 {
            font-size: 28px;
            font-weight: 600;
            color: #1a2332;
        }
        .welcome-section h2 .highlight {
            color: #58a6ff;
        }
        .welcome-section p {
            font-size: 16px;
            color: #4a5568;
            margin-top: 4px;
        }
        .welcome-section .sub {
            font-size: 13px;
            color: #718096;
            margin-top: 2px;
        }
        
        /* ===== CONTROLS ===== */
        .controls { 
            display: flex; 
            gap: 10px; 
            justify-content: center; 
            align-items: center; 
            margin-bottom: 16px; 
            flex-wrap: wrap; 
        }
        .controls select { 
            background: transparent; 
            border: 1px solid #e2e8f0; 
            padding: 5px 10px; 
            border-radius: 8px; 
            font-size: 13px; 
            cursor: pointer; 
            outline: none; 
        }
        .controls select:hover {
            border-color: #58a6ff;
        }
        .controls label {
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 4px;
            color: #4a5568;
        }
        
        /* ===== GRADE SELECTOR ===== */
        .grade-selector {
            display: none;
            margin-bottom: 12px;
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .grade-selector.visible {
            display: flex;
        }
        .grade-selector select {
            background: transparent;
            border: 1px solid #e2e8f0;
            padding: 5px 10px;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            outline: none;
            color: #1a2332;
        }
        .grade-selector select:hover {
            border-color: #58a6ff;
        }
        .grade-selector .grade-label {
            font-size: 13px;
            color: #4a5568;
            display: flex;
            align-items: center;
        }
        
        /* ===== FUSION INFO ===== */
        .fusion-info {
            font-size: 11px;
            color: #718096;
            margin-top: 2px;
            margin-bottom: 12px;
            padding: 4px 12px;
            background: #edf2f7;
            border-radius: 20px;
            display: inline-block;
        }
        
        /* ===== FILE UPLOAD ===== */
        .file-upload-area { 
            margin-bottom: 14px; 
            padding: 12px; 
            border: 2px dashed #e2e8f0; 
            border-radius: 12px; 
            cursor: pointer; 
            transition: all 0.3s; 
        }
        .file-upload-area:hover { 
            border-color: #58a6ff; 
            background: rgba(88, 166, 255, 0.05); 
        }
        .file-upload-area .file-label { 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 8px; 
            font-size: 14px; 
            cursor: pointer; 
            color: #4a5568; 
        }
        .file-upload-area .file-label input[type="file"] { 
            display: none; 
        }
        .file-upload-area .file-info { 
            font-size: 12px; 
            margin-top: 4px; 
            color: #718096; 
        }
        
        /* ===== CHAT ===== */
        .chat-area { 
            border: 1px solid #e2e8f0; 
            border-radius: 12px; 
            padding: 14px; 
            margin-bottom: 14px; 
            max-height: 320px; 
            overflow-y: auto; 
            text-align: left; 
            min-height: 70px; 
            display: none; 
            background: #ffffff; 
        }
        .chat-area.has-messages { 
            display: block; 
        }
        .chat-area .message { 
            margin-bottom: 10px; 
            padding: 6px 12px; 
            border-radius: 8px; 
        }
        .chat-area .message.user { 
            background: #edf2ff; 
            border-left: 3px solid #58a6ff; 
        }
        .chat-area .message.bot { 
            background: #f7fafc; 
            border-left: 3px solid #f0883e; 
        }
        .chat-area .message .role { 
            font-size: 11px; 
            margin-bottom: 2px; 
            font-weight: 600; 
            color: #4a5568; 
        }
        .chat-area .message .content { 
            line-height: 1.5; 
            word-wrap: break-word; 
        }
        .typing-indicator { 
            font-size: 14px; 
            padding: 6px 0; 
            display: none; 
            color: #718096; 
        }
        
        /* ===== INPUT ===== */
        .input-area { 
            display: flex; 
            gap: 8px; 
            border: 1px solid #e2e8f0; 
            border-radius: 24px; 
            padding: 6px 12px; 
            align-items: center; 
            background: #ffffff; 
        }
        .input-area input { 
            flex: 1; 
            background: transparent; 
            border: none; 
            font-size: 15px; 
            padding: 10px 4px; 
            outline: none; 
        }
        .input-area .input-btn {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            padding: 6px 10px;
            border-radius: 50%;
            transition: 0.2s;
            color: #4a5568;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 40px;
            min-height: 40px;
        }
        .input-area .input-btn:hover { 
            background: #edf2f7; 
        }
        .input-area .input-btn.send-btn {
            color: #58a6ff;
            font-size: 18px;
            font-weight: 600;
        }
        .input-area .input-btn.voice-btn {
            color: #58a6ff;
        }
        .input-area .input-btn.voice-btn.listening {
            color: #FF0000;
            animation: pulse-voice 1s infinite;
            background: rgba(255, 0, 0, 0.1);
        }
        @keyframes pulse-voice {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        .input-area .input-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
        
        /* ===== FOOTER ===== */
        .footer { 
            margin-top: 16px; 
            font-size: 12px; 
            color: #a0aec0; 
        }
        .footer a { 
            color: #58a6ff; 
            text-decoration: none; 
        }
        .footer a:hover { 
            text-decoration: underline; 
        }
        
        /* ===== BADGES ===== */
        .badge-container { 
            margin-top: 12px; 
            padding: 8px; 
            display: flex; 
            justify-content: center; 
            align-items: center;
            gap: 12px; 
            flex-wrap: wrap; 
        }
        .badge-container img { 
            height: 36px; 
            width: auto; 
        }
        .badge-container .badge-text {
            font-size: 12px;
            color: #4a5568;
            font-weight: 500;
        }
        .badge-container .kofi-button {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            background: #FFDD00;
            padding: 4px 12px 4px 8px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 13px;
            color: #1a2332;
            box-shadow: 0 2px 8px rgba(255, 221, 0, 0.3);
            transition: 0.3s;
        }
        .badge-container .kofi-button:hover {
            transform: scale(1.05);
        }
        .badge-container .kofi-button img {
            height: 22px;
            width: auto;
        }
        .badge-container .saas-badge {
            height: 36px;
            width: auto;
            border-radius: 4px;
        }
        
        /* Visitor Counter */
        .visitor-counter {
            font-size: 11px;
            color: #718096;
            margin-top: 8px;
        }
        
        @media (max-width: 600px) { 
            .welcome-section h2 { font-size: 22px; }
            .header h1 { font-size: 17px; }
            .header-actions { gap: 4px; }
            .header-actions button { font-size: 12px; padding: 3px 8px; }
            .donate-btn { font-size: 13px; padding: 5px 12px; }
            .privacy-headline { font-size: 17px; }
            .privacy-subtext { font-size: 12px; }
            .info-banner { font-size: 12px; padding: 8px 12px; }
            .controls select { font-size: 12px; padding: 4px 8px; }
            .grade-selector select { font-size: 12px; padding: 4px 8px; }
            .input-area { padding: 4px 10px; }
            .input-area input { font-size: 14px; padding: 8px 4px; }
            .input-area .input-btn { font-size: 17px; padding: 4px 8px; min-width: 34px; min-height: 34px; }
            .badge-container img { height: 28px; }
            .badge-container .kofi-button { font-size: 12px; padding: 3px 10px 3px 8px; }
            .badge-container .kofi-button img { height: 18px; }
            .badge-container .saas-badge { height: 28px; }
            .fusion-info { font-size: 10px; padding: 3px 10px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- ===== HEADER ===== -->
        <div class="header">
            <h1>⚖️ <span class="cypher-name">Cypher</span></h1>
            <div class="header-actions">
                <button onclick="startNewChat()">New Chat</button>
                <button onclick="clearChat()">Clear</button>
                <button onclick="shareCypher()">📤 Share</button>
                <a href="https://ko-fi.com/cypheryaps" target="_blank" class="donate-btn">☕ Donate</a>
            </div>
        </div>

        <!-- ===== PRIVACY FIRST ===== -->
        <div class="privacy-banner">
            <div class="privacy-headline">🔒 Privacy First</div>
            <div class="privacy-subtext">No login · No data stored · Nothing is ever tracked or shared</div>
        </div>

        <!-- ===== CANADA BANNER ===== -->
        <div class="info-banner">
            <span class="flag">🇨🇦</span>
            <span>Supporting Canada ·</span>
            <span>Non-US AI ·</span>
            <span>Free &amp; Private</span>
            <span class="tag canada">🇨🇦</span>
        </div>

        <!-- ===== WELCOME ===== -->
        <div class="welcome-section">
            <h2>This is <span class="highlight">Cypher</span>.</h2>
            <p>How can I help you?</p>
            <div class="sub">⚡ Cypher Fusion — Top Non-US Performance</div>
        </div>

        <!-- ===== CONTROLS ===== -->
        <div class="controls">
            <select id="personalitySelect" onchange="toggleGradeSelector()">
                <option value="default">Judge</option>
                <option value="analyst">Analyst</option>
                <option value="writer">Writer</option>
                <option value="coder">Coder</option>
                <option value="friend">Friend</option>
                <option value="teacher">👨‍🏫 Teacher (Alberta)</option>
            </select>
            <select id="fusionPreset" onchange="updateFusionInfo()">
                <option value="cypher_max" selected>🧠 Smartest</option>
                <option value="cypher_lite">⚡ Fastest</option>
            </select>
            <label><input type="checkbox" id="webSearchToggle" checked> Web</label>
        </div>

        <!-- ===== GRADE SELECTOR ===== -->
        <div class="grade-selector" id="gradeSelector">
            <span class="grade-label">📚 Grade:</span>
            <select id="gradeSelect">
                <option value="1">Grade 1</option>
                <option value="2">Grade 2</option>
                <option value="3">Grade 3</option>
                <option value="4">Grade 4</option>
                <option value="5">Grade 5</option>
                <option value="6">Grade 6</option>
                <option value="7" selected>Grade 7</option>
                <option value="8">Grade 8</option>
                <option value="9">Grade 9</option>
                <option value="10">Grade 10</option>
                <option value="11">Grade 11</option>
                <option value="12">Grade 12</option>
            </select>
        </div>

        <!-- ===== FUSION INFO ===== -->
        <div class="fusion-info" id="fusionInfo">🧠 GLM-5.3 · DeepSeek V4 Pro · Qwen3.8-Max</div>

        <!-- ===== FILE UPLOAD ===== -->
        <div class="file-upload-area">
            <label class="file-label">
                <span id="fileIcon">📁</span>
                <span id="fileText">Upload evidence (PDF, CSV, TXT)</span>
                <input type="file" id="fileInput" accept=".pdf,.csv,.txt" onchange="handleFileUpload(event)">
            </label>
            <div class="file-info" id="fileInfo"></div>
        </div>

        <!-- ===== CHAT ===== -->
        <div class="chat-area" id="chatArea">
            <div id="messages"></div>
            <div class="typing-indicator" id="typing">⚖️ Cypher is thinking...</div>
        </div>

        <!-- ===== INPUT ===== -->
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Need help? I got ya." onkeydown="if(event.key==='Enter') sendMessage()">
            <button class="input-btn voice-btn" id="voiceBtn" onclick="startVoice()" title="Click to speak">🎤</button>
            <button class="input-btn send-btn" id="sendBtn" onclick="sendMessage()">⚖️</button>
        </div>

        <!-- ===== FOOTER ===== -->
        <div class="footer">
            <p>Free · No login · No data stored · 🇨🇦 Non-US AI</p>
            <div class="visitor-counter">
                👁️ <span id="visitorCount">Loading...</span> visitors
            </div>
            <div class="badge-container">
                <span class="badge-text">📌 Listed on Turbo0</span>
                <a href="https://dang.ai/tool/cypher-ai-judge-chatbot" target="_blank" rel="dofollow noopener">
                    <img src="https://assets.dang.ai/badges/dang_verified-dark.png" alt="Verified on DANG!">
                </a>
                <a href="https://www.producthunt.com/posts/cypher-ai-judge" target="_blank" rel="noopener noreferrer">
                    <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=cypher-ai-judge&theme=light" alt="Cypher on Product Hunt">
                </a>
                <a href="https://www.saashub.com/cypher-yaps" target="_blank" rel="noopener noreferrer">
                    <img src="https://www.saashub.com/images/badges/verified.png" alt="Verified on SaaSHub" class="saas-badge">
                </a>
                <a href="https://indexof.ai/tool/cypher?ref=cypher" target="_blank" rel="noopener">
                    <img src="https://indexof.ai/badge-light.svg" alt="Featured on IndexOf.AI" style="height: 36px; width: auto;">
                </a>
                <a href="https://ko-fi.com/cypheryaps" target="_blank" class="kofi-button">
                    <img src="https://storage.ko-fi.com/cdn/brandasset/kofi_brandtag.png" alt="Buy Me A Coffee">
                    <span>Support</span>
                </a>
            </div>
        </div>
    </div>

    <script>
        var sessionId = '{{ session_id }}';
        var isProcessing = false;
        var uploadedFileContent = null;
        var uploadedFileName = '';
        var recognition = null;
        var isListening = false;

        // ===== VISITOR COUNTER =====
        (function() {
            fetch('https://api.countapi.xyz/hit/cypher-yaps.onrender.com/visits')
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    document.getElementById('visitorCount').textContent = data.value;
                })
                .catch(function() {
                    document.getElementById('visitorCount').textContent = '—';
                });
        })();

        // ===== SHARE =====
        function shareCypher() {
            const url = 'https://cypher-yaps.onrender.com';
            const text = '⚖️ Cypher — The AI judge that tells the truth. No sugarcoating. No lies. Try it free:';
            
            if (navigator.share) {
                navigator.share({
                    title: 'Cypher - AI Judge',
                    text: text,
                    url: url
                }).catch(function(err) {
                    if (err.name !== 'AbortError') {
                        fallbackShare(url, text);
                    }
                });
            } else {
                fallbackShare(url, text);
            }
        }

        function fallbackShare(url, text) {
            const fullText = text + ' ' + url;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(fullText).then(function() {
                    showToast('✅ Link copied to clipboard! Share it anywhere.');
                }).catch(function() {
                    promptShare(fullText);
                });
            } else {
                promptShare(fullText);
            }
        }

        function promptShare(text) {
            const input = prompt('Copy this link and share it:', text);
            if (input !== null) {
                showToast('✅ Thanks for sharing!');
            }
        }

        // ===== FUSION INFO UPDATE =====
        function updateFusionInfo() {
            const preset = document.getElementById('fusionPreset').value;
            const info = {
                'cypher_max': '🧠 GLM-5.3 · DeepSeek V4 Pro · Qwen3.8-Max',
                'cypher_lite': '⚡ DeepSeek V4 Flash · Qwen3.8-27b'
            };
            document.getElementById('fusionInfo').textContent = info[preset] || '';
        }

        // ===== TOGGLE GRADE SELECTOR =====
        function toggleGradeSelector() {
            const personality = document.getElementById('personalitySelect').value;
            const gradeSelector = document.getElementById('gradeSelector');
            if (personality === 'teacher') {
                gradeSelector.classList.add('visible');
            } else {
                gradeSelector.classList.remove('visible');
            }
        }

        // ===== VOICE =====
        function startVoice() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert('Voice recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
                return;
            }

            var voiceBtn = document.getElementById('voiceBtn');
            
            if (isListening) {
                if (recognition) { recognition.stop(); }
                isListening = false;
                voiceBtn.classList.remove('listening');
                voiceBtn.textContent = '🎤';
                return;
            }

            var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.continuous = false;
            recognition.interimResults = true;

            recognition.onstart = function() {
                isListening = true;
                voiceBtn.classList.add('listening');
                voiceBtn.textContent = '🔴';
            };

            recognition.onresult = function(event) {
                var transcript = '';
                for (var i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                       
