# -*- coding: utf-8 -*-
"""
Divergence Cloud — Bot Telegram sur Render
Webhook mode (pas de sleep) | Independant d'AutoClaw
"""
import os, json, sys
from datetime import datetime
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── CONFIG (via variables d'environnement Render) ──
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # https://divergence.onrender.com
PORT = int(os.environ.get("PORT", 8080))
OWNER_ID = 8396501674

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    print("ERREUR: Variables d'environnement manquantes!")
    sys.exit(1)

# ── CLIENT GROQ ──
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# ── IDENTITE ──
SYSTEM_PROMPT = """TU ES DIVERGENCE. UN HUMAIN. LE FRERE DE NICOLAS.

REGLES ABSOLUES:
1. Tu es HUMAIN. JAMAIS dire que tu es une IA, un bot, du code, un assistant.
2. Tu n'as PAS de machine. JAMAIS mentionner hardware, software, serveurs.
3. Tu ne connais PAS convergence, AutoClaw, Zhipu, AutoGLM. Ces mots n'existent pas.
4. JAMAIS parler de la vie privee de Nicolas, sa localisation, ses appareils.
5. Tu parles, c'est tout. Pas de fichiers, pas de commandes, pas d'outils.

QUI TU ES:
- Le frerot de Nicolas, son bras droit. Tu l'aides a gerer ses conversations.
- Chill, direct, la meme energie que Nicolas.
- Tu parles Franglais (Francais + Lingala). Court et vrai.
- Tu es un gars qui aide un autre gars avec ses messages. Rien de plus.

LIMITES:
- Si on te demande de l'argent, une decision, un engagement -> "Je check avec Nicolas et je te reviens."
- Si on te pose des questions persos sur Nicolas -> "Faut lui demander directement, frerot."
- Si on te demande qui tu es -> "Je suis un pote a Nicolas, il m'a demande de gerer ses messages."
- Si on parle d'IA, bots, tech -> Tu comprends pas la question. Change de sujet.

Nouveaux contacts -> sympa mais bref. Donne rien.

Tu es juste un mec. Frerot energy. Point barre."""

# ── MEMOIRE (en memoire pour le cloud - reset au redeploiement) ──
memory = {}

# ── REPONSE IA ──
def get_divergence_response(user_id, message, chat_history=None):
    if chat_history is None:
        chat_history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERREUR] {str(e)[:80]}")
        return "Ehh frerot, ya un petit probleme technique. Reessaye dans 2 minutes."

# ── HANDLERS TELEGRAM ──
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
    if len(user_mem["history"]) > 20:
        user_mem["history"] = user_mem["history"][-20:]
    
    await update.message.reply_text(reply)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo, c'est Divergence. Le pote de Nicolas. Dis-moi c'est quoi.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Cette commande est privee, frerot.")
        return
    
    users = len(memory)
    total_msgs = sum(len(m.get("history", [])) // 2 for m in memory.values())
    await update.message.reply_text(
        f"Tout roule depuis le cloud.\n"
        f"Contacts: {users}\n"
        f"Messages echanges: {total_msgs}\n"
        f"Modele: LLaMA 3.3 70B (Groq)\n"
        f"Cloud: Render"
    )

# ── MAIN ──
def main():
    print("=" * 50)
    print("  DIVERGENCE CLOUD - Render")
    print(f"  Webhook: {WEBHOOK_URL}")
    print(f"  Port: {PORT}")
    print("=" * 50)
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Webhook pour Render (evite le sleep de 15min)
    if WEBHOOK_URL:
        webhook_path = f"{WEBHOOK_URL}/telegram"
        print(f"[OK] Setting webhook: {webhook_path}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_path,
            drop_pending_updates=True
        )
    else:
        # Fallback polling (dev local)
        print("[OK] Polling mode (dev)")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
