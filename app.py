import sys
import subprocess

# A dictionary of required packages, mapping the import name to the pip package name.
# This is useful for packages like 'yaml' which is installed via 'PyYAML'.
REQUIRED_PACKAGES = {
    'requests': 'requests',
    'yaml': 'PyYAML',
    'qrcode': 'qrcode'
}

print("--- Checking for required packages ---")
all_packages_installed = True

# Dynamically import the '__import__' function to check for modules
from importlib import util

for module_name, package_name in REQUIRED_PACKAGES.items():
    # A more modern way to check if a module can be imported
    if util.find_spec(module_name):
        print(f"✔️  Module '{module_name}' is already installed.")
    else:
        print(f"⚠️  Module '{module_name}' not found. Attempting to install '{package_name}'...")
        all_packages_installed = False
        try:
            # Use sys.executable to ensure pip is for the correct Python environment
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅  Successfully installed '{package_name}'.")
        except subprocess.CalledProcessError as e:
            print(f"❌ ERROR: Failed to install '{package_name}'. {e}")
            print(f"Please install it manually (e.g., 'pip install {package_name}') and re-run the script.")
            sys.exit(1)

if not all_packages_installed:
    print("\n--- All required packages are now installed. Script will now proceed. ---\n")

# --- Standard and Third-Party Library Imports ---
# Now that we've ensured they exist, we can import them.
import requests
import json
import time
import uuid
import os
import yaml
import qrcode
from urllib.parse import urlencode

# --- CONFIGURATION ---

# Telegram Bot Token from BotFather
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_NAME = os.environ.get("TELEGRAM_BOT_NAME")

PANEL_PROTOCOL = os.environ.get("PANEL_PROTOCOL")
PANEL_HOST = os.environ.get("PANEL_HOST")  # Your panel's IP or domain
PANEL_PORT = os.environ.get("PANEL_PORT")
WEB_BASE_PATH = os.environ.get("WEB_BASE_PATH")          # The path after the port, if any. Leave empty "" if none.
PANEL_USERNAME = os.environ.get("PANEL_USERNAME")
PANEL_PASSWORD = os.environ.get("PANEL_PASSWORD")

# Inbound & Server Details
INBOUND_REMARK = os.environ.get("INBOUND_REMARK")
SERVER_IP_OR_DOMAIN = os.environ.get("SERVER_IP_OR_DOMAIN") # The public IP or domain of your server for the config link

# New Client Settings
INITIAL_DATA_LIMIT_GB = os.environ.get("INITIAL_DATA_LIMIT_GB")
INITIAL_VALID_DAYS = os.environ.get("INITIAL_VALID_DAYS")
RENEWAL_DATA_GB = os.environ.get("RENEWAL_DATA_GB")
RENEWAL_DAYS = os.environ.get("RENEWAL_DAYS")

# Data file
DATA_FILE = "data.yaml"

# --- Validate Essential Configuration ---
try:
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")

    TELEGRAM_BOT_NAME = os.environ.get("TELEGRAM_BOT_NAME")
    if not TELEGRAM_BOT_NAME:
        raise ValueError("TELEGRAM_BOT_NAME environment variable not set.")

    PANEL_PROTOCOL = os.environ.get("PANEL_PROTOCOL")
    if not PANEL_PROTOCOL:
        raise ValueError("PANEL_PROTOCOL environment variable not set.")

    PANEL_HOST = os.environ.get("PANEL_HOST")
    if not PANEL_HOST:
        raise ValueError("PANEL_HOST environment variable not set.")

    PANEL_PORT = os.environ.get("PANEL_PORT")
    if not PANEL_PORT:
        raise ValueError("PANEL_PORT environment variable not set.")

    # This one is allowed to be empty, so no check is needed.
    WEB_BASE_PATH = os.environ.get("WEB_BASE_PATH", "")

    PANEL_USERNAME = os.environ.get("PANEL_USERNAME")
    if not PANEL_USERNAME:
        raise ValueError("PANEL_USERNAME environment variable not set.")

    PANEL_PASSWORD = os.environ.get("PANEL_PASSWORD")
    if not PANEL_PASSWORD:
        raise ValueError("PANEL_PASSWORD environment variable not set.")

    INBOUND_REMARK = os.environ.get("INBOUND_REMARK")
    if not INBOUND_REMARK:
        raise ValueError("INBOUND_REMARK environment variable not set.")

    SERVER_IP_OR_DOMAIN = os.environ.get("SERVER_IP_OR_DOMAIN")
    if not SERVER_IP_OR_DOMAIN:
        raise ValueError("SERVER_IP_OR_DOMAIN environment variable not set.")

    INITIAL_DATA_LIMIT_GB = os.environ.get("INITIAL_DATA_LIMIT_GB")
    if not INITIAL_DATA_LIMIT_GB:
        raise ValueError("INITIAL_DATA_LIMIT_GB environment variable not set.")

    INITIAL_VALID_DAYS = os.environ.get("INITIAL_VALID_DAYS")
    if not INITIAL_VALID_DAYS:
        raise ValueError("INITIAL_VALID_DAYS environment variable not set.")

    RENEWAL_DATA_GB = os.environ.get("RENEWAL_DATA_GB")
    if not RENEWAL_DATA_GB:
        raise ValueError("RENEWAL_DATA_GB environment variable not set.")

    RENEWAL_DAYS = os.environ.get("RENEWAL_DAYS")
    if not RENEWAL_DAYS:
        raise ValueError("RENEWAL_DAYS environment variable not set.")

except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)

# --- END OF CONFIGURATION ---



# Suppress InsecureRequestWarning for self-signed certificates
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# --- Global Variables ---
panel_session = requests.Session()
inbound_details_cache = {}


# --- URL BUILDER HELPER ---
def build_api_url(endpoint):
    base_path = WEB_BASE_PATH.strip('/')
    endpoint = endpoint.strip('/')
    full_path = f"/{base_path}/{endpoint}" if base_path else f"/{endpoint}"
    return f"{PANEL_PROTOCOL}://{PANEL_HOST}:{PANEL_PORT}{full_path}"


# --- YAML Data Handling ---
def load_user_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, 'r') as f: return yaml.safe_load(f) or {}

def save_user_data(data):
    with open(DATA_FILE, 'w') as f: yaml.dump(data, f, indent=2)


# --- 3X-UI API HELPERS ---
def login_and_get_inbound():
    global inbound_details_cache
    if inbound_details_cache: return inbound_details_cache
    try:
        r = panel_session.post(build_api_url('/login'), data={'username': PANEL_USERNAME, 'password': PANEL_PASSWORD}, timeout=5, verify=False)
        if not r.json().get('success'):
            print("Error: 3x-ui login failed.")
            return None
        r = panel_session.get(build_api_url('/panel/api/inbounds/list'), timeout=5, verify=False)
        for inbound in r.json().get('obj', []):
            if inbound['remark'] == INBOUND_REMARK:
                inbound_details_cache = inbound
                print(f"Successfully fetched details for inbound '{INBOUND_REMARK}'")
                return inbound_details_cache
        print(f"Error: Inbound with remark '{INBOUND_REMARK}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to 3x-ui panel: {e}")
        return None

def find_client_in_panel(email):
    inbound = login_and_get_inbound()
    if not inbound: return None
    try:
        full_inbound_url = build_api_url(f"/panel/api/inbounds/get/{inbound['id']}")
        r = panel_session.get(full_inbound_url, timeout=5, verify=False)
        settings = json.loads(r.json()['obj']['settings'])
        for client in settings.get('clients', []):
            if client['email'] == email:
                return client
        return None
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError):
        return None

def create_or_update_client(inbound_id, email, client_uuid, total_gb, expiry_days):
    total_bytes = int(total_gb * 1024**3) if total_gb > 0 else 0
    expiry_time = int((time.time() + expiry_days * 86400) * 1000) if expiry_days > 0 else 0
    client_data = {"id": client_uuid, "email": email, "enable": True, "totalGB": total_bytes, "expiryTime": expiry_time, "flow": "", "limitIp": 0, "tgId": "", "subId": "", "reset": 0}
    payload = {"id": inbound_id, "settings": json.dumps({"clients": [client_data]})}
    try:
        r_update = panel_session.post(build_api_url(f'/panel/api/inbounds/updateClient/{client_uuid}'), json=payload, timeout=5, verify=False)
        if r_update.json().get('success'): return True
    except (requests.exceptions.RequestException, json.JSONDecodeError): pass
    try:
        r_add = panel_session.post(build_api_url('/panel/api/inbounds/addClient'), json=payload, timeout=5, verify=False)
        return r_add.json().get('success', False)
    except requests.exceptions.RequestException: return False

def get_client_stats(email):
    try:
        r = panel_session.get(build_api_url(f'/panel/api/inbounds/getClientTraffics/{email}'), timeout=5, verify=False)
        return r.json()['obj'] if r.json().get('success') else None
    except requests.exceptions.RequestException: return None


# --- TELEGRAM API HELPERS ---
def send_telegram_request(method, data=None, files=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        return requests.post(url, data=data, files=files, timeout=20).json()
    except requests.exceptions.RequestException: return None

def send_message(chat_id, text):
    return send_telegram_request('sendMessage', data={'chat_id': chat_id, 'text': text})

def delete_message(chat_id, message_id):
    return send_telegram_request('deleteMessage', data={'chat_id': chat_id, 'message_id': message_id})

def answer_callback_query(query_id, text, show_alert=False):
    payload = {'callback_query_id': query_id, 'text': text}
    if show_alert: payload['show_alert'] = True
    return send_telegram_request('answerCallbackQuery', data=payload)

def format_status_message(stats):
    if not stats: return "Could not retrieve your stats."
    remaining_gb = (stats.get('total', 0) - (stats.get('up', 0) + stats.get('down', 0))) / 1024**3
    data_text = f"Data: `{remaining_gb:.2f} GB` remaining" if stats.get('total', 0) > 0 else "Data: `Unlimited`"
    expiry_time = stats.get('expiryTime', 0) / 1000
    if expiry_time > 0 and (remaining_seconds := expiry_time - time.time()) > 0:
        d,h,m = int(remaining_seconds/86400), int((remaining_seconds%86400)/3600), int((remaining_seconds%3600)/60)
        time_text = f"Expires in: `{d}d {h}h {m}m`"
    else: time_text = "Status: `Expired`" if expiry_time > 0 else "Expires: `Never`"
    return f"---\n{time_text}\n{data_text}"

def send_config_message(chat_id, user_id, client_uuid):
    inbound = login_and_get_inbound()
    stream_settings = json.loads(inbound['streamSettings'])
    reality_settings = stream_settings.get('realitySettings', {})
    params = {'type': stream_settings.get('network', 'tcp'), 'security': stream_settings.get('security', 'reality'), 'sni': reality_settings.get('serverNames', [''])[0], 'fp': reality_settings.get('settings', {}).get('fingerprint', 'chrome'), 'pbk': reality_settings.get('settings', {}).get('publicKey'), 'sid': reality_settings.get('shortIds', [''])[0]}
    if reality_settings.get('settings', {}).get('spiderX'): params['spx'] = reality_settings['settings']['spiderX']
    if stream_settings.get('tcpSettings', {}).get('header', {}).get('type') == 'http':
        params['headerType'] = 'http'
        if isinstance(stream_settings['tcpSettings']['header'].get('request', {}).get('path'), list):
            params['path'] = stream_settings['tcpSettings']['header']['request']['path'][0]
    
    config_name = f"{TELEGRAM_BOT_NAME}-{inbound['remark']}"
    vless_link = f"vless://{client_uuid}@{SERVER_IP_OR_DOMAIN}:{inbound['port']}?{urlencode(params)}#{config_name}"
    
    stats_text = format_status_message(get_client_stats(user_id))
    caption = f"Here is your config. Tap to copy:\n\n`{vless_link}`\n\n{stats_text}"
    
    qr_path = f"qr_{user_id}.png"
    qrcode.make(vless_link).save(qr_path)

    keyboard = {'inline_keyboard': [[{'text': f"⚡️ Boost Account (+{RENEWAL_DAYS}d, +{RENEWAL_DATA_GB}GB)", 'callback_data': 'renew'}], [{'text': "📲 App Guides", 'callback_data': 'howto'}, {'text': "💎 Go PRO", 'callback_data': 'pro'}]]}
    with open(qr_path, 'rb') as photo_file:
        send_telegram_request('sendPhoto', data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(keyboard)}, files={'photo': photo_file})
    os.remove(qr_path)


# --- BOT LOGIC ---
def handle_start(chat_id, user):
    user_id, name, lang = str(user['id']), user['first_name'], user.get('language_code', 'en')
    # send_message(chat_id, f"Welcome, {name}! Please wait, checking your account status...")
    
    all_users = load_user_data()
    user_in_yaml = all_users.get(user_id)
    panel_client = find_client_in_panel(user_id)
    
    if user_in_yaml and not panel_client:
        # send_message(chat_id, "It seems your old account was removed. Creating a new one for you...")
        del all_users[user_id]
        panel_client = None

    if panel_client:
        client_uuid = panel_client['id']
        if not user_in_yaml or user_in_yaml.get('uuid') != client_uuid:
            all_users[user_id] = {'name': name, 'language': lang, 'uuid': client_uuid, 'renewal_log': [f"Recovered on {time.strftime('%Y-%m-%d %H:%M:%S')}"]}
            save_user_data(all_users)
    else:
        client_uuid = str(uuid.uuid4())
        inbound = login_and_get_inbound()
        if not create_or_update_client(inbound['id'], user_id, client_uuid, INITIAL_DATA_LIMIT_GB, INITIAL_VALID_DAYS):
            send_message(chat_id, "Sorry, I couldn't create your account. Please contact an administrator.")
            return
        all_users[user_id] = {'name': name, 'language': lang, 'uuid': client_uuid, 'renewal_log': [f"Created on {time.strftime('%Y-%m-%d %H:%M:%S')}"]}
        save_user_data(all_users)
        
    send_config_message(chat_id, user_id, client_uuid)


def handle_callback(query):
    query_id, user, chat_id, message_id = query['id'], query['from'], query['message']['chat']['id'], query['message']['message_id']
    user_id = str(user['id'])
    data = query['data']

    if data == 'renew':
        all_users = load_user_data()
        user_data = all_users.get(user_id)
        
        # --- NEW ROBUST RECOVERY LOGIC ---
        if not user_data:
            panel_client = find_client_in_panel(user_id)
            if not panel_client:
                return answer_callback_query(query_id, "Your account appears to be deleted. Please use /start to create a new one.", show_alert=True)
            
            # Seamlessly recover the user's data
            user_data = {
                'name': user.get('first_name'), 
                'language': user.get('language_code', 'en'), 
                'uuid': panel_client['id'], 
                'renewal_log': [f"Auto-recovered on {time.strftime('%Y-%m-%d %H:%M:%S')}"]
            }
            all_users[user_id] = user_data
            save_user_data(all_users)
            
        answer_callback_query(query_id, "Renewing your account, please wait...")
        
        stats = get_client_stats(user_id)
        if not (inbound := login_and_get_inbound()) or not stats:
            return send_message(chat_id, "Sorry, there was a problem fetching server data. Please try again.")

        new_total_gb = stats.get('total', 0) / 1024**3 + RENEWAL_DATA_GB
        base_time = max(time.time(), stats.get('expiryTime', 0) / 1000)
        new_expiry_days = (base_time - time.time()) / 86400 + RENEWAL_DAYS
        
        client_uuid = user_data['uuid']
        if not create_or_update_client(inbound['id'], user_id, client_uuid, new_total_gb, new_expiry_days):
            return send_message(chat_id, "Sorry, I failed to update your account.")
        
        user_data['renewal_log'].append(f"Renewed on {time.strftime('%Y-%m-%d %H:%M:%S')}")
        save_user_data(all_users)
        
        delete_message(chat_id, message_id)
        send_config_message(chat_id, user_id, client_uuid)

    elif data == 'howto':
        howto_text = "INSTRUCTIONS:\n\n1. Copy your configuration\n2. Install V2Box app.\n3. OpenV2Box, Go to Configs\n   - Tap +\n   - Import uri from clipboard\n   - Connect\n4. You can also scan the QR code"
        answer_callback_query(query_id, howto_text, show_alert=True)

    elif data == 'pro':
        answer_callback_query(query_id, "This feature is coming soon! Stay tuned for premium options.", show_alert=True)


# --- MAIN BOT LOOP ---
def main():
    print("Bot started...")
    login_and_get_inbound()
    offset = 0
    while True:
        try:
            updates = send_telegram_request('getUpdates', data={'offset': offset, 'timeout': 30})
            if updates and updates.get('ok'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    if 'message' in update and 'text' in update['message'] and update['message']['text'] == '/start':
                        handle_start(update['message']['chat']['id'], update['message']['from'])
                    elif 'callback_query' in update:
                        handle_callback(update['callback_query'])
        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()