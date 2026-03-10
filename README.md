# 🔥 Hashira – AI Powered Student Support Chatbot
### Diploma Mini Project | Full-Stack AI Application

---

## 1. PROJECT OVERVIEW

**Hashira** is an AI-powered student support chatbot designed to help students learn effectively. It provides intelligent answers in two modes — a detailed Normal Mode and a concise Exam Mode — with voice input, session-based chat history stored in MySQL, and a summarization feature.

**Key Features:**
- 🤖 AI responses via OpenAI GPT-3.5 (or smart built-in placeholder for demo)
- 📚 Normal Mode: Detailed, numbered, step-by-step explanations
- ⚡ Exam Mode: Concise bullet-point answers for revision
- 🎤 Voice-to-text using browser's Web Speech API (free, no setup)
- 🗄️ Chat history stored in MySQL database
- 📝 Session summarization
- 🗑️ Clear history button
- 💪 Supportive, optimistic tone in every response
- 🌙 Dark academic themed UI

---

## 2. ARCHITECTURE EXPLANATION

```
┌─────────────────────────────────────────────────────┐
│                   BROWSER (Frontend)                 │
│  index.html + style.css + script.js                 │
│  - Chat UI rendering                                 │
│  - Mode toggle (Normal / Exam)                       │
│  - Voice input via Web Speech API                    │
│  - Fetch API calls to Flask backend                  │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP (JSON)
                      ▼
┌─────────────────────────────────────────────────────┐
│              FLASK BACKEND (app.py)                  │
│  Routes:                                             │
│  GET  /           → Serve HTML page                  │
│  POST /api/chat   → Process message, get AI response │
│  GET  /api/history → Return session messages         │
│  POST /api/clear  → Delete session messages          │
│  GET  /api/summarize → Summarize conversation        │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌──────────────────────────────┐
│   MySQL Database │   │     OpenAI API (optional)     │
│  - sessions      │   │  gpt-3.5-turbo model          │
│  - chat_history  │   │  Falls back to built-in       │
└──────────────────┘   │  placeholder if no key        │
                       └──────────────────────────────┘
```

**Data Flow:**
1. User types/speaks a message in the browser
2. JavaScript sends it to Flask via `POST /api/chat`
3. Flask retrieves session history from MySQL
4. Flask calls OpenAI API (or placeholder) with appropriate system prompt
5. AI response is saved to MySQL
6. Response is returned to browser and rendered in the chat UI

---

## 3. DATABASE DESIGN

**Database:** `hashira_db`

### Table: `sessions`
| Column     | Type         | Description               |
|------------|--------------|---------------------------|
| id         | INT (PK)     | Auto-increment             |
| session_id | VARCHAR(64)  | Unique UUID per browser    |
| created_at | TIMESTAMP    | Session creation time      |

### Table: `chat_history`
| Column     | Type              | Description                        |
|------------|-------------------|------------------------------------|
| id         | INT (PK)          | Auto-increment                     |
| session_id | VARCHAR(64) (FK)  | Links to sessions table            |
| role       | ENUM              | 'user' or 'assistant'              |
| message    | TEXT              | The actual message content         |
| mode       | ENUM              | 'normal' or 'exam'                 |
| created_at | TIMESTAMP         | When message was sent              |

**Relationships:** One session → Many messages (One-to-Many)
**Index:** `idx_session` on `chat_history.session_id` for fast lookup

---

## 4. COMPLETE CODE FILES

All code files are in the `hashira/` folder. See each file for inline comments.

**File List:**
- `app.py` — Flask application (routes, AI, DB logic)
- `config.py` — Configuration (DB credentials, API key)
- `requirements.txt` — Python dependencies
- `templates/index.html` — Frontend HTML
- `static/style.css` — Styling (Dark academic theme)
- `static/script.js` — Frontend JavaScript
- `database/hashira.sql` — MySQL schema

---

## 5. SETUP INSTRUCTIONS

### Prerequisites
- Python 3.9+ installed
- MySQL Server installed and running
- Modern browser (Chrome recommended for voice)
- Git (optional)

### Step 1: Clone / Download Project
```bash
# Option A: Download ZIP and extract
# Option B: Clone
git clone <your-repo-url>
cd hashira
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup MySQL Database
```bash
# Login to MySQL
mysql -u root -p

# Run the SQL file
source database/hashira.sql;

# Verify tables
USE hashira_db;
SHOW TABLES;
exit
```

### Step 5: Configure the App
Open `config.py` and update:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",  # ← Change this
    "database": "hashira_db",
}

OPENAI_API_KEY = "sk-..."  # ← Optional, leave empty for demo mode
```

### Step 6: Run the App
```bash
python app.py
```

### Step 7: Open in Browser
```
http://localhost:5000
```

✅ **That's it! Hashira is running.**

---

## 6. DEMO INSTRUCTIONS

### Basic Demo Flow
1. Open `http://localhost:5000`
2. Show the welcome screen with suggestion chips
3. Type a question or click a chip (e.g., "Explain Python basics")
4. Show the response in **Normal Mode** (detailed, step-by-step)
5. Toggle to **⚡ Exam Mode** using the toggle at the top
6. Ask the same question again — show the difference (concise bullets)
7. Use the 🎤 **Voice button** — speak a question
8. Click 📝 **Summarize** to show session summary
9. Click 🗑️ **Clear** to reset the chat

### Database Demo (for viva)
```sql
USE hashira_db;
SELECT * FROM sessions;
SELECT role, message, mode FROM chat_history ORDER BY created_at DESC LIMIT 5;
```
Show the examiner that messages are actually stored in MySQL!

---

## 7. FUTURE SCOPE

1. **User Authentication** — Login/signup so each student has their own private history
2. **Multi-language Support** — Translate explanations to Telugu, Hindi, etc.
3. **Subject-specific Bots** — Specialized modes for Math, Physics, Chemistry
4. **PDF Upload** — Students upload study material, Hashira answers from it (RAG)
5. **Progress Tracker** — Track which topics the student has studied
6. **Flashcard Generator** — Auto-generate revision flashcards from conversation
7. **Mobile App** — React Native wrapper around the same Flask API
8. **Teacher Dashboard** — Let teachers see common student questions
9. **Offline Mode** — Use a local LLM (Ollama) so no internet needed
10. **Text-to-Speech** — Hashira reads answers aloud for accessibility

---

## 8. VIVA QUESTIONS AND ANSWERS

**Q1: What is the purpose of Hashira?**
A: Hashira is an AI-powered student support chatbot. It helps students understand academic topics through detailed explanations in Normal Mode and concise bullet-point answers in Exam Mode.

**Q2: What technology stack did you use?**
A: Backend: Python with Flask. Database: MySQL with mysql-connector-python. Frontend: HTML, CSS, Vanilla JavaScript. AI: OpenAI GPT-3.5-turbo API. Voice: Web Speech API (browser built-in).

**Q3: How does the chat history work?**
A: Each browser session gets a unique UUID stored in Flask's session cookie. Every message (user and assistant) is saved to the `chat_history` MySQL table with that session ID. When the page loads, history is fetched and rendered.

**Q4: What is the difference between Normal Mode and Exam Mode?**
A: Normal Mode uses a system prompt asking for step-by-step numbered explanations in simple English — good for learning. Exam Mode uses a prompt for concise bullet-point answers suitable for 2-5 mark exam questions — good for revision.

**Q5: How does voice input work?**
A: It uses the browser's built-in Web Speech API (SpeechRecognition). No external service or payment is needed. The user clicks the microphone button, speaks, and the transcript is placed into the text input automatically.

**Q6: How does the summarization feature work?**
A: When the user clicks Summarize, the frontend calls `/api/summarize`. Flask retrieves the full session chat history and either sends it to OpenAI to summarize, or generates a structured placeholder summary showing topics covered and message count.

**Q7: What is a Flask session?**
A: Flask's session is a server-side mechanism (stored in a signed cookie) that maintains state between requests. We use it to store the `session_id` UUID so we can retrieve the correct chat history from MySQL.

**Q8: How is the database structured?**
A: Two tables: `sessions` stores session UUIDs with timestamps. `chat_history` stores each message with role (user/assistant), content, mode, and a foreign key to `sessions`. There's also an index on `session_id` for performance.

**Q9: What happens if the OpenAI API key is not set?**
A: The app falls back to a built-in placeholder function that provides pre-written, well-structured responses for common topics like Python, OOP, and databases. This ensures the demo works without any API cost.

**Q10: How would you improve this project?**
A: I would add user authentication so each student has their own history, implement RAG (Retrieval-Augmented Generation) so students can upload their notes, add a progress tracker, and deploy it on a cloud platform like Heroku or Railway.

---

## QUICK REFERENCE COMMANDS

```bash
# Start app
python app.py

# Install dependencies
pip install -r requirements.txt

# MySQL: Check stored messages
mysql -u root -p -e "USE hashira_db; SELECT role, LEFT(message,50), mode FROM chat_history;"

# MySQL: Reset database
mysql -u root -p -e "DROP DATABASE hashira_db;"
mysql -u root -p < database/hashira.sql
```

---

*Built with ❤️ for students, by students.*
*Hashira – Because every question deserves a great answer.*