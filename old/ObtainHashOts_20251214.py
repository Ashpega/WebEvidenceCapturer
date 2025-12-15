import os
import sys
import hashlib
import subprocess
import time
import re
import shutil
import urllib.parse
import locale
import tzlocal
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

def wait_for_file(path, timeout=120):    # Wait until a file exists.
    p = Path(path)
    start = time.time()

    while not p.exists():
        if time.time() - start > timeout:
            raise RuntimeError(f"Timeout: {path} did not appear within {timeout} seconds.")
        time.sleep(0.5)

    return p

def stamp_and_move(file_path, ots_dir):
    result = subprocess.run(["ots", "stamp", file_path])
    if result.returncode != 0:
        sys.stderr.write(f"Failed to obtain OTS timestamp for: {file_path}\n") 
    else:
        ots_path = Path(str(file_path) + ".ots")
        if ots_path.exists():
            shutil.move(ots_path, ots_dir / ots_path.name)
            
# === initial Setup ===
if len(sys.argv) < 4:
    print("The script's directory was not passed.")
    exit(1)

url_file_path = Path(sys.argv[1])
scriptDLfolder = url_file_path.parent
fullhtml_path_txt = scriptDLfolder / "wslScriptFullHtmlPath.txt"
base_name = sys.argv[3]

with open(url_file_path, 'r', encoding='utf-8') as f:
    url = f.readline().strip()
url = re.sub(r'^[\ufeff]+', '', url)  # Removing the BOM from URL if present

venv_root = Path(sys.prefix)
print("venv_root in OpenChromium.py =", venv_root)
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
fullhtml_ots_path = fullhash_txt_path.with_name(fullhash_txt_path.name + ".ots")
onlyfullhtml_ots_path = onlyfullhash_txt_path.with_name(onlyfullhash_txt_path.name + ".ots")
ots_path = ots_dir / f"{base_name}.sha256.txt.ots"

#  Launching Playwright and setting custom User-Agent
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    har_context = browser.new_context(
        record_har_path=assets_path,
        record_har_content="attach",  # Include both request and response bodies
    )
    page = har_context.new_page()
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
    
    # Normalize charset to  UTF-8 (e.g., convert from EUC-JP
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

# Generate OTS timestamp for HTML and move it to the ots directory
stamp_and_move(hash_txt_path, ots_dir)
stamp_and_move(onlyhash_txt_path, ots_dir)
    
# Wait for FullHTML path file
print("Waiting for FullHTML path file...")
file_path = wait_for_file(fullhtml_path_txt)

print("FullHTML path file detected:", file_path)

# read the content of file (Full path of FullHTML)
with open(file_path, "r", encoding="utf-8") as f:
    fullhtml_path_org = Path(f.read().strip())

print("Detected FullHTML path:", fullhtml_path_org)

fullhtmlpath_name = fullhtml_path_org.name

# Temporarily moving the saved .full.html to WSL
if fullhtml_path_org.exists():
    shutil.move(fullhtml_path_org, fullhtml_path)

# Generating SHA-256 hash of fullHTML
with open(fullhtml_path, "rb") as f:
    fullhash_val = hashlib.sha256(f.read()).hexdigest()

# Getting creation timestamp of fullHTML file
fullhtmlstat = os.stat(fullhtml_path)
fullhtmlcreated_at = datetime.fromtimestamp(fullhtmlstat.st_ctime).isoformat()

# Detailed report including SHA-256 hash
with open(fullhash_txt_path, "w", encoding="utf-8") as f:
    f.write(f"# File Information\n")
    f.write(f"URL: {url}\n")
    f.write(f"Capture Time: {fullhtmlcreated_at}\n")
    f.write(f"File Name: {fullhtml_path.name}\n\n")
    f.write(f"# SHA-256 Hash\n")
    f.write(f"SHA256 ({fullhtml_path.name}) = {fullhash_val}\n")

# Creating a file containing only the SHA-256 Hash (used for OTS timestamp)
with open(onlyfullhash_txt_path, "w", encoding="utf-8") as f:
    f.write(fullhash_val + "\n")

# Generate OTS timestamp for Full HTML and move it to the ots directory
stamp_and_move(fullhash_txt_path, ots_dir)
stamp_and_move(onlyfullhash_txt_path, ots_dir)

# Finalize HAR file saving (trigger internal flush)
# Finalize HAR (flush & save)
har_context.close()  
# Close the Chromium instance
browser.close()

# wait for HAR creation
for i in range(10):
    if assets_path.exists():
        break
    time.sleep(0.5)
else:
    raise RuntimeError("HAR file not found after waiting.")

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

# Generate OTS timestamp for HAR and move it to the ots directory
stamp_and_move(harhash_txt_path, ots_dir)
stamp_and_move(onlyharhash_txt_path, ots_dir)

# Moving the output directory to the Downloads folder
if output_dir.exists():
    shutil.move(output_dir, scriptDLfolder)

# output success text
Path(scriptDLfolder / "success.txt").write_text("")

