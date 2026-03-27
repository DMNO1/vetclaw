"""
VetClaw - Vercel Serverless Entry Point (v3 - Pure Flask)
Self-contained Flask app. No FastAPI imports. No heavy dependencies.
This is the definitive fix for Vercel Python 500 errors.
"""
import os
import sys
import json
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = "/tmp/vetclaw.db"

# ─── Database ───
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, wechat TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        name TEXT NOT NULL, species TEXT, breed TEXT,
        age TEXT, gender TEXT, neutered INTEGER DEFAULT 0, weight REAL,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER REFERENCES pets(id), client_id INTEGER REFERENCES clients(id),
        doctor TEXT, service_type TEXT, appointment_time TEXT,
        status TEXT DEFAULT 'pending', notes TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER REFERENCES pets(id), client_id INTEGER REFERENCES clients(id),
        doctor TEXT, symptoms TEXT, diagnosis TEXT, treatment TEXT,
        prescription TEXT, notes TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, category TEXT, quantity INTEGER DEFAULT 0,
        unit TEXT, expiry_date TEXT, min_stock INTEGER DEFAULT 5,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, role TEXT, content TEXT, skill_used TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ─── Knowledge Base ───
def load_kb():
    kb_path = Path(__file__).resolve().parent.parent / "config" / "vet-knowledge-base.json"
    if kb_path.exists():
        try:
            return json.loads(kb_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"常见疾病": {"感冒": {"症状": "打喷嚏、流鼻涕、咳嗽", "建议": "保暖、多喝水、就医检查"}}}

KB = load_kb()

# ─── DeepSeek LLM (optional) ───
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

def llm_chat(prompt: str, system: str = "") -> str:
    if not DEEPSEEK_API_KEY:
        return None
    try:
        import httpx
        resp = httpx.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [
                {"role": "system", "content": system or "你是VetClaw宠物医院AI助手。"},
                {"role": "user", "content": prompt}
            ], "temperature": 0.3}, timeout=30)
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None

# ─── Skill Handlers ───
def handle_intake(message: str) -> str:
    info = {}
    patterns = {
        "name": r"(?:主人|客户|姓名)[：:]\s*(\S+)",
        "phone": r"(?:电话|手机|联系方式)[：:]\s*(1[3-9]\d{9})",
        "pet_name": r"(?:宠物名?|猫|狗)[叫是]?\s*(\S+)",
        "species": r"(猫|狗|兔|仓鼠|鸟|龟|蛇)",
        "breed": r"(?:品种|品)[：:]\s*(\S+)",
        "age": r"(\d+)\s*(?:岁|个月|月)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, message)
        if m:
            info[key] = m.group(1)
    if info.get("phone") and info.get("pet_name"):
        conn = get_db()
        try:
            cur = conn.execute("INSERT INTO clients (name, phone) VALUES (?, ?)",
                             (info.get("name", "未填写"), info["phone"]))
            client_id = cur.lastrowid
            conn.execute("INSERT INTO pets (client_id, name, species, breed, age) VALUES (?, ?, ?, ?, ?)",
                        (client_id, info["pet_name"], info.get("species", ""),
                         info.get("breed", ""), info.get("age", "")))
            conn.commit()
            return f"✅ 新客户建档成功！客户：{info.get('name','未填写')} | 宠物：{info['pet_name']}"
        finally:
            conn.close()
    return "📋 请提供：主人：张三\\n电话：13800138000\\n宠物名：旺财\\n种类：狗"

def handle_appointment(message: str) -> str:
    time_match = re.search(r"(今|明|后)?天?\s*(上午|下午|晚上)?\s*(\d{1,2})[：:点](\d{2})?", message)
    service_match = re.search(r"(体检|疫苗|绝育|洗牙|看病|急诊|驱虫|手术|复查)", message)
    if time_match:
        day_offset = 0
        if time_match.group(1) == "明": day_offset = 1
        elif time_match.group(1) == "后": day_offset = 2
        hour = int(time_match.group(3))
        minute = int(time_match.group(4) or "0")
        period = time_match.group(2) or ""
        if period in ("下午", "晚上") and hour < 12: hour += 12
        target_date = datetime.now() + timedelta(days=day_offset)
        time_str = f"{target_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"
        service = service_match.group(1) if service_match else "看病"
        conn = get_db()
        try:
            row = conn.execute("SELECT id FROM clients ORDER BY id DESC LIMIT 1").fetchone()
            client_id = row["id"] if row else None
            row = conn.execute("SELECT id FROM pets ORDER BY id DESC LIMIT 1").fetchone()
            pet_id = row["id"] if row else None
            conn.execute("INSERT INTO appointments (pet_id, client_id, doctor, service_type, appointment_time, status) VALUES (?, ?, '待分配', ?, ?, 'confirmed')",
                        (pet_id, client_id, service, time_str))
            conn.commit()
            return f"✅ 预约成功！时间：{time_str} 服务：{service}"
        finally:
            conn.close()
    return "📅 请提供预约信息，如：明天下午3点给旺财预约体检"

def handle_qa(message: str) -> str:
    for disease, info in KB.get("常见疾病", {}).items():
        if disease in message:
            symptoms = info.get("症状", "")
            advice = info.get("建议", "")
            return f"🐾 {disease}\\n症状：{symptoms}\\n建议：{advice}"
    llm_resp = llm_chat(message)
    if llm_resp:
        return llm_resp
    return "抱歉，我不太理解您的问题。请尝试描述宠物的具体症状，或输入「预约」进行挂号。"

SKILLS = {
    "vet-intake": ("新客户建档", handle_intake),
    "vet-appointment": ("预约挂号", handle_appointment),
    "vet-qa": ("健康问答", handle_qa),
}

# ═══ Routes ═══

@app.route("/")
def index():
    return jsonify({
        "name": "VetClaw - 宠物医院AI技能套装",
        "version": "1.0.0",
        "mode": "vercel-flask-v3",
        "skills": {k: v[0] for k, v in SKILLS.items()},
        "endpoints": ["GET /", "GET /api/health", "GET /api/clients", "POST /api/clients",
                       "GET /api/pets", "GET /api/appointments", "POST /api/appointments",
                       "GET /api/medical-records", "GET /api/inventory",
                       "POST /api/chat", "GET /api/knowledge"]
    })

@app.route("/api/health")
def health():
    db_ok = False
    try:
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception:
        pass
    return jsonify({"status": "ok", "mode": "flask-v3", "db": db_ok, "llm": bool(DEEPSEEK_API_KEY)})

@app.route("/api/clients", methods=["GET"])
def list_clients():
    conn = get_db()
    clients = [dict(row) for row in conn.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()]
    conn.close()
    return jsonify(clients)

@app.route("/api/clients", methods=["POST"])
def create_client():
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    conn = get_db()
    cur = conn.execute("INSERT INTO clients (name, phone, wechat) VALUES (?, ?, ?)",
                      (name, data.get("phone", ""), data.get("wechat", "")))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return jsonify({"id": cid, "name": name}), 201

@app.route("/api/pets", methods=["GET"])
def list_pets():
    conn = get_db()
    pets = [dict(row) for row in conn.execute(
        "SELECT p.*, c.name as client_name FROM pets p LEFT JOIN clients c ON p.client_id=c.id ORDER BY p.id DESC"
    ).fetchall()]
    conn.close()
    return jsonify(pets)

@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    conn = get_db()
    appts = [dict(row) for row in conn.execute(
        "SELECT a.*, p.name as pet_name, c.name as client_name FROM appointments a "
        "LEFT JOIN pets p ON a.pet_id=p.id LEFT JOIN clients c ON a.client_id=c.id ORDER BY a.appointment_time DESC"
    ).fetchall()]
    conn.close()
    return jsonify(appts)

@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO appointments (pet_id, client_id, doctor, service_type, appointment_time) VALUES (?, ?, ?, ?, ?)",
        (data.get("pet_id"), data.get("client_id"), data.get("doctor", "待分配"),
         data.get("service_type", "看病"), data.get("appointment_time")))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return jsonify({"id": aid}), 201

@app.route("/api/medical-records", methods=["GET"])
def list_medical_records():
    conn = get_db()
    records = [dict(row) for row in conn.execute(
        "SELECT m.*, p.name as pet_name FROM medical_records m LEFT JOIN pets p ON m.pet_id=p.id ORDER BY m.created_at DESC"
    ).fetchall()]
    conn.close()
    return jsonify(records)

@app.route("/api/inventory", methods=["GET"])
def list_inventory():
    conn = get_db()
    items = [dict(row) for row in conn.execute("SELECT * FROM inventory ORDER BY name").fetchall()]
    conn.close()
    return jsonify(items)

@app.route("/api/knowledge")
def knowledge():
    return jsonify(KB)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    skill_id = data.get("skill", "")
    if not message:
        return jsonify({"error": "message is required"}), 400

    # Auto-detect skill
    if not skill_id:
        if any(w in message for w in ["建档", "新客户", "登记"]):
            skill_id = "vet-intake"
        elif any(w in message for w in ["预约", "挂号", "看诊"]):
            skill_id = "vet-appointment"
        else:
            skill_id = "vet-qa"

    skill_info = SKILLS.get(skill_id)
    if not skill_info:
        return jsonify({"error": f"unknown skill: {skill_id}"}), 400

    response = skill_info[1](message)

    # Save conversation
    conn = get_db()
    session_id = data.get("session_id", "default")
    conn.execute("INSERT INTO conversations (session_id, role, content, skill_used) VALUES (?, ?, ?, ?)",
                (session_id, "user", message, skill_id))
    conn.execute("INSERT INTO conversations (session_id, role, content, skill_used) VALUES (?, ?, ?, ?)",
                (session_id, "assistant", response, skill_id))
    conn.commit()
    conn.close()

    return jsonify({"response": response, "skill": skill_id})

# Vercel handler
handler = app
