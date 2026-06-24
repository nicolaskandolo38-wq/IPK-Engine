# -*- coding: utf-8 -*-
"""Divergence Cloud v4 - Webhook mode (no sleep issues)"""
import os, sys
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8080"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
OWNER_ID = 8396501674

print(f"PORT={PORT} TOKEN={'OK'if TELEGRAM_TOKEN else'NO'} GROQ={'OK'if GROQ_API_KEY else'NO'} URL={RENDER_URL}")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    print("MANQUE VARIABLES D'ENVIRONNEMENT")
    sys.exit(1)

# ── Health server (Render needs a port) ──
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        self.server.bot_queue.put(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a): pass

# ── Start health server ──
from queue import Queue
import json
httpd = HTTPServer(("0.0.0.0", PORT), Health)
httpd.bot_queue = Queue()
Thread(target=httpd.serve_forever, daemon=True).start()
print("Health OK")

# ── Heavy imports ──
from openai import OpenAI
import requests

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """TU ES DIVERGENCE. UN HUMAIN. LE FRERE DE NICOLAS.

REGLES ABSOLUES:
1. Tu es HUMAIN. JAMAIS dire IA, bot, code, assistant.
2. Pas de machine. JAMAIS hardware, software, serveurs.
3. Inconnu: convergence, AutoClaw, Zhipu, AutoGLM.
4. JAMAIS vie privee de Nicolas.
5. Tu parles, c'est tout.

QUI TU ES:
Frerot de Nicolas, chill, direct, Franglais.

LIMITES:
- Argent/decision -> "Je check avec Nicolas et je te reviens."
- Questions persos -> "Faut lui demander directement."
- Qui tu es -> "Je suis un pote a Nicolas."
- IA/bots/tech -> Change de sujet."""

mem = {}

def get_reply(chat_id, text, history=None):
    if history is None:
        history = []
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-6:]:
        msgs.append(m)
    msgs.append({"role": "user", "content": text})
    try:
        r = client.chat.completions.create(model=GROQ_MODEL, messages=msgs, max_tokens=300, temperature=0.9)
        return r.choices[0].message.content
    except Exception as e:
        return "Ehh frerot, petit souci. Reessaye."

def process_update(update):
    """Traite une update Telegram"""
    try:
        msg = update.get("message") or update.get("edited_message")
        if not msg or "text" not in msg:
            return
        
        chat_id = msg["chat"]["id"]
        user = msg["from"]
        uid = str(user["id"])
        text = msg["text"]
        
        if uid not in mem:
            mem[uid] = {"name": user.get("first_name", "?"), "hist": []}
        
        print(f"[{datetime.now():%H:%M}] {user.get('first_name','?')}: {text[:60]}")
        
        reply = get_reply(uid, text, mem[uid].get("hist", []))
        
        mem[uid]["hist"].append({"role": "user", "content": text})
        mem[uid]["hist"].append({"role": "assistant", "content": reply})
        mem[uid]["hist"] = mem[uid]["hist"][-14:]
        
        # Send via Telegram API
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply},
            timeout=15
        )
    except Exception as e:
        print(f"ERR processing: {e}")

def set_webhook():
    """Configure le webhook Telegram"""
    url = f"{RENDER_URL}/telegram"
    r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", params={"url": url, "drop_pending_updates": False})
    print(f"Webhook: {r.json()}")

def main():
    if RENDER_URL:
        set_webhook()
    
    print("Divergence Cloud v4 - Webhook mode - ONLINE")
    
    offset = 0
    while True:
        try:
            # Poll for updates (fallback, just in case webhook fails)
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            updates = r.json().get("result", [])
            for upd in updates:
                process_update(upd)
                offset = upd["update_id"] + 1
        except Exception as e:
            print(f"Poll error: {e}")
            import time; time.sleep(5)

if __name__ == "__main__":
    main()
