"""
VetClaw - Vercel Serverless Entry Point (v2)
Attempts FastAPI+Mangum first, falls back to lightweight Flask if FastAPI init fails.
This resolves FUNCTION_INVOCATION_FAILED errors on Vercel Python runtime.
"""
import os
import sys
import logging
import pathlib
import json
import sqlite3

logger = logging.getLogger("vetclaw.vercel")

# Ensure project root is in path
project_root = str(pathlib.Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault("DATABASE_PATH", "/tmp/vetclaw.db")

# ─── Attempt 1: FastAPI + Mangum (preferred) ───
try:
    from main import app
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    logger.info("VetClaw FastAPI handler created successfully")
except Exception as fastapi_err:
    logger.warning(f"FastAPI init failed: {fastapi_err}, falling back to Flask")
    
    # ─── Attempt 2: Lightweight Flask fallback ───
    from flask import Flask, jsonify, request, render_template_string
    
    _app = Flask(__name__)
    DB_PATH = "/tmp/vetclaw.db"
    
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
            name TEXT NOT NULL, species TEXT, breed TEXT, age_years INTEGER, weight_kg REAL
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER REFERENCES pets(id), client_id INTEGER REFERENCES clients(id),
            date TEXT NOT NULL, time TEXT NOT NULL, reason TEXT, status TEXT DEFAULT 'pending'
        );
        """)
        conn.commit()
        conn.close()
    
    try:
        init_db()
    except Exception as e:
        logger.error(f"Flask fallback DB init failed: {e}")
    
    # Load knowledge base
    kb = {}
    kb_path = pathlib.Path(project_root) / "config" / "vet-knowledge-base.json"
    if kb_path.exists():
        try:
            kb = json.loads(kb_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    @_app.route("/")
    def index():
        return jsonify({
            "name": "VetClaw - 宠物医院AI技能套装",
            "version": "1.0.0",
            "mode": "flask-fallback",
            "fastapi_error": str(fastapi_err),
            "endpoints": [
                "GET /",
                "GET /api/health",
                "GET /api/knowledge",
                "GET /api/clients",
                "POST /api/clients",
                "GET /api/pets",
                "POST /api/appointments",
            ]
        })
    
    @_app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "mode": "flask-fallback", "db": os.path.exists(DB_PATH)})
    
    @_app.route("/api/knowledge")
    def knowledge():
        return jsonify(kb)
    
    @_app.route("/api/clients", methods=["GET"])
    def list_clients():
        conn = get_db()
        clients = [dict(row) for row in conn.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()]
        conn.close()
        return jsonify(clients)
    
    @_app.route("/api/clients", methods=["POST"])
    def create_client():
        data = request.get_json(force=True)
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "name is required"}), 400
        conn = get_db()
        cur = conn.execute("INSERT INTO clients (name, phone, wechat) VALUES (?, ?, ?)",
                          (name, data.get("phone", ""), data.get("wechat", "")))
        conn.commit()
        client_id = cur.lastrowid
        conn.close()
        return jsonify({"id": client_id, "name": name}), 201
    
    @_app.route("/api/pets", methods=["GET"])
    def list_pets():
        conn = get_db()
        pets = [dict(row) for row in conn.execute(
            "SELECT p.*, c.name as client_name FROM pets p LEFT JOIN clients c ON p.client_id=c.id ORDER BY p.id DESC"
        ).fetchall()]
        conn.close()
        return jsonify(pets)
    
    @_app.route("/api/appointments", methods=["GET"])
    def list_appointments():
        conn = get_db()
        appts = [dict(row) for row in conn.execute(
            "SELECT a.*, p.name as pet_name, c.name as client_name FROM appointments a "
            "LEFT JOIN pets p ON a.pet_id=p.id LEFT JOIN clients c ON a.client_id=c.id ORDER BY a.date DESC"
        ).fetchall()]
        conn.close()
        return jsonify(appts)
    
    @_app.route("/api/appointments", methods=["POST"])
    def create_appointment():
        data = request.get_json(force=True)
        required = ["pet_id", "client_id", "date", "time"]
        for f in required:
            if not data.get(f):
                return jsonify({"error": f"{f} is required"}), 400
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO appointments (pet_id, client_id, date, time, reason) VALUES (?, ?, ?, ?, ?)",
            (data["pet_id"], data["client_id"], data["date"], data["time"], data.get("reason", ""))
        )
        conn.commit()
        appt_id = cur.lastrowid
        conn.close()
        return jsonify({"id": appt_id}), 201
    
    handler = _app
    logger.info("VetClaw Flask fallback handler created")
