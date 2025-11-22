import os
import sys
import hashlib
import subprocess
import time
import re
import shutil
import urllib.parse
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# === initial Setup ===
if len(sys.argv) < 4:
    print("The script's directory was not passed.")
    exit(1)

url_file_path = Path(sys.argv[1])
base_name = sys.argv[3]

with open(url_file_path, 'r', encoding='utf-8') as f:
    url = f.readline().strip()
url = re.sub(r'^[\ufeff]+', '', url)  # Removing the BOM from URL if present

venv_root = Path(sys.prefix)
print("venv_root in ObtainHash.py=", venv_root)
output_dir = venv_root / sys.argv[2]
output_dir.mkdir(parents=True, exist_ok=True)
main_dir = output_dir / "main"
main_dir.mkdir(parents=True, exist_ok=True)
assets_dir = output_dir / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)
hashes_dir = output_dir / "hashes"
hashes_dir.mkdir(parents=True, exist_ok=True)
ots_dir = output_dir / "ots"
ots_dir.mkdir(parents=True, exist_ok=True)

html_path = main_dir / f"{base_name}.html"
assets_path = assets_dir / f"{base_name}.har"
fullhtml_path = main_dir / f"{base_name}.full.html"
har_path = main_dir / f"{base_name}.har"
png_path = main_dir / f"{base_name}.png"
harhash_txt_path = hashes_dir / f"{base_name}.harsha256.txt"
onlyharhash_txt_path = hashes_dir / f"{base_name}.onlyharsha256.txt"
hash_txt_path = hashes_dir / f"{base_name}.sha256.txt"
onlyhash_txt_path = hashes_dir / f"{base_name}.onlysha256.txt"
fullhash_txt_path = hashes_dir / f"{base_name}.fullsha256.txt"
onlyfullhash_txt_path = hashes_dir / f"{base_name}.onlyfullsha256.txt"
ots_path = ots_dir / f"{base_name}.sha256.txt.ots"

#  Launching Playwright and setting custom User-Agent
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",  # Avoid detection as automation
            "--no-sandbox",  # Improve compatibility
            "--disable-gpu",  # Disable GPU accelaration
            "--disable-dev-shm-usage", # Prevent /dev/shm issues
        ]
    )

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720},
        java_script_enabled=True,
        record_har_path=assets_path,
        record_har_content="attach",  # Include both request and response bodies
        locale="ja-JP",
        timezone_id="Asia/Tokyo",
    )

    # avoid automation detection：prevent WebDriver fingerprinting
    context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """)

    page = context.new_page()
    try:
        page.goto(url, wait_until="networkidle", timeout=10000)
    except PlaywrightTimeoutError:
        print("Timeout while loading pages. Continuing execution if the page is already visible.")


    # Save PNG
    # Capture screenshot after scrolling to the bottom of the page
    page.evaluate("""
        (() => {
            return new Promise(resolve => {
                window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                setTimeout(resolve, 3000);  //  Wait for scrolling animation to finish
            });
        })();
    """)

#    time.sleep(2)
    page.screenshot(path=png_path, full_page=True)

    # Save HTML
    # Ensure compatibility with multi-encoding cases
    html_content = page.content()
    
    # Normalize charset to  UTF-8 (e.g., convert from EUC-JP)
    html_content = re.sub(
        r'(<meta[^>]+charset=)[^"\'>]+',
        r'\1"UTF-8"',
        html_content,
        flags=re.IGNORECASE | re.MULTILINE
    )

    # Save the HTML content with UTF-8 encoding
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    if not html_content.strip().lower().endswith("</html>"):
        print("Missing </html> at the end. The HTML might not have been saved properly.")

    # Finalize HAR file saving (trigger internal flush)
    context.close()  
    browser.close()

    # Move the saved HAR file to the HAR directory
    try:
        shutil.move(assets_path, har_path)
    except Exception as e:
        print(f"Failed to move HAR file: {e}")

# Generate SHA-256 hash of HAR file
with open(har_path, "rb") as f:
    hash_value = hashlib.sha256(f.read()).hexdigest()

# Get the creation timestamp of the HAR file
harstat = os.stat(har_path)
harcreated_at = datetime.fromtimestamp(harstat.st_ctime).isoformat()

# Write a detailed report containing the SHA-256 Hash of HAR
with open(harhash_txt_path, "w", encoding="utf-8") as f:
    f.write(f"# File Information\n")
    f.write(f"URL: {url}\n")
    f.write(f"Capture Time: {harcreated_at}\n")
    f.write(f"File Name: {os.path.basename(har_path)}\n\n")
    f.write(f"# SHA-256 Hash\n")
    f.write(f"SHA256 ({os.path.basename(har_path)}) = {hash_value}\n")

# Creating a file with only the SHA-256 hash of HAR
with open(onlyharhash_txt_path, "w", encoding="utf-8") as f:
    f.write(hash_value + "\n")

# Generate the SHA-256 hash of HTML file
with open(html_path, "rb") as f:
    hash_val = hashlib.sha256(f.read()).hexdigest()

# Get the creation timestamp of the HTML file
htmlstat = os.stat(html_path)
htmlcreated_at = datetime.fromtimestamp(htmlstat.st_ctime).isoformat()

# Write a detailed report containing the SHA-256 Hash of HTML
with open(hash_txt_path, "w", encoding="utf-8") as f:
    f.write(f"# File Information\n")
    f.write(f"URL: {url}\n")
    f.write(f"Capture Time: {htmlcreated_at}\n")
    f.write(f"File Name: {os.path.basename(html_path)}\n\n")
    f.write(f"# SHA-256 Hash\n")
    f.write(f"SHA256 ({os.path.basename(html_path)}) = {hash_val}\n")

# Creating a file with only the SHA-256 hash (used for OTS timestamp)
with open(onlyhash_txt_path, "w", encoding="utf-8") as f:
    f.write(hash_val + "\n")

# Generate OTS timestamp
result = subprocess.run(["ots", "stamp", harhash_txt_path])
if result.returncode != 0:
    print("Failed to obtain OTS timestamp for:", harhash_txt_path)

result = subprocess.run(["ots", "stamp", onlyharhash_txt_path])
if result.returncode != 0:
    print("Failed to obtain OTS timestamp for:", onlyharhash_txt_path)

result = subprocess.run(["ots", "stamp", hash_txt_path])
if result.returncode != 0:
    print("Failed to obtain OTS timestamp for:", hash_txt_path)

result = subprocess.run(["ots", "stamp", onlyhash_txt_path])
if result.returncode != 0:
    print("Failed to obtain OTS timestamp for:", onlyhash_txt_path)

# Move the generated OTS file to the designated directory
if os.path.exists(f"{harhash_txt_path}.ots"):
    shutil.move(f"{harhash_txt_path}.ots", os.path.join(ots_dir, os.path.basename(harhash_txt_path) + ".ots"))

if os.path.exists(f"{onlyharhash_txt_path}.ots"):
    shutil.move(f"{onlyharhash_txt_path}.ots", os.path.join(ots_dir, os.path.basename(onlyharhash_txt_path) + ".ots"))

if os.path.exists(f"{hash_txt_path}.ots"):
    shutil.move(f"{hash_txt_path}.ots", os.path.join(ots_dir, os.path.basename(hash_txt_path) + ".ots"))

if os.path.exists(f"{onlyhash_txt_path}.ots"):
    shutil.move(f"{onlyhash_txt_path}.ots", os.path.join(ots_dir, os.path.basename(onlyhash_txt_path) + ".ots"))

print("\n Successfully saved PNG, HTML, HAR, SHA-256 hash, and OTS timestamp files.")

