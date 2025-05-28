import time
import subprocess
import requests
import webbrowser
import os
import tempfile
import shutil
import sys
from windows_toasts import Toast, WindowsToaster

# === CONFIGURATION ===
SERVER_HOST = "localhost:15608"
SERVER_URL = f"http://{SERVER_HOST}/versions"
VERSION_DETAIL_URL = f"http://{SERVER_HOST}/version/"
CHECK_INTERVAL_SECONDS = 60
KNOWN_VERSIONS_FILE = "known_versions.txt"

toaster = WindowsToaster("Minecraft Version Watcher")

def extract_node_bundle():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    server_src = os.path.join(base_path, "server")
    temp_dir = os.path.join(tempfile.gettempdir(), "mcversion_temp")
    server_dst = os.path.join(temp_dir, "server")

    if os.path.exists(server_dst):
        shutil.rmtree(server_dst)
    shutil.copytree(server_src, server_dst)

    return os.path.join(server_dst, "server.js")

def start_node_server():
    try:
        node_script = extract_node_bundle()
        print("[*] Starting Node.js server...")
        subprocess.Popen(
            ["node", node_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(3)
        print("[+] Node.js server started.")
    except Exception as e:
        print(f"[!] Failed to start Node.js server: {e}")

def fetch_versions():
    try:
        response = requests.get(SERVER_URL)
        response.raise_for_status()
        return set(response.json())
    except Exception as e:
        print(f"[!] Failed to fetch versions: {e}")
        return set()

def load_known_versions():
    if not os.path.exists(KNOWN_VERSIONS_FILE):
        print("[*] known_versions.txt not found. Initializing with current versions...")
        current_versions = fetch_versions()
        with open(KNOWN_VERSIONS_FILE, "w") as f:
            for version in sorted(current_versions):
                f.write(version + "\n")
        print("[+] Initialized known versions file.")
        return current_versions

    with open(KNOWN_VERSIONS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_new_versions(new_versions):
    with open(KNOWN_VERSIONS_FILE, "a") as f:
        for version in sorted(new_versions):
            f.write(version + "\n")

def handle_click(version):
    try:
        detail_url = f"{VERSION_DETAIL_URL}{version}"
        response = requests.get(detail_url)
        response.raise_for_status()
        data = response.json()

        vtype = data.get("type", "release")
        formatted_version = version.replace(".", "-")

        if vtype == "release":
            article_url = f"https://www.minecraft.net/en-us/article/minecraft-java-edition-{formatted_version}"
        else:
            article_url = f"https://www.minecraft.net/en-us/article/minecraft-snapshot-{version}"

        webbrowser.open(article_url)
    except Exception as e:
        print(f"[!] Failed to fetch or open article for version {version}: {e}")

def notify_new_versions(new_versions):
    for version in sorted(new_versions):
        print(f"[+] New version found: {version}")
        toast = Toast()
        toast.text_fields = [f"New Minecraft version: {version}"]
        toast.on_activated = lambda _: handle_click(version)
        toaster.show_toast(toast)

def main():
    start_node_server()
    known_versions = load_known_versions()

    print("[*] Watching for new versions. Currently known:")
    for version in sorted(known_versions):
        print(" -", version)

    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)
        current_versions = fetch_versions()
        new_versions = current_versions - known_versions
        if new_versions:
            notify_new_versions(new_versions)
            save_new_versions(new_versions)
            known_versions.update(new_versions)

if __name__ == "__main__":
    main()
