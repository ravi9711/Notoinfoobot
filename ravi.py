import os
import telebot
import requests
import json
import re
import time
from telebot.apihelper import ApiTelegramException
from telebot import types 

# ---------- CONFIGURATION ----------
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8012608728:AAHReNPPs79VVIaT56e_VlqtXelSzjgBg7k"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# API Configuration
API_URL_MOBILE = "https://subhxmouktik-number-api.onrender.com/api"
API_KEY_MOBILE = "SPARK"
API_URL_VEHICLE = "https://vehicke-info.vercel.app/" 
API_URL_AADHAR = "http://osintx.info/API/krobetahack.php"
API_KEY_AADHAR = "SHAD0WINT3L"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Group/Channel Details
PRIMARY_JOIN_LINK = "https://t.me/+l1DfWFUEJI1jYjEx"
CHANNEL_1_USERNAME = "@TgUnknowncoder" 
CHANNEL_2_LINK = "https://t.me/+ptJB4Xxi4ZIwMmZl" 
PRIVATE_CHANNEL_ID = -1001939119074 # MUST BE CORRECT ID AND BOT MUST BE ADMIN
CHANNELS_TO_CHECK = [CHANNEL_1_USERNAME, PRIVATE_CHANNEL_ID] 

# Media URLs
START_VIDEO_URL = "https://files.catbox.moe/1owxai.png" 
WELCOME_LEAVE_PHOTO_URL = "https://files.catbox.moe/1owxai.png"

MAX_CHUNK = 3800
user_ids = set() 
# ----------------------------------------------------


# ---------- HELPER FUNCTIONS ----------

def safe_send(chat_id, text, photo=None, reply_to=None, reply_markup=None):
    """Sends text or photo messages safely, handling errors and chunking."""
    try:
        if photo:
            return bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_to_message_id=reply_to,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        elif len(text) <= MAX_CHUNK:
            return bot.send_message(chat_id, text, reply_to_message_id=reply_to, reply_markup=reply_markup, parse_mode="HTML")
        else:
            # Chunking logic for long messages (text only)
            cur = ""
            for line in text.splitlines(True):
                if len(cur) + len(line) > MAX_CHUNK:
                    bot.send_message(chat_id, cur, parse_mode="HTML")
                    time.sleep(0.12)
                    cur = line
                else:
                    cur += line
            if cur:
                return bot.send_message(chat_id, cur, parse_mode="HTML")
            return None

    except ApiTelegramException as e:
        if 'bot was blocked by the user' in str(e):
            print(f"INFO: Blocked user {chat_id} skipped in safe_send.")
        else:
            print(f"ERROR in safe_send for {chat_id}: {e}")
        return None

def pretty_json(obj):
    """Safely converts an object to a pretty-printed JSON string."""
    try: return json.dumps(obj, ensure_ascii=False, indent=2)
    except: return str(obj)

def last_10_digits(text):
    """Extracts the last 10 digits from a string."""
    digits = re.sub(r'\D', '', text)
    return digits[-10:] if len(digits) >= 10 else digits

def clean_vehicle_number(text):
    """Cleans a vehicle number by removing spaces/dashes and converting to uppercase."""
    return re.sub(r'[\s-]', '', text).upper()

def check_membership(user_id, channels):
    """Checks if a user is a member of ALL required channels."""
    for channel in channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked', 'banned']: 
                return False
        except ApiTelegramException as e:
            # CRITICAL: This usually means bot is not admin or channel ID is wrong.
            print(f"CRITICAL ERROR in check_membership for {user_id} in {channel}: {e}")
            return False 
        except Exception as e:
            print(f"Unexpected error in check_membership: {e}")
            return False
    return True

# ---------- API LOOKUP FUNCTIONS (No changes here) ----------

def run_api_lookup_mobile(m, mobile):
    """Handles the mobile number API call."""
    chat_id = m.chat.id
    safe_send(chat_id, "searching....")

    params = {"key": API_KEY_MOBILE, "number": mobile}

    try:
        resp = requests.get(API_URL_MOBILE, params=params, headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException as e:
        safe_send(chat_id, f"❌ Request failed for {mobile}.")
        return

    if resp.status_code != 200:
        safe_send(chat_id, f"🚫 Information not available for {mobile}.")
        return

    # Process and format data 
    try:
        # Check for API Shutdown message first
        if 'Invalid or inactive API key' in resp.text:
            safe_send(chat_id, "⚠️ **Service Shutdown** ⚠️\nThe bot's lookup service is temporarily unavailable. Contact @ox1_spark.")
            return

        text_data = resp.text.replace("by anish", "by @ox1_spark")
        
        try:
            data = json.loads(text_data)
            if "owner" in data: del data["owner"]
            data["channel"] = "https://t.me/TgUnknowncoder"
            data["credit"] = "by the crime coder spark" 
            pretty = pretty_json(data)
            
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            text_data = re.sub(r'"owner"\s*:\s*".*?"[,}]', '', text_data)
            pretty = text_data.strip() + '\n\nChannel: https://t.me/TgUnknowncoder\nCredit: by the crime coder spark'
            
        safe_send(chat_id, "<pre>" + pretty[:3500] + "</pre>")

    except Exception as e:
        print(f"Mobile parsing error: {e}")
        safe_send(chat_id, f"⚠️ Parsing error occurred.")

def run_api_lookup_vehicle(m, rc_number):
    """Handles the vehicle number API call."""
    chat_id = m.chat.id
    safe_send(chat_id, "searching....")

    params = {"rc_number": rc_number}

    try:
        resp = requests.get(API_URL_VEHICLE, params=params, headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException:
        safe_send(chat_id, f"❌ Request failed for {rc_number}.")
        return

    if resp.status_code != 200:
        safe_send(chat_id, f"🚫 Information not available for {rc_number}.")
        return

    try:
        data = resp.json()
        
        api_credit = data.pop("credit", None) 
        api_status = data.pop("status", "failed")
        details = data.pop("details", {})

        info_message = f"Could not find vehicle details for {rc_number}. Please check the number."
        
        if api_status == "success" and details:
            info_message = "\n".join([f"{k}: {v}" for k, v in details.items()])
            
            unwanted_credit = "@urSTARKz"
            if unwanted_credit in info_message:
                    info_message = "\n".join([line for line in info_message.split('\n') 
                                             if unwanted_credit not in line])


        final_result = {
            "success": True,
            "result": {"success": True, "result": {"message": info_message}},
            "channel": "https://t.me/TgUnknowncoder",
            "credit": "by the crime coder spark"
        }

        pretty_output = pretty_json(final_result)
        safe_send(chat_id, "<pre>" + pretty_output[:3500] + "</pre>")

    except Exception as e:
        print(f"Vehicle parsing error: {e}")
        safe_send(chat_id, f"⚠️ Parsing error occurred.")

def run_api_lookup_aadhar(m, aadhar_id):
    """Handles the Aadhaar ID API call."""
    chat_id = m.chat.id
    safe_send(chat_id, "searching....")

    params = {"key": API_KEY_AADHAR, "type": "id_number", "term": aadhar_id}

    try:
        resp = requests.get(API_URL_AADHAR, params=params, headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException:
        safe_send(chat_id, f"❌ Request failed for {aadhar_id}.")
        return

    if resp.status_code == 400:
        safe_send(chat_id, "🚫 Aadhar no. is invalid")
        return
    
    if resp.status_code != 200:
        safe_send(chat_id, f"🚫 Information not available for {aadhar_id}.")
        return

    try:
        data = resp.json()
        info_message = ""
        unwanted_credit_line = "\n\nAPI Credit: API DEVELOPER : @krobeta"
        
        if isinstance(data, dict):
            if data.get('message') and ('no records found' in data['message'].lower() or 'not found' in data['message'].lower()):
                info_message = "No records found"
            elif 'error' in data:
                 info_message = f"Lookup Error: {data['error']}"
            else:
                info_message = "\n".join([f"{k}: {v}" for k, v in data.items()])
                if info_message.endswith(unwanted_credit_line):
                    info_message = info_message[:-len(unwanted_credit_line)].strip()
        
        else:
              response_text = str(data)
              if 'no records found' in response_text.lower() or 'not found' in response_text.lower():
                  info_message = "No records found"
              else:
                  if response_text.endswith(unwanted_credit_line):
                       info_message = response_text[:-len(unwanted_credit_line)].strip()
                  else:
                       info_message = response_text.strip()
        
        final_result = {
            "success": True,
            "result": {"success": True, "result": {"message": info_message}}, 
            "channel": "https://t.me/TgUnknowncoder",
            "credit": "by the crime coder spark"
        }

        pretty_output = pretty_json(final_result)
        safe_send(chat_id, "<pre>" + pretty_output[:3500] + "</pre>")

    except Exception as e:
        print(f"Aadhar parsing error: {e}")
        safe_send(chat_id, f"⚠️ Parsing error occurred.")

# ---------- HANDLERS: WELCOME & LEAVE (MODIFIED) ----------

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(m):
    """Handles new member joining the group/channel."""
    chat_id = m.chat.id
    if m.chat.type in ["group", "supergroup"]:
        for user in m.new_chat_members:
            if user.id == bot.user.id:
                # Ignore if the bot itself is being added
                continue 

            # Create user mention
            user_mention = f"<a href='tg://user?id={user.id}'>{user.first_name or user.username}</a>"
            
            # Use the new welcome text
            welcome_text = (
                f"[ 🫶🏻 ]┘\n"
                f"╰┈➤ 𝐇𝐞𝐲 !~ {user_mention} Welcome 🐼🫶🏻\n\n"
                "WELCOME TO OUR COMMUNITY ❤️‍🩹\n\n"
                "I’m SPARK ⚡ — the bot owner/assistant here\n"
                "❤️‍🩹!~WELCOME ❤️‍🩹\n"
                "These are my commands;\n"
                "**/num** - 🔢 Type a 10-digit number, example: `/num 927374XXXX`\n"
                "**/aadhar** - 🆔 Type a 12-digit Aadhaar number, example: `/aadhar 62837444XXXX`\n"
                "**/vehicle** - 🚗 Type a vehicle number, example: `/vehicle MHXXXXX`\n"
                "🎮 IF YOU HAVE ANY PROBLEM\n\n"
                "MESSAGE DEV :-)\n"
                "╰┈➤ 🆔 @ox1_spark\n\n"
                "╰┈➤ JOIN FOR MORE: @TgUnknowncoder"
            )
            
            safe_send(chat_id, welcome_text, photo=WELCOME_LEAVE_PHOTO_URL)
            

@bot.message_handler(content_types=['left_chat_member'])
def handle_left_member(m):
    """Handles member leaving the group/channel."""
    chat_id = m.chat.id
    user = m.left_chat_member

    if user.id == bot.user.id:
        print(f"INFO: Bot removed from group {chat_id}.")
        return

    leave_text = (
        f"└[ 🖤⚡ ]┘\n"
        f"╰┈➤ 𝐖𝐡𝐚𝐭’𝐬 𝐮𝐩! **{user.first_name}** just left the group 😎\n"
        "╰┈➤ They tried, but the vibe here was too strong to handle 💥🔥\n\n"
        "🚪 𝐓𝐡𝐞𝐲 walked out… but legends never really leave 💀✨\n"
        "╰┈➤ 𝐓𝐡𝐞 𝐦𝐞𝐦𝐞𝐬, 𝐭𝐡𝐞 𝐡𝐞𝐚𝐭, 𝐚𝐧𝐝 𝐭𝐡𝐞 𝐡𝐨𝐨𝐭𝐬 𝐬𝐭𝐚𝐲 𝐛𝐚𝐜𝐤 👀⚡\n\n"
        "🎮 𝐈f 𝐲𝐨𝐮 𝐜𝐚𝐧't 𝐡𝐚𝐧𝐝𝐥𝐞 𝐭𝐡𝐢𝐬 𝐯𝐢𝐛𝐞, 𝐭𝐡𝐞𝐧 𝐰𝐚𝐥𝐤 𝐨𝐮𝐭… 𝐛𝐮𝐭 𝐰𝐞 𝐤𝐧𝐨𝐰 𝐲𝐨𝐮 𝐰𝐢𝐥𝐥 𝐛𝐞 𝐦𝐢𝐬𝐬𝐞𝐝 ❤️‍🔥\n\n"
        "╰┈➤ 🆔 @ox1_spark\n"
        "╰┈➤ JOIN FOR MORE @TgUnknowncoder"
    )
    
    safe_send(chat_id, leave_text, photo=WELCOME_LEAVE_PHOTO_URL)


# ---------- HANDLERS: COMMANDS (FINAL MODIFICATIONS) ----------

@bot.message_handler(commands=['start', 'help'])
def cmd_start(m):
    chat_id = m.chat.id
    
    # Text for both private chat and group /start
    start_text_template = (
        f"[ 🫶🏻 ]┘\n"
        f"╰┈➤ 𝐇𝐞𝐲 !~ Welcome 🐼🫶🏻\n\n"
        "I’m SPARK ⚡ — the bot owner/assistant here\n"
        "❤️‍🩹!~WELCOME ❤️‍🩹\n"
        "These are my commands;\n"
        "**/num** - 🔢 Type a 10-digit number, example: `/num 927374XXXX`\n"
        "**/aadhar** - 🆔 Type a 12-digit Aadhaar number, example: `/aadhar 62837444XXXX`\n"
        "**/vehicle** - 🚗 Type a vehicle number, example: `/vehicle MHXXXXX`\n"
        "🎮 IF YOU HAVE ANY PROBLEM\n\n"
        "MESSAGE DEV :-)\n"
        "╰┈➤ 🆔 @ox1_spark\n\n"
        "╰┈➤ JOIN FOR MORE: @TgUnknowncoder"
    )
    
    if m.chat.type == "private":
        # Get bot's username (needed for 'Add to Group' link)
        bot_info = bot.get_me()
        bot_username = bot_info.username
        
        # Customize private message part
        # Insert "THANKS FOR USING ME" after the welcome line
        private_caption = start_text_template.replace(
            "Welcome 🐼🫶🏻\n\n", 
            "Welcome 🐼🫶🏻\n\nTHANKS FOR USING ME ❤️‍🩹\n\n"
        )
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        join_button = types.InlineKeyboardButton("➡️ Use me Here", url=PRIMARY_JOIN_LINK)
        
        # Add to Group link
        add_to_group_link = f"https://t.me/{bot_username}?startgroup=start&admin=can_change_info+can_delete_messages+can_invite_users+can_restrict_members+can_pin_messages+can_promote_members"
        add_button = types.InlineKeyboardButton("➕ Add me to your Group", url=add_to_group_link)
        
        keyboard.add(join_button, add_button)

        # Send photo with buttons
        safe_send(chat_id, private_caption, photo=WELCOME_LEAVE_PHOTO_URL, reply_markup=keyboard)
    
    elif m.chat.type in ["group", "supergroup"]:
        
        # ⚠️ Group Command Fix: Check if the command includes the bot's username
        # Get bot's username dynamically to check against the message text
        bot_info = bot.get_me()
        bot_username = bot_info.username.lower()

        # Check if the message contains the exact command: /start OR /start@bot_username
        command_text = m.text.lower().split()[0] # e.g., /start or /start@mybot
        
        # We only proceed if command is /start@{username} or if it is just /start (to be safe in smaller groups)
        # However, to strictly follow your request: "jabhi vo text bhje tb koi banda /start@bot ka username lgaye sath"
        # We will check if it contains the bot's username or if it is the /help command (which usually works without username)
        
        if command_text == '/start' and m.text.find('@') == -1 and command_text != '/help':
            # Ignore plain /start to prevent spam in large groups
            return
            
        if command_text == '/start' or command_text == f'/start@{bot_username}' or command_text == '/help':
            
            # Customize group message part
            # Insert "WELCOME TO OUR COMMUNITY" after the welcome line
            group_caption = start_text_template.replace(
                "Welcome 🐼🫶🏻\n\n", 
                "Welcome 🐼🫶🏻\n\nWELCOME TO OUR COMMUNITY ❤️‍🩹\n\n"
            )

            safe_send(chat_id, group_caption)


@bot.message_handler(commands=['num'])
def cmd_num_lookup(m):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.chat.type == "private": return cmd_start(m)

    command_parts = m.text.split(maxsplit=1)
    if len(command_parts) < 2:
        return safe_send(chat_id, "⚠️ Usage: `/num 10-digit number`\nExample: `/num 9319163057`", reply_to=m.message_id)

    mobile = last_10_digits(command_parts[1].strip())
    
    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return safe_send(chat_id, f"@{m.from_user.username or m.from_user.first_name}, ⚠️ Please send a valid 10-digit mobile number.", reply_to=m.message_id)

    if check_membership(user_id, CHANNELS_TO_CHECK):
        run_api_lookup_mobile(m, mobile)
    else:
        send_verification_message(m)


@bot.message_handler(commands=['vehicle']) 
def cmd_vehicle_lookup(m):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.chat.type == "private": return cmd_start(m)

    command_parts = m.text.split(maxsplit=1)
    if len(command_parts) < 2:
        return safe_send(chat_id, "⚠️ Usage: `/vehicle <RC number>`\nExample: `/vehicle MH12AB1234`", reply_to=m.message_id)

    rc_number = clean_vehicle_number(command_parts[1].strip())

    if not rc_number or len(rc_number) < 4:
        return safe_send(chat_id, f"@{m.from_user.username or m.from_user.first_name}, ⚠️ Please send a valid vehicle number (e.g., MH12AB1234).", reply_to=m.message_id)

    if check_membership(user_id, CHANNELS_TO_CHECK):
        run_api_lookup_vehicle(m, rc_number)
    else:
        send_verification_message(m)


@bot.message_handler(commands=['aadhar'])
def cmd_aadhar_lookup(m):
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.chat.type == "private": return cmd_start(m)

    command_parts = m.text.split(maxsplit=1)
    if len(command_parts) < 2:
        return safe_send(chat_id, "⚠️ Usage: `/aadhar <ID number>`\nExample: `/aadhar 284495408590`", reply_to=m.message_id)

    aadhar_id = command_parts[1].strip()

    if not aadhar_id.isdigit() or len(aadhar_id) < 10:
        return safe_send(chat_id, f"@{m.from_user.username or m.from_user.first_name}, ⚠️ Please send a valid ID number (only digits, 10 or more).", reply_to=m.message_id)

    if check_membership(user_id, CHANNELS_TO_CHECK):
        run_api_lookup_aadhar(m, aadhar_id)
    else:
        send_verification_message(m)


def send_verification_message(m):
    """Sends the standard membership verification message."""
    chat_id = m.chat.id
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn_channel_1 = types.InlineKeyboardButton(f"➡️ Join {CHANNEL_1_USERNAME}", url=f"https://t.me/{CHANNEL_1_USERNAME.strip('@')}")
    btn_channel_2 = types.InlineKeyboardButton("➡️ Join Our Channel 2", url=CHANNEL_2_LINK)
    keyboard.add(btn_channel_1, btn_channel_2)

    reply_text_verification = (
        f"Hey, **@{m.from_user.username or m.from_user.first_name}**!\n\n"
        "🚫 **Access Denied:** To use this bot for lookup, you must join our channels. "
        "Please join them and try the command again."
    )
    
    try:
        bot.send_message(
            chat_id=chat_id,
            text=reply_text_verification,
            reply_to_message_id=m.message_id, 
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except ApiTelegramException as e:
        print(f"ERROR sending verification message in group {chat_id}: {e}")
        

# ---------- RUN BOT ----------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    print(f"⚠️ IMPORTANT: Bot must be an ADMIN in the channels: {CHANNELS_TO_CHECK} to check membership!")
    while True:
        try:
            # Use skip_pending=True to clear old 409 errors upon startup
            bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
        except Exception as e:
            print(f"Main polling loop error: {e}. Restarting in 5 seconds...")
            time.sleep(5)