# ============================================================
# app.py - Hashira v2 | All Features
# ============================================================

from flask import (Flask, request, jsonify, render_template,
                   session, redirect, url_for)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid, requests, base64, time, json, re
from functools import wraps
from config import get_db, GEMINI_API_KEY, APP_SECRET_KEY, DEBUG_MODE

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
CORS(app)

# ============================================================
# GEMINI HELPERS
# ============================================================

GEMINI_TEXT_URL  = ("https://generativelanguage.googleapis.com/v1beta/models/"
                    "gemini-2.5-flash:generateContent?key={}")
GEMINI_VIS_URL   = GEMINI_TEXT_URL   # 2.5-flash is multimodal

def _post_gemini(url, payload, retries=2):
    for attempt in range(retries):
        r = requests.post(url, json=payload, timeout=40)
        if r.status_code == 429:
            print(f"[Gemini] 429 rate limit — waiting 12s (attempt {attempt+1})")
            time.sleep(12)
            continue
        if r.status_code != 200:
            print(f"[Gemini {r.status_code}] {r.text[:300]}")
            r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    raise Exception("Rate limit exceeded after retries. Wait a moment and try again.")


def call_gemini_text(prompt):
    url     = GEMINI_TEXT_URL.format(GEMINI_API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}
    }
    return _post_gemini(url, payload)


def call_gemini_vision(prompt, image_b64, mime_type="image/jpeg"):
    """Send image + text to Gemini vision."""
    url     = GEMINI_VIS_URL.format(GEMINI_API_KEY)
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}
    }
    return _post_gemini(url, payload)


def gemini_ok():
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip()
                not in ("", "your_gemini_api_key_here"))


# ============================================================
# AUTH DECORATORS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not logged in", "redirect": "/login"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Admin only"}), 403
        return f(*args, **kwargs)
    return decorated


# ============================================================
# DB HELPERS
# ============================================================

def db_query(sql, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
    except Exception as e:
        print(f"[DB] {e}")
        return None
    finally:
        cur.close(); conn.close()


def get_or_create_session(user_id, session_uid=None):
    if not session_uid:
        session_uid = str(uuid.uuid4())
    existing = db_query("SELECT * FROM chat_sessions WHERE session_uid=%s",
                        (session_uid,), fetchone=True)
    if not existing:
        db_query("INSERT INTO chat_sessions (session_uid,user_id,title) VALUES (%s,%s,%s)",
                 (session_uid, user_id, "New Chat"), commit=True)
    return session_uid


def get_history(session_uid, limit=20):
    return db_query(
        "SELECT role,message,mode,has_image,created_at FROM chat_history "
        "WHERE session_uid=%s ORDER BY created_at ASC LIMIT %s",
        (session_uid, limit), fetchall=True) or []


def save_msg(session_uid, role, message, mode, has_image=False):
    db_query(
        "INSERT INTO chat_history (session_uid,role,message,mode,has_image) VALUES (%s,%s,%s,%s,%s)",
        (session_uid, role, message, mode, has_image), commit=True)
    # Auto-title from first user message
    if role == "user":
        sess = db_query("SELECT title FROM chat_sessions WHERE session_uid=%s",
                        (session_uid,), fetchone=True)
        if sess and sess["title"] == "New Chat":
            title = message[:60] + ("..." if len(message) > 60 else "")
            db_query("UPDATE chat_sessions SET title=%s WHERE session_uid=%s",
                     (title, session_uid), commit=True)


def build_mode_prompt(mode):
    if mode == "exam":
        return ("Answer in clear bullet points suitable for 2-5 marks exam answer. "
                "Be concise, structured, exam-ready. End with one encouraging line.")
    return ("Explain clearly in simple English using numbered step-by-step format. "
            "Be supportive and optimistic. End with a motivating tip.")


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html",
                           username=session.get("username"),
                           role=session.get("role"),
                           avatar=session.get("avatar","🎓"))


@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect("/")
    return render_template("login.html")


@app.route("/admin")
def admin_page():
    if session.get("role") != "admin":
        return redirect("/login")
    return render_template("admin.html", username=session.get("username"))


# ============================================================
# AUTH API
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():
    d        = request.get_json()
    username = d.get("username","").strip()
    email    = d.get("email","").strip()
    password = d.get("password","").strip()

    if not all([username, email, password]):
        return jsonify({"error": "All fields required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    existing = db_query("SELECT id FROM users WHERE username=%s OR email=%s",
                        (username, email), fetchone=True)
    if existing:
        return jsonify({"error": "Username or email already taken"}), 400

    pw_hash  = generate_password_hash(password)
    avatars  = ["🎓","📚","🧠","⚡","🔬","🎯","🌟","🚀"]
    avatar   = avatars[hash(username) % len(avatars)]
    db_query("INSERT INTO users (username,email,password_hash,avatar) VALUES (%s,%s,%s,%s)",
             (username, email, pw_hash, avatar), commit=True)

    return jsonify({"success": True, "message": "Account created! Please log in."})


@app.route("/api/login", methods=["POST"])
def login():
    d        = request.get_json()
    username = d.get("username","").strip()
    password = d.get("password","").strip()

    user = db_query("SELECT * FROM users WHERE username=%s OR email=%s",
                    (username, username), fetchone=True)

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    session["role"]     = user["role"]
    session["avatar"]   = user["avatar"]

    db_query("UPDATE users SET last_login=NOW() WHERE id=%s", (user["id"],), commit=True)
    return jsonify({"success": True, "role": user["role"]})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# ============================================================
# CHAT API
# ============================================================

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    user_id = session["user_id"]
    mode    = request.form.get("mode", "normal")
    message = request.form.get("message", "").strip()
    sess_uid= request.form.get("session_uid") or session.get("current_session")

    image_b64  = None
    mime_type  = "image/jpeg"
    has_image  = False

    # Handle image upload
    if "image" in request.files:
        img   = request.files["image"]
        mime_type = img.mimetype or "image/jpeg"
        raw   = img.read()
        image_b64 = base64.b64encode(raw).decode("utf-8")
        has_image = True

    if not message and not has_image:
        return jsonify({"error": "Message or image required"}), 400

    sess_uid = get_or_create_session(user_id, sess_uid)
    session["current_session"] = sess_uid

    history  = get_history(sess_uid)
    history_text = "\n".join(
        f"{'Student' if m['role']=='user' else 'Hashira'}: {m['message']}"
        for m in history[-8:]
    )

    display_msg = message or "📷 [Image uploaded]"
    save_msg(sess_uid, "user", display_msg, mode, has_image)

    if not gemini_ok():
        bot_reply = "⚠️ Gemini API key not configured. Please set it in config.py."
    else:
        try:
            instr = build_mode_prompt(mode)

            # ── RESOURCE FINDER: detect resource requests ──
            resource_keywords = ["find","resource","link","website","book","tutorial",
                                 "where can i","recommend","reference","article","video","course"]
            wants_resources = any(kw in message.lower() for kw in resource_keywords)

            # ── DIAGRAM: detect diagram requests ──
            diagram_keywords = ["diagram","draw","visualize","chart","flowchart","explain with"]
            wants_diagram = any(kw in message.lower() for kw in diagram_keywords)

            if has_image and image_b64:
                prompt = f"""You are Hashira, a warm AI study assistant.
{instr}
Previous conversation:
{history_text}

The student has uploaded an image. Analyse it carefully and explain what it shows in the context of their question.
Student's question: {message or 'Please explain this image.'}

Provide a clear, educational explanation of the image."""
                bot_reply = call_gemini_vision(prompt, image_b64, mime_type)

            elif wants_diagram:
                prompt = f"""You are Hashira, a warm AI study assistant.
{instr}
Previous conversation:
{history_text}
Student's question: {message}

Provide:
1. A clear explanation
2. An ASCII diagram or structured visual representation using text/unicode characters
3. Step-by-step breakdown

Make the diagram clear and educational."""
                bot_reply = call_gemini_text(prompt)

            elif wants_resources:
                prompt = f"""You are Hashira, a warm AI study assistant.
{instr}
Previous conversation:
{history_text}
Student's question: {message}

Provide:
1. A brief answer to their question
2. **📚 Recommended Resources** section with:
   - 2-3 free websites (like Khan Academy, MDN, W3Schools, GeeksForGeeks, etc.)
   - 1-2 YouTube search terms they can use
   - 1 book recommendation if relevant
   Format each resource clearly with what they'll find there."""
                bot_reply = call_gemini_text(prompt)

            else:
                prompt = f"""You are Hashira, a warm, friendly, supportive AI study assistant.
{instr}
Previous conversation:
{history_text}
Student's question: {message}

Your response:"""
                bot_reply = call_gemini_text(prompt)

        except Exception as e:
            err = str(e)
            print(f"[Gemini ERROR] {err}")
            if "429" in err or "rate" in err.lower():
                bot_reply = "⏳ Gemini is busy (rate limit). Please wait 15 seconds and try again."
            else:
                bot_reply = f"⚠️ AI Error: {err}"

    save_msg(sess_uid, "assistant", bot_reply, mode)
    return jsonify({"response": bot_reply, "mode": mode, "session_uid": sess_uid})


# ============================================================
# CHAT HISTORY / SESSIONS
# ============================================================

@app.route("/api/sessions", methods=["GET"])
@login_required
def list_sessions():
    sessions = db_query(
        "SELECT session_uid,title,created_at,updated_at FROM chat_sessions "
        "WHERE user_id=%s ORDER BY updated_at DESC LIMIT 30",
        (session["user_id"],), fetchall=True) or []
    for s in sessions:
        s["created_at"] = str(s["created_at"])
        s["updated_at"] = str(s["updated_at"])
    return jsonify({"sessions": sessions})


@app.route("/api/sessions/<uid>", methods=["GET"])
@login_required
def load_session(uid):
    # Verify ownership
    sess = db_query("SELECT * FROM chat_sessions WHERE session_uid=%s AND user_id=%s",
                    (uid, session["user_id"]), fetchone=True)
    if not sess:
        return jsonify({"error": "Session not found"}), 404

    session["current_session"] = uid
    msgs = get_history(uid, limit=200)
    for m in msgs:
        m["created_at"] = str(m["created_at"])
    return jsonify({"messages": msgs, "title": sess["title"]})


@app.route("/api/sessions/<uid>", methods=["DELETE"])
@login_required
def delete_session(uid):
    db_query("DELETE FROM chat_sessions WHERE session_uid=%s AND user_id=%s",
             (uid, session["user_id"]), commit=True)
    return jsonify({"success": True})


@app.route("/api/sessions/new", methods=["POST"])
@login_required
def new_session():
    uid = str(uuid.uuid4())
    get_or_create_session(session["user_id"], uid)
    session["current_session"] = uid
    return jsonify({"session_uid": uid})


@app.route("/api/clear", methods=["POST"])
@login_required
def clear_current():
    uid = session.get("current_session")
    if uid:
        db_query("DELETE FROM chat_history WHERE session_uid=%s", (uid,), commit=True)
        db_query("UPDATE chat_sessions SET title='New Chat' WHERE session_uid=%s",
                 (uid,), commit=True)
    return jsonify({"success": True})


# ============================================================
# SUMMARIZE
# ============================================================

@app.route("/api/summarize", methods=["POST"])
@login_required
def summarize():
    uid  = session.get("current_session")
    hist = get_history(uid, limit=100) if uid else []

    if not hist:
        return jsonify({"summary": "No messages to summarize yet!"})

    conv = "\n".join(
        f"{'Student' if m['role']=='user' else 'Hashira'}: {m['message']}"
        for m in hist
    )

    if gemini_ok():
        try:
            summary = call_gemini_text(
                f"""Summarize this student study session:\n\n{conv}\n\n
Provide:
1. **Topics Covered**
2. **Key Concepts Learned**
3. **Study Tips Given**
4. **Encouragement** (one motivating line)"""
            )
        except Exception as e:
            summary = f"Could not generate summary: {e}"
    else:
        msgs = [m["message"] for m in hist if m["role"] == "user"]
        summary = f"**Topics explored:** {len(msgs)} question(s) asked this session.\n\n💡 Add your Gemini key for AI-powered summaries!"

    return jsonify({"summary": summary})


# ============================================================
# SAVED MESSAGES (Offline Bookmarks)
# ============================================================

@app.route("/api/saved", methods=["GET"])
@login_required
def get_saved():
    items = db_query(
        "SELECT id,message,note,saved_at FROM saved_messages WHERE user_id=%s ORDER BY saved_at DESC",
        (session["user_id"],), fetchall=True) or []
    for i in items:
        i["saved_at"] = str(i["saved_at"])
    return jsonify({"saved": items})


@app.route("/api/saved", methods=["POST"])
@login_required
def save_message_api():
    d       = request.get_json()
    message = d.get("message","").strip()
    note    = d.get("note","").strip()
    if not message:
        return jsonify({"error": "Message required"}), 400
    db_query("INSERT INTO saved_messages (user_id,message,note) VALUES (%s,%s,%s)",
             (session["user_id"], message, note), commit=True)
    return jsonify({"success": True})


@app.route("/api/saved/<int:sid>", methods=["DELETE"])
@login_required
def delete_saved(sid):
    db_query("DELETE FROM saved_messages WHERE id=%s AND user_id=%s",
             (sid, session["user_id"]), commit=True)
    return jsonify({"success": True})


# ============================================================
# ADMIN API
# ============================================================

@app.route("/api/admin/users", methods=["GET"])
@login_required
@admin_required
def admin_users():
    users = db_query(
        "SELECT id,username,email,role,avatar,created_at,last_login FROM users ORDER BY created_at DESC",
        fetchall=True) or []
    for u in users:
        u["created_at"] = str(u["created_at"])
        u["last_login"]  = str(u["last_login"]) if u["last_login"] else "Never"
        # Count sessions
        sc = db_query("SELECT COUNT(*) as c FROM chat_sessions WHERE user_id=%s",
                      (u["id"],), fetchone=True)
        mc = db_query("SELECT COUNT(*) as c FROM chat_history ch "
                      "JOIN chat_sessions cs ON ch.session_uid=cs.session_uid WHERE cs.user_id=%s",
                      (u["id"],), fetchone=True)
        u["session_count"] = sc["c"] if sc else 0
        u["message_count"] = mc["c"] if mc else 0
    return jsonify({"users": users})


@app.route("/api/admin/users/<int:uid>", methods=["DELETE"])
@login_required
@admin_required
def admin_delete_user(uid):
    if uid == session["user_id"]:
        return jsonify({"error": "Cannot delete yourself"}), 400
    db_query("DELETE FROM users WHERE id=%s", (uid,), commit=True)
    return jsonify({"success": True})


@app.route("/api/admin/stats", methods=["GET"])
@login_required
@admin_required
def admin_stats():
    total_users    = db_query("SELECT COUNT(*) as c FROM users", fetchone=True)
    total_sessions = db_query("SELECT COUNT(*) as c FROM chat_sessions", fetchone=True)
    total_messages = db_query("SELECT COUNT(*) as c FROM chat_history", fetchone=True)
    today_users    = db_query("SELECT COUNT(*) as c FROM users WHERE DATE(last_login)=CURDATE()", fetchone=True)
    return jsonify({
        "total_users":    total_users["c"] if total_users else 0,
        "total_sessions": total_sessions["c"] if total_sessions else 0,
        "total_messages": total_messages["c"] if total_messages else 0,
        "active_today":   today_users["c"] if today_users else 0,
    })


@app.route("/api/admin/promote/<int:uid>", methods=["POST"])
@login_required
@admin_required
def promote_user(uid):
    db_query("UPDATE users SET role='admin' WHERE id=%s", (uid,), commit=True)
    return jsonify({"success": True})


# ============================================================
# CURRENT SESSION INFO
# ============================================================

@app.route("/api/me", methods=["GET"])
@login_required
def me():
    return jsonify({
        "user_id":  session["user_id"],
        "username": session["username"],
        "role":     session["role"],
        "avatar":   session.get("avatar","🎓"),
        "current_session": session.get("current_session")
    })


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("="*55)
    print("  🔥 Hashira v2 — AI Study Companion")
    print(f"  Gemini: {'✅ Connected' if gemini_ok() else '❌ Key not set'}")
    print("  URL: http://127.0.0.1:5000")
    print("="*55)
    app.run(debug=DEBUG_MODE, host="0.0.0.0", port=5000)