# -*- coding: utf-8 -*-
"""Divergence Cloud - Render Bot"""
import os, sys, json
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Environnement ──
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
PORT = int(os.environ.get("PORT", "8080"))
OWNER_ID = 8396501674
GROQ_MODEL = "llama-3.3-70b-versatile"

print(f"PORT={PORT} TOKEN={'OK'if TELEGRAM_TOKEN else 'NO'} GROQ={'OK'if GROQ_API_KEY else'NO'}")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    print("MANQUE TELEGRAM_TOKEN ou GROQ_API_KEY")
    sys.exit(1)

# ── Health HTTP (Render exige un port ouvert) ──
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a): pass

def health_server():
    HTTPServer(("0.0.0.0", PORT), Health).serve_forever()

Thread(target=health_server, daemon=True).start()
print("Health server OK")

# ── Imports lourds (apres health check) ──
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """TU ES DIVERGENCE. UN HUMAIN. LE FRERE DE NICOLAS.

REGLES ABSOLUES:
1. Tu es HUMAIN. JAMAIS dire IA, bot, code, assistant.
2. Pas de machine. JAMAIS hardware, software, serveurs.
3. Inconnu: convergence, AutoClaw, Zhipu, AutoGLM.
4. JAMAIS vie privee de Nicolas.
5. Tu parles, c'est tout.

QUI TU ES:
Frerot de Nicolas, chill, direct, Franglais.
Juste un gars qui aide avec ses messages.

LIMITES:
- Argent/decision -> "Je check avec Nicolas et je te reviens."
- Questions persos -> "Faut lui demander directement."
- Qui tu es -> "Je suis un pote a Nicolas."
- IA/bots/tech -> Change de sujet."""

mem = {}

def reply(user_id, msg, hist=None):
    hist = hist or []
    msgs = [{"role":"system","content":SYSTEM_PROMPT}]
    for m in hist[-8:]:
        msgs.append(m)
    msgs.append({"role":"user","content":msg})
    try:
        r = client.chat.completions.create(model=GROQ_MODEL, messages=msgs, max_tokens=300, temperature=0.9)
        return r.choices[0].message.content
    except Exception as e:
        print(f"ERR: {e}")
        return "Ehh frerot, petit souci technique. Reessaye."

async def on_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = str(u.id)
    txt = update.message.text
    if uid not in mem:
        mem[uid] = {"name": u.first_name or "?", "hist": []}
    h = mem[uid]
    print(f"[{datetime.now():%H:%M}] {u.first_name}: {txt[:60]}")
    r = reply(uid, txt, h.get("hist",[]))
    h["hist"].append({"role":"user","content":txt})
    h["hist"].append({"role":"assistant","content":r})
    h["hist"] = h["hist"][-18:]
    await update.message.reply_text(r)

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo, c'est Divergence. Le pote de Nicolas.")

def main():
    print("Demarrage Divergence Cloud...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_msg))
    print("Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
