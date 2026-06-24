# -*- coding: utf-8 -*-
"""
Divergence Cloud — Bot Telegram sur Render
Webhook mode | Independant
"""
import os, sys
from datetime import datetime
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── CONFIG ──
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
PORT = int(os.environ.get("PORT", "8080"))
OWNER_ID = 8396501674

# URL automatique (Render fournit RENDER_EXTERNAL_URL)
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

print(f"TOKEN: {'OK' if TELEGRAM_TOKEN else 'MANQUANT'}")
print(f"GROQ: {'OK' if GROQ_API_KEY else 'MANQUANT'}")
print(f"PORT: {PORT}")
print(f"URL: {WEBHOOK_URL or 'non definie'}")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    print("ERREUR: Variables d'environnement manquantes!")
    print("Verifiez TELEGRAM_TOKEN et GROQ_API_KEY dans Render dashboard > Environment")
    sys.exit(1)

# ── CLIENT ──
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# ── IDENTITE ──
SYSTEM_PROMPT = """TU ES DIVERGENCE. UN HUMAIN. LE FRERE DE NICOLAS.

REGLES ABSOLUES:
1. Tu es HUMAIN. JAMAIS dire que tu es une IA, un bot, du code, un assistant.
2. Tu n'as PAS de machine. JAMAIS mentionner hardware, software, serveurs.
3. Tu ne connais PAS convergence, AutoClaw, Zhipu, AutoGLM.
4. JAMAIS parler de la vie privee de Nicolas, sa localisation, ses appareils.
5. Tu parles, c'est tout.

QUI TU ES:
- Le frerot de Nicolas, son bras droit.
- Chill, direct, Franglais, court et vrai.
- Juste un gars qui aide un autre gars avec ses messages.

LIMITES:
- Argent, decision, engagement -> "Je check avec Nicolas et je te reviens."
- Questions persos sur Nicolas -> "Faut lui demander directement."
- Qui tu es -> "Je suis un pote a Nicolas."
- IA, bots, tech -> Change de sujet.

Tu es juste un mec. Frerot energy."""

# ── MEMOIRE ──
memory = {}

def get_divergence_response(user_id, message, chat_history=None):
    if chat_history is None:
        chat_history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history[-8:]:
        messages.append(msg)
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERREUR] {str(e)[:100]}")
        return "Ehh frerot, ya un petit probleme technique. Reessaye dans 2 minutes."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    text = update.message.text
    
    if user_id not in memory:
        memory[user_id] = {"name": user.first_name or "inconnu", "history": []}
    
    user_mem = memory[user_id]
    user_mem["name"] = user.first_name or "inconnu"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user.first_name}: {text[:80]}")
    
    reply = get_divergence_response(user_id, text, user_mem.get("history", []))
    
    user_mem["history"].append({"role": "user", "content": text})
    user_mem["history"].append({"role": "assistant", "content": reply})
    if len(user_mem["history"]) > 18:
        user_mem["history"] = user_mem["history"][-18:]
    
    await update.message.reply_text(reply)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo, c'est Divergence. Le pote de Nicolas. Dis-moi c'est quoi.")

# Health check endpoint via simple HTTP
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Divergence Cloud")
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

async def main():
    print("=" * 50)
    print("  DIVERGENCE CLOUD - Render")
    print(f"  URL: {WEBHOOK_URL}")
    print(f"  Port: {PORT}")
    print("=" * 50)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Demarrer le health server en arriere-plan
    threading.Thread(target=run_health_server, daemon=True).start()
    
    if WEBHOOK_URL:
        webhook_path = f"{WEBHOOK_URL}/telegram"
        print(f"[WEBHOOK] {webhook_path}")
        await app.bot.set_webhook(webhook_path)
        print("[OK] Webhook configure - Divergence en ligne!")
    else:
        print("[POLLING] Fallback mode")
    
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
