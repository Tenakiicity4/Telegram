import sqlite3
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Telegram Bot Token'ı
TOKEN = "7371899560:AAFu5iRIrT8A6QRcRQLD6Ly0FcQT6UPtfO0"

# Bot sahibinin kullanıcı ID'si
OWNER_ID = 7259547401  # Bot sahibinin Telegram kullanıcı ID'si

# Zorunlu kanalların bilgileri (2 kanal)
REQUIRED_CHANNELS = ["https://t.me/+-0yqQ4B8sYA1ZDQ0", "@t4kiicity"]  # Burada kanal kullanıcı adlarını girin

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
    {"name": "LIVE", "required_refs": 20, "file": "live.txt"},
]

# Logging ayarları
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Kullanıcıyı kaydetme ve referans yapan kişiye mesaj gönderme
async def register_user(user_id, referrer_id=None, context=None):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        ref_link = f"https://t.me/retroarsivtk_bot?start={user_id}"
        cursor.execute("INSERT INTO users (id, refs, ref_link, referrer_id) VALUES (?, ?, ?, ?)",
                       (user_id, 0, ref_link, referrer_id))
        conn.commit()

        # Eğer referans yapan bir kullanıcı varsa, ona bilgi gönder
        if referrer_id:
            cursor.execute("SELECT refs FROM users WHERE id = ?", (referrer_id,))
            ref_count = cursor.fetchone()[0]  # Referans yapan kişinin mevcut sayısını al

            # Referans yapan kişiye mesaj gönderme
            try:
                await context.bot.send_message(
                    referrer_id,
                    f"🎉 Yeni bir kullanıcı senin referans linkinle kaydoldu!\n"
                    f"Yeni kullanıcı: {user_id}\n"
                    f"Referans sayın: {ref_count + 1}"  # Yeni toplam referans sayısı
                )

                # Ayrıca referans sayısını güncelle
                cursor.execute("UPDATE users SET refs = refs + 1 WHERE id = ?", (referrer_id,))
                conn.commit()

            except Exception as e:
                logger.error(f"Referans yapan kullanıcıya mesaj gönderilirken hata oluştu: {e}")
    else:
        logger.info(f"Kullanıcı zaten kaydedilmiş: {user_id}")

# Kanal kontrolü
async def check_channel_membership(update: Update):
    user_id = update.effective_user.id
    for channel in REQUIRED_CHANNELS:
        chat_member = await update.bot.get_chat_member(channel, user_id)
        if chat_member.status not in [ChatMember.ADMINISTRATOR, ChatMember.MEMBER]:
            await update.message.reply_text(
                f"❌ Botu kullanabilmek için **{channel}** kanalına katılmanız gerekiyor."
            )
            return False
    return True

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_channel_membership(update):
        return

    # Kullanıcıyı kaydet, referans linki gönder
    referrer_id = None
    if len(update.message.text.split()) > 1:
        referrer_id = int(update.message.text.split()[1])  # Referans linkinden gelen ID'yi al
    await register_user(user_id, referrer_id, context)

    cursor.execute("SELECT refs FROM users WHERE id = ?", (user_id,))
    refs = cursor.fetchone()[0]

    # Anahtar kelime yanıtları için mesaj
    await update.message.reply_text(
        f"Merhaba {update.effective_user.first_name}!\n"
        f"Referans linkini paylaşarak ödüller kazanabilirsin.\n\n"
        f"Mevcut referans sayın: {refs}\n\n"
        "Mevcut komutlar:\n"
        "/ekle [user_id] [sayı] - Referans ekle (Sadece kuruculara özel)\n"
        "/mesaj [mesaj] - Tüm kullanıcılara mesaj gönder (Sadece kuruculara özel)\n"
        "/ödüller - Ödülleri görmek için"
    )

# /ekle komutu (Sadece kuruculara özel)
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Bu komut sadece kuruculara özeldir.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Kullanıcı ID'si ve referans sayısı girmeniz gerekiyor.")
        return

    target_user_id = int(context.args[0])
    ref_count = int(context.args[1])

    cursor.execute("SELECT refs FROM users WHERE id = ?", (target_user_id,))
    current_refs = cursor.fetchone()

    if not current_refs:
        await update.message.reply_text("❌ Bu kullanıcı kayıtlı değil.")
        return

    cursor.execute("UPDATE users SET refs = refs + ? WHERE id = ?", (ref_count, target_user_id))
    conn.commit()

    await update.message.reply_text(f"✅ Kullanıcı {target_user_id} başarıyla {ref_count} referans eklendi.")

# /mesaj komutu (Sadece kuruculara özel)
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Bu komut sadece kuruculara özeldir.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("❌ Mesaj yazmanız gerekiyor.")
        return

    message = " ".join(context.args)
    
    # Tüm kullanıcılara mesaj gönder
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for user in users:
        try:
            await update.bot.send_message(user[0], message)
        except Exception as e:
            logger.error(f"Mesaj gönderilirken hata oluştu: {e}")

    await update.message.reply_text("✅ Mesaj tüm kullanıcılara gönderildi.")

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

# Ödül talep etme ve dosya silme
async def claim_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    reward_name = query.data.split("_")[1]  # "claim_<reward_name>" kısmından ödül ismini al
    user_id = update.effective_user.id
    
    # Kullanıcının mevcut referans sayısını al
    cursor.execute("SELECT refs FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    if not user_data:
        await query.answer("❌ Kullanıcı bulunamadı.")
        return

    user_refs = user_data[0]

    # Ödül koşulunu kontrol et
    reward = next((r for r in REWARDS if r["name"] == reward_name), None)
    if not reward:
        await query.answer("❌ Geçersiz ödül.")
        return

    if user_refs >= reward["required_refs"]:
        # Ödül verildi
        # Ödülü aldıktan sonra, dosyayı sil
        reward_file = reward["file"]
        
        # Ödül dosyasını sil
        if os.path.exists(reward_file):
            os.remove(reward_file)
            await query.answer(f"✅ {reward_name} ödülünü başarıyla aldınız ve dosya silindi.")
        else:
            await query.answer(f"❌ {reward_name} dosyası bulunamadı.")
    else:
        await query.answer(f"❌ {reward_name} ödülünü almak için {reward['required_refs']} referans gerekmektedir. Mevcut referans sayınız: {user_refs}")

# Uygulamayı başlat
application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ekle", add_user))
application.add_handler(CommandHandler("mesaj", send_message))
application.add_handler(CallbackQueryHandler(view_rewards, pattern="^claim_"))
application.add_handler(CallbackQueryHandler(view_rewards, pattern="^back_to_menu"))
application.add_handler(CallbackQueryHandler(claim_reward, pattern="^claim_"))

application.run_polling()