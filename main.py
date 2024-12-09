import os
import sqlite3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Çevresel değişkenleri yükle
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")

# SQLite veritabanı oluşturma
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Veritabanı tabloları oluşturma
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    refs INTEGER DEFAULT 0,
    ref_link TEXT
)
""")
conn.commit()

# Ödül bilgileri
REWARDS = [
    {"name": "SUPERCELL", "required_refs": 10, "file": "supercell.txt"},
    {"name": "SMS ONAY", "required_refs": 10, "file": "sms_onay.txt"},
    {"name": "PES", "required_refs": 10, "file": "pes.txt"},
    {"name": "PUBG", "required_refs": 15, "file": "pubg.txt"},
    {"name": "NETFLIX", "required_refs": 30, "file": "netflix.txt"},
    {"name": "BLU TV", "required_refs": 10, "file": "blutv.txt"},
    {"name": "BEIN SPORTS", "required_refs": 10, "file": "bein_sports.txt"},
    {"name": "PLAY KOD", "required_refs": 10, "file": "play_kod.txt"},
    {"name": "EXXEN HESAP", "required_refs": 5, "file": "exxen.txt"},
    {"name": "DISNEY HESAP", "required_refs": 5, "file": "disney.txt"},
]

# Kullanıcıyı kaydetme
def register_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        ref_link = f"https://t.me/retrot4k_bot?start={user_id}"
        cursor.execute("INSERT INTO users (id, refs, ref_link) VALUES (?, ?, ?)", (user_id, 0, ref_link))
        conn.commit()

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    cursor.execute("SELECT refs FROM users WHERE id = ?", (user_id,))
    refs = cursor.fetchone()[0]

    # Anahtar kelime yanıtları için mesaj
    await update.message.reply_text(
        f"Merhaba {update.effective_user.first_name}!\n"
        f"Referans linkini paylaşarak ödüller kazanabilirsin.\n\n"
        f"Mevcut referans sayın: {refs}\n\n"
        "Ödülleri görmek için '🎁 Ödülleri Gör' butonuna tıklayın."
    )

    # Referans ve ödül butonları
    keyboard = [
        [InlineKeyboardButton("📎 Referans Linki Al", callback_data="get_ref_link")],
        [InlineKeyboardButton("🎁 Ödülleri Gör", callback_data="view_rewards")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bir seçim yapın:", reply_markup=reply_markup)

# Referans linki alma
async def get_ref_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cursor.execute("SELECT ref_link FROM users WHERE id = ?", (user_id,))
    ref_link = cursor.fetchone()[0]

    await query.edit_message_text(f"Bu senin referans linkin:\n\n{ref_link}")

# Ödülleri görüntüleme
async def view_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Ödül butonları oluştur
    keyboard = [
        [InlineKeyboardButton(reward["name"], callback_data=f"claim_{reward['name']}")]
        for reward in REWARDS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("🎁 Mevcut Ödüller:\nÖdül almak için birine tıklayın.", reply_markup=reply_markup)

# Ödül talebi işleme
async def claim_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data.split("_", 1)[1]

    cursor.execute("SELECT refs FROM users WHERE id = ?", (user_id,))
    refs = cursor.fetchone()[0]

    for reward in REWARDS:
        if reward["name"] == data:
            if refs < reward["required_refs"]:
                await query.edit_message_text(f"❌ {reward['name']} için yetersiz referans! "
                                              f"{reward['required_refs']} davet gerekiyor.")
                return

            # Stok kontrolü
            file_path = reward["file"]
            if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
                await query.edit_message_text(f"❌ {reward['name']} stoğu tükenmiş!")
                return

            # Ödül verme ve stoktan düşme
            with open(file_path, "r") as f:
                lines = f.readlines()

            reward_content = lines[0].strip()
            with open(file_path, "w") as f:
                f.writelines(lines[1:])

            # Referansları düşür
            cursor.execute("UPDATE users SET refs = refs - ? WHERE id = ?", (reward["required_refs"], user_id))
            conn.commit()

            await query.edit_message_text(f"✅ Tebrikler! {reward['name']} ödülünü aldınız.\n"
                                          f"Ödül: {reward_content}")
            return

    await query.edit_message_text("❌ Geçersiz ödül.")

# Bot başlatma
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Komut ve callback handler'ları
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(get_ref_link, pattern="get_ref_link"))
    app.add_handler(CallbackQueryHandler(view_rewards, pattern="view_rewards"))
    app.add_handler(CallbackQueryHandler(claim_reward, pattern="claim_"))

    app.run_polling()