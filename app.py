#from flask import Flask, render_template, send_file
from flask import Flask, render_template, request, redirect, url_for, flash
import telebot
import threading
import requests
import random
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === CONFIG ===
BOT_TOKEN = '1537813571:AAHMUX-GOaUY3xiIba1P_hc804ZX13J8o-E'
CHANNEL_ID = -1001813768021
ADMIN_IDS = [1527992708]
BAN_LIST = set()

bot = telebot.TeleBot(BOT_TOKEN)
#app = Flask(__name__)

app = Flask(__name__)
app.secret_key = 'callMeMotherfuvker7777_h03_im_B4D'

USER_STATS = {}

class RapidProxyScanner:
    VERIFICATION_ENDPOINTS = [
        "http://httpbin.org/ip",
        "http://ip-api.com/json",
        "http://api.ipify.org?format=json"
    ]
    PROXY_TIMEOUT = 3
    PROTOCOLS = ['http', 'https', 'socks4', 'socks5']
    MIN_LIVE_PROXIES = 5
    MAX_WORKERS = 50

    def __init__(self):
        self.API_URL = "https://domains.yougetsignal.com/domains.php"
        self.proxy_file = "proxies.txt"
        self.live_proxies = []
        self.session = requests.Session()
        self.session.headers.update({'Connection': 'keep-alive'})
        self.load_proxies()

    def load_proxies(self):
        if not os.path.exists(self.proxy_file):
            self.all_proxies = []
            return
        with open(self.proxy_file) as f:
            self.all_proxies = [line.strip() for line in f if line.strip()]

    def verify_proxy(self, proxy):
        for protocol in self.PROTOCOLS:
            proxy_url = f"{protocol}://{proxy}"
            try:
                response = self.session.get(
                    random.choice(self.VERIFICATION_ENDPOINTS),
                    proxies={'http': proxy_url, 'https': proxy_url},
                    timeout=self.PROXY_TIMEOUT
                )
                if response.status_code == 200:
                    return (proxy, protocol)
            except:
                continue
        return None

    def get_live_proxies(self):
        verified = []
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {executor.submit(self.verify_proxy, proxy): proxy for proxy in self.all_proxies}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    verified.append(f"{result[1]}://{result[0]}")
                    if len(verified) >= self.MIN_LIVE_PROXIES:
                        break
        return verified

    def scan(self, target):
        self.live_proxies = self.get_live_proxies()
        if not self.live_proxies:
            return None
        with ThreadPoolExecutor(max_workers=len(self.live_proxies)) as executor:
            futures = {
                executor.submit(self.make_api_request, target, proxy): proxy for proxy in self.live_proxies
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    return result
        return None

    def make_api_request(self, target, proxy):
        try:
            response = requests.post(
                self.API_URL,
                data={'remoteAddress': target},
                proxies={'http': proxy, 'https': proxy},
                timeout=10,
                headers={'User-Agent': random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Mozilla/5.0 (Linux; Android 10)",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0)"
                ])}
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

@bot.message_handler(commands=['start'])
def welcome(msg):
    if not is_subscriber(msg):
        return
    user_id = msg.from_user.id
    bot.reply_to(msg, f"👋 ***Hi*** , *Welcome To Reverse Scanner*\n            **your ID ** => _{ user_id }_ \n\n``` __Botz By__ => @theboidoingthingz ``` \n\n\n• _Send me a domain or IP to scan._\n",parse_mode="Markdown")

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.id in ADMIN_IDS:
        try:
            uid = int(msg.text.split()[1])
            BAN_LIST.add(uid)
            bot.reply_to(msg, f"🚫 User {uid} banned.")
        except:
            bot.reply_to(msg, "⚠️ Usage: /ban <user_id>")

@bot.message_handler(commands=['unban'])
def unban_user(msg):
    if msg.from_user.id in ADMIN_IDS:
        try:
            uid = int(msg.text.split()[1])
            BAN_LIST.discard(uid)
            bot.reply_to(msg, f"✅ User {uid} unbanned.")
        except:
            bot.reply_to(msg, "⚠️ Usage: /unban <user_id>")

@bot.message_handler(commands=['stats'])
def stats(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    total_users = len(USER_STATS)
    total_scans = sum(USER_STATS.values())
    bot.reply_to(msg, f"📊 Total users: {total_users}\n🔍 Total scans: {total_scans}")

@bot.message_handler(commands=['users'])
def user_list(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    if not USER_STATS:
        bot.reply_to(msg, "📭 No user activity yet.")
    else:
        txt = "\n".join([f"{uid}: {count} scans" for uid, count in USER_STATS.items()])
        bot.reply_to(msg, f"📈 User Stats:\n{txt}")

@bot.message_handler(func=lambda m: True)
def handle_target(msg):
    if msg.from_user.id in BAN_LIST:
        bot.reply_to(msg, "⛔ You are banned.")
        return
    if not is_subscriber(msg):
        return

    target = msg.text.strip()
    user_id = msg.from_user.id

    bot.send_message(msg.chat.id, f"🔎 Scanning `{target}`...", parse_mode="Markdown")
    scanner = RapidProxyScanner()
    result = scanner.scan(target)

    if result and 'domainArray' in result:
        domains = [d[0] for d in result['domainArray'][:5]]
        full_domains = [d[0] for d in result['domainArray']]
        response = f"✅ Found {result['domainCount']} domains:\n" + "\n".join(domains)
        bot.send_message(msg.chat.id, response)

        # Save full list to file
        file_path = f"found_{target}.txt"
        with open(file_path, "w") as f:
            f.write("\n".join(full_domains))
        bot.send_document(msg.chat.id, open(file_path, "rb"))
        os.remove(file_path)

        bot.send_message(CHANNEL_ID, f"📡 Scan: {target}\nDomains: {result['domainCount']}")
        log_result(user_id, target, result['domainCount'])
    else:
        bot.send_message(msg.chat.id, "❌ Proxy error please try again.")

def is_subscriber(msg):
    try:
        status = bot.get_chat_member(CHANNEL_ID, msg.from_user.id).status
        if status not in ['member', 'administrator', 'creator']:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Join Us", url=f"https://t.me/+OlmHhje9XHhlZjM0"))
            bot.send_message(msg.chat.id, "🚫 Join our community to use the bot.", reply_markup=markup)
            return False
        return True
    except:
        bot.send_message(msg.chat.id, "🚫 Verification failed.")
        return False

def log_result(uid, target, count):
    with open("logs.txt", "a") as f:
        f.write(f"{uid}|{target}|{count} domains\n")
    USER_STATS[uid] = USER_STATS.get(uid, 0) + 1

@app.route("/")
def dashboard():
    logs = []
    if os.path.exists("logs.txt"):
        with open("logs.txt") as f:
            logs = f.readlines()

    unique_users = set()
    total_scans = 0
    previous_targets = []

    for line in logs:
        parts = line.strip().split("|")
        if len(parts) >= 3:
            uid, target, count = parts
            unique_users.add(uid)
            total_scans += 1
            previous_targets.append(target)

    return render_template("index.html", logs=logs, users=len(unique_users), scans=total_scans, targets=previous_targets)



@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    code = request.form.get('code')
  #  if code == os.getenv("ADMIN_CLEAR_CODE"):  # Store in .env
    if code == ("Dustbin999"):
        open("logs.txt", "w").close()
        flash("✅ Logs cleared successfully!", "success")
    else:
        flash("❌ Incorrect admin code.", "danger")
    return redirect(url_for('dashboard'))

def run_flask():
    app.run("0.0.0.0", 5000)

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
