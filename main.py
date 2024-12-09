import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Telegram Bot Token'ı doğrudan koda ekledik
TOKEN = "7907191541:AAHrm6cwSnp1i7wXspk-beje9ejKYT34qko"  # Bot token'ınızı buraya ekleyin

# Bot sahibinin kullanıcı ID'sini buraya ekleyin
OWNER_ID = 7259547401  # Bot sahibinin Telegram kullanıcı ID'si

# SQLite veritabanı oluşturma
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Veritabanı tabloları oluşturma
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    refs INTEGER DEFAULT 0,
    ref_link TEXT,
    referrer_id INTEGER
)
""")
conn.commit()

# Logging ayarları
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
def register_user(user_id, referrer_id=None):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        ref_link = f"https://t.me/retrot4kk_bot?start={user_id}"
        cursor.execute("INSERT INTO users (id, refs, ref_link, referrer_id) VALUES (?, ?, ?, ?)",
                       (user_id, 0, ref_link, referrer_id))
        conn.commit()
    else:
        logger.info(f"Kullanıcı zaten kaydedilmiş: {user_id}")

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Kullanıcıyı kaydet, referans linki gönder
    referrer_id = None
    if len(update.message.text.split()) > 1:
        referrer_id = int(update.message.text.split()[1])  # Referans linkinden gelen ID'yi al
    register_user(user_id, referrer_id)

    cursor.execute("SELECT refs FROM users WHERE id = ?", (user_id,))
    refs = cursor.fetchone()[0]

    # Anahtar kelime yanıtları için mesaj
    await update.message.reply_text(
        f"Merhaba {update.effective_user.first_name}!\n"
        f"Referans linkini paylaşarak ödüller kazanabilirsin.\n\n"
        f"Mevcut referans sayın: {refs}\n\n"
        "Ödülleri görmek için '🎁 Ödülleri Gör' butonuna tıklayın."
    )

    # Seçim menüsü (Ana Menü)
    keyboard = [
        [InlineKeyboardButton("📎 Referans Linki Al", callback_data="get_ref_link")],
        [InlineKeyboardButton("🎁 Ödülleri Gör", callback_data="view_rewards")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bir seçim yapın:", reply_markup=reply_markup)

# Geri butonuna tıklanınca ana menüye dön
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Ana Menü
    keyboard = [
        [InlineKeyboardButton("📎 Referans Linki Al", callback_data="get_ref_link")],
        [InlineKeyboardButton("🎁 Ödülleri Gör", callback_data="view_rewards")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Bir seçim yapın:", reply_markup=reply_markup)

# Referans linki al
async def get_ref_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    try:
        cursor.execute("SELECT ref_link FROM users WHERE id = ?", (user_id,))
        ref_link = cursor.fetchone()[0]

        # Geri butonu ekleyerek referans linkini göster
        keyboard = [
            [InlineKeyboardButton("Geri", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Bu senin referans linkin:\n\n{ref_link}", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Referans linki alınırken hata oluştu: {e}")
        await query.edit_message_text("❌ Bir hata oluştu, lütfen tekrar deneyin.")

# Ödülleri görüntüleme
async def view_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # Ödül butonları oluştur
        keyboard = [
            [InlineKeyboardButton(reward["name"], callback_data=f"claim_{reward['name']}")]
            for reward in REWARDS
        ]
        keyboard.append([InlineKeyboardButton("Geri", callback_data="back_to_menu")])  # Geri butonu

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("🎁 Mevcut Ödüller:\nÖdül almak için birine tıklayın.", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ödüller görüntülenirken hata oluştu: {e}")
        await query.edit_message_text("❌ Ödüller yüklenirken bir hata oluştu.")

# Ödül talebi işleme
async def claim_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data.split("_", 1)[1]

    try:
        cursor.execute("SELECT refs FROM users WHERE id = ?", (user_id,))
        refs = cursor.fetchone()[0]

        for reward in REWARDS:
            if reward["name"] == data:
                if refs < reward["required_refs"]:
                    # Bakiye yetersiz olduğunda geri butonuyla birlikte mesaj
                    keyboard = [
                        [InlineKeyboardButton("Geri", callback_data="back_to_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await query.edit_message_text(f"❌ {reward['name']} için yetersiz referans! "
                                                  f"{reward['required_refs']} davet gerekiyor.", reply_markup=reply_markup)
                    return

                # Stok kontrolü
                file_path = reward["file"]
                if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
                    # Stok tükenmişse, geri butonu ekle
                    keyboard = [
                        [InlineKeyboardButton("Geri", callback_data="back_to_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await query.edit_message_text(f"❌ {reward['name']} stoğu tükenmiş!", reply_markup=reply_markup)
                    return

                # Ödül verme ve stoktan düşme işlemi
                with open(file_path, "r") as f:
                    lines = f.readlines()

                reward_content = lines[0].strip()
                with open(file_path, "w") as f:
                    f.writelines(lines[1:])

                # Referansları düşür
                cursor.execute("UPDATE users SET refs = refs - ? WHERE id = ?", (reward["required_refs"], user_id))
                conn.commit()

                # Ödül başarıyla alındığında
                keyboard = [
                    [InlineKeyboardButton("Geri", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(f"✅ Tebrikler! {reward['name']} ödülünü aldınız.\nÖdül: {reward_content}\n\nMenüye dönmek için /start yazın.", reply_markup=reply_markup)

    except Exception as e:
        # Hata mesajını göster
        await query.edit_message_text(f"❌ Hata oluştu: {str(e)}")

# Uygulamayı başlat
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))
application.add_handler(CallbackQueryHandler(get_ref_link, pattern="get_ref_link"))
application.add_handler(CallbackQueryHandler(view_rewards, pattern="view_rewards"))
application.add_handler(CallbackQueryHandler(claim_reward, pattern="claim_"))

application.run_polling()