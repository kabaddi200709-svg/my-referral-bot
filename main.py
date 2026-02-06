import telebot
import sqlite3

# --- Aapki Settings ---
API_TOKEN = '8306641308:AAGQyrXw_sVAJAetdIhX4_K-b2yXtW04mR4'
ADMIN_ID = 8315839506  # Aapki Numeric ID

CHANNELS = ['@techearning0070', '@TechEarning00709'] 
REF_REWARD = 2       # Ab 2 points milenge
MIN_WITHDRAW = 20    # Ab 20 points par withdrawal hoga

bot = telebot.TeleBot(API_TOKEN)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('referral_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (user_id TEXT PRIMARY KEY, balance INTEGER, referred_by TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('referral_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referred_by FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def check_all_joined(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None
    
    init_db()
    user = get_user(user_id)

    if user is None:
        conn = sqlite3.connect('referral_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, 0, referrer_id))
        conn.commit()
        conn.close()
    
    if check_all_joined(message.from_user.id):
        current_user = get_user(user_id)
        if current_user and current_user[1] and current_user[1] != "rewarded":
            ref_id = current_user[1]
            conn = sqlite3.connect('referral_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REF_REWARD, ref_id))
            cursor.execute("UPDATE users SET referred_by = 'rewarded' WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            try:
                bot.send_message(ref_id, f"🎉 Aapke link se koi juda! Aapko {REF_REWARD} points mile.")
            except: pass

        user_data = get_user(user_id)
        bot_uname = bot.get_me().username
        msg = (f"👋 Namaste {username}!\n\n💰 Balance: {user_data[0]} points\n"
               f"🔗 Link: https://t.me/{bot_uname}?start={user_id}")
        
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Withdraw", "Balance")
        bot.send_message(message.chat.id, msg, reply_markup=markup)
    else:
        btn = telebot.types.InlineKeyboardMarkup()
        btn.add(telebot.types.InlineKeyboardButton("Channel 1 🚀", url="https://t.me/techearning0070"))
        btn.add(telebot.types.InlineKeyboardButton("Channel 2 🚀", url="https://t.me/TechEarning00709"))
        bot.send_message(message.chat.id, "❌ Join both channels to use bot!", reply_markup=btn)

@bot.message_handler(func=lambda m: m.text == "Balance")
def bal(message):
    user = get_user(str(message.from_user.id))
    if user:
        bot.send_message(message.chat.id, f"💰 Balance: {user[0]} points")

@bot.message_handler(func=lambda m: m.text == "Withdraw")
def withdraw_request(message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    if user and user[0] >= MIN_WITHDRAW:
        msg = bot.send_message(message.chat.id, "💳 Apna UPI/Paytm number bhejein:")
        bot.register_next_step_handler(msg, process_withdrawal)
    else:
        bot.send_message(message.chat.id, f"⚠️ Kam se kam {MIN_WITHDRAW} points chahiye.")

def process_withdrawal(message):
    payment_info = message.text
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    if user:
        amount = user[0]
        admin_msg = (f"🚀 **New Withdraw!**\n\n👤 Name: {message.from_user.first_name}\n🆔 ID: `{user_id}`\n💰 Amount: {amount}\n💳 Info: `{payment_info}`")
        try:
            bot.send_message(ADMIN_ID, admin_msg)
            conn = sqlite3.connect('referral_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, "✅ Request sent to Admin!")
        except:
            bot.send_message(message.chat.id, "❌ Admin error!")

init_db()
bot.polling(none_stop=True)
          
