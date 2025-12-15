import os
import sys
import hashlib
import time
import re
import shutil
import subprocess
import urllib.parse
import locale
import tzlocal
import tkinter as tk
from tkinter import simpledialog
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

import AutoCloseMsgBox
import CreateBaseName

def stamp_and_move(file_path, ots_dir):
    result = subprocess.run(["ots", "stamp", file_path])
    if result.returncode != 0:
        sys.stderr.write(f"Failed to obtain OTS timestamp for: {file_path}\n") 
    else:
        ots_path = Path(str(file_path) + ".ots")
        if ots_path.exists():
            shutil.move(ots_path, ots_dir / ots_path.name)

def fmt_human(dt):
    return dt.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

# === initial Setup ===
current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
output_dir = f"output_{current_time}"
script_dir = Path(__file__).resolve().parent
print("This python script is in =: ", script_dir)
url_txt_path = script_dir / "tmp_url.txt"

# candidates of PowerShell paths
powershell_paths = [
    r"/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
    r"/mnt/c/Windows/System32/powershell.exe"
]

for path in powershell_paths:
    if os.path.exists(path):
        powershell_path = path
        break
else:
    AutoCloseMsgBox.show_auto_closing_message("PowerShell not found.", 3)
    print("PowerShell not found.")
    sys.exit(1)


# Obtain Windows Downloads folder path
powershell_cmd = (
    "$OutputEncoding = [Console]::OutputEncoding = "
    "[System.Text.UTF8Encoding]::new(); "
    "(New-Object -ComObject Shell.Application)"
    ".NameSpace('shell:Downloads').Self.Path; exit 0"
)

win_path = subprocess.check_output(
    [powershell_path, "-NoProfile", "-Command", powershell_cmd],
    text=True,
).strip()

if not win_path:
    raise RuntimeError("Failed to get Windows Downloads path (empty output).")

wsl_path = subprocess.check_output(
    ["wslpath", win_path],
    text=True
).strip()

DLfolder_path = Path(wsl_path)
print("DLfolder_path=:", DLfolder_path)
    
# Obtain Windows version
result = subprocess.run(
    [powershell_path, "-NoProfile", "-Command",
     "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').CurrentBuild"],
    capture_output=True,
    text=True
)

build = int(result.stdout.strip())
win_ver = "11" if build >= 22000 else "10"

print("windows_version =:", win_ver)

# Ask for input URL according to Windows version
if win_ver.strip() == "11":
    root = tk.Tk()
    root.withdraw()
    url = simpledialog.askstring(
        title="URL Input",
        prompt="Enter the URL you would like to save:"
    )
    root.destroy() # closes and removes the hidden Tk root window
else:
    url = input("Enter URL you would like to save: ")

# Simply check for URL
if not url or not re.match(r'^https?://', url):
    AutoCloseMsgBox.show_auto_closing_message("Please input valid URL.", 3)
    print("This URL is not valid.")
    sys.exit(1)

# output URL to a text file
with open(url_txt_path, "w", encoding="utf-8") as f:
    f.write(url + "\n")

# candidates of chrome paths
chrome_paths = [
    r"/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    r"/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
]

for path in chrome_paths:
    if os.path.exists(path):
        subprocess.Popen([path, url])
        break
else:
    AutoCloseMsgBox.show_auto_closing_message("Chome not found.", 3)
    print("Chrome not found.")
    sys.exit(1)

# Use it as a file name
output_dir_path = script_dir / output_dir
output_dir_path.mkdir(parents=True, exist_ok=True)
main_dir_path = output_dir_path / "main"
main_dir_path.mkdir(parents=True, exist_ok=True)
workspace_dir_path = output_dir_path / "workspace"
workspace_dir_path.mkdir(parents=True, exist_ok=True)
hashes_dir_path = output_dir_path / "hashes"
hashes_dir_path.mkdir(parents=True, exist_ok=True)
ots_dir_path = output_dir_path / "ots"
ots_dir_path.mkdir(parents=True, exist_ok=True)

base_name = CreateBaseName.get_basename(url)
png_path = main_dir_path / f"{base_name}.png"
html_path = main_dir_path / f"{base_name}.html"
hat_tmp_path = workspace_dir_path / f"{base_name}.har"
har_final_path = main_dir_path / f"{base_name}.har"
fullhtml_path = main_dir_path / f"{base_name}.full.html"

htmlhash_txt_path = hashes_dir_path / f"{base_name}.htmlsha256.txt"
onlyhtmlhash_txt_path = hashes_dir_path / f"{base_name}.onlyhtmlsha256.txt"
harhash_txt_path = hashes_dir_path / f"{base_name}.harsha256.txt"
onlyharhash_txt_path = hashes_dir_path / f"{base_name}.onlyharsha256.txt"
fullhtmlhash_txt_path = hashes_dir_path / f"{base_name}.fullhtmlsha256.txt"
onlyfullhtmlhash_txt_path = hashes_dir_path / f"{base_name}.onlyfullhtmlsha256.txt"

# Start to obtain HTML & PNG.
AutoCloseMsgBox.show_auto_closing_message("Starting to obtain HTML & PNG....", 2)
print("Starting to obtain HTML & PNG...")

# get local timezone
timezone_id = tzlocal.get_localzone().key

# Try to use the system locale.If that fails, default to 'en-US'.
locale_str = locale.getlocale()[0] or "en-US"

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
        record_har_path=hat_tmp_path,
        record_har_content="attach",  # Include both request and response bodies
        locale=locale_str,
        timezone_id=timezone_id,
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
        htmlhash_val = hashlib.sha256(f.read()).hexdigest()

    # Get the creation timestamp of the HTML file
    htmlstat = os.stat(html_path)
    htmlcreated_at = datetime.fromtimestamp(htmlstat.st_mtime).isoformat()

    # Write a detailed report containing the SHA-256 Hash of HTML
    with open(htmlhash_txt_path, "w", encoding="utf-8") as f:
        f.write(f"# File Information\n")
        f.write(f"URL: {url}\n")
        f.write(f"Capture Time: {htmlcreated_at}\n")
        f.write(f"File Name: {os.path.basename(html_path)}\n\n")
        f.write(f"# SHA-256 Hash\n")
        f.write(f"SHA256 ({os.path.basename(html_path)}) = {htmlhash_val}\n")

    # Creating a file with only the SHA-256 hash (used for OTS timestamp)
    with open(onlyhtmlhash_txt_path, "w", encoding="utf-8") as f:
        f.write(htmlhash_val + "\n")

    # Generate OTS timestamp for HTML and move it to the ots directory
    stamp_and_move(htmlhash_txt_path, ots_dir_path)
    stamp_and_move(onlyhtmlhash_txt_path, ots_dir_path)

    # Get the set of files before SingleFile save
    before_files = {f.name for f in DLfolder_path.glob("*.html")}

    # Save Full HTML using AHK via powershell
    ps_cmd = r'''
    $root = "$env:USERPROFILE\Projects\WebEvidenceCapture"
    Start-Process "$root\ahk\SingleFileSave1.exe"
    '''
    subprocess.run([powershell_path, "-Command", ps_cmd], check=False)

    # detect new HTML files in Downloads folder using loop
    max_wait = 60
    elapse = 0
    poll_interval = 1

    while elapse < max_wait:
        after_files = {i.name for i in DLfolder_path.glob("*.html")}
        diff_files = after_files - before_files

        if diff_files:
            # Select most newest one
            candidates = sorted(
                [DLfolder_path / j for j in diff_files],
                key=lambda j: j.stat().st_mtime,
                reverse=True
            )
            new_html_path = candidates[0]
            print(f" New HTML file is: {new_html_path.name}")
            break

        time.sleep(poll_interval)
        elapse += poll_interval
    else:
        raise RuntimeError(
            "Full HTML was not detected in Downloads within timeout."
        )

    # Temporarily move the saved full HTML to WSL
    if new_html_path.exists():
        fullhtml_detected_at = datetime.fromtimestamp(
            new_html_path.stat().st_mtime
        )
        fullhtml_detected_at = fmt_human(fullhtml_detected_at)
        print("SingleFile save completion time is: ", fullhtml_detected_at)
        shutil.move(new_html_path, fullhtml_path)

    # Generating SHA-256 hash of fullHTML
    with open(fullhtml_path, "rb") as f:
        fullhtmlhash_val = hashlib.sha256(f.read()).hexdigest()

    # Getting creation timestamp of fullHTML file
    fullhtmlstat = os.stat(fullhtml_path)
    fullhtmlcreated_at = datetime.fromtimestamp(fullhtmlstat.st_mtime).isoformat()

    # Detailed report including SHA-256 hash
    with open(fullhtmlhash_txt_path, "w", encoding="utf-8") as f:
        f.write(f"# File Information\n")
        f.write(f"URL: {url}\n")
        f.write(f"Capture Time: {fullhtmlcreated_at}\n")
        f.write(f"File Name: {fullhtml_path.name}\n\n")
        f.write(f"# SHA-256 Hash\n")
        f.write(f"SHA256 ({fullhtml_path.name}) = {fullhtmlhash_val}\n")

    # Creating a file containing only the SHA-256 Hash (used for OTS timestamp)
    with open(onlyfullhtmlhash_txt_path, "w", encoding="utf-8") as f:
        f.write(fullhtmlhash_val + "\n")

    # Generate OTS timestamp for Full HTML and move it to the ots directory
    stamp_and_move(fullhtmlhash_txt_path, ots_dir_path)
    stamp_and_move(onlyfullhtmlhash_txt_path, ots_dir_path)

    # Close Chrome tab
    powershell_command = r'''
    $root = "$env:USERPROFILE\Projects\WebEvidenceCapture"
    Start-Process "$root\ahk\CloseChromeTab1.exe"
    '''

    subprocess.run([powershell_path, "-Command", powershell_command])

    # Finalize HAR file saving (trigger internal flush)
    # Finalize HAR (flush & save)
    context.close()  
    # Close the Chromium instance
    browser.close()

# wait for HAR creation
for i in range(10):
    if hat_tmp_path.exists():
        break
    time.sleep(0.5)
else:
    raise RuntimeError("HAR file not found after waiting.")

# Move the saved HAR file to the HAR directory
try:
    shutil.move(hat_tmp_path, har_final_path)
except Exception as e:
    print(f"Failed to move HAR file: {e}")

# Generate SHA-256 hash of HAR file
with open(har_final_path, "rb") as f:
    harhash_value = hashlib.sha256(f.read()).hexdigest()

# Get the creation timestamp of the HAR file
harstat = os.stat(har_final_path)
harcreated_at = datetime.fromtimestamp(harstat.st_ctime).isoformat()

# Write a detailed report containing the SHA-256 Hash of HAR
with open(harhash_txt_path, "w", encoding="utf-8") as f:
    f.write(f"# File Information\n")
    f.write(f"URL: {url}\n")
    f.write(f"Capture Time: {harcreated_at}\n")
    f.write(f"File Name: {os.path.basename(har_final_path)}\n\n")
    f.write(f"# SHA-256 Hash\n")
    f.write(f"SHA256 ({os.path.basename(har_final_path)}) = {harhash_value}\n")

# Creating a file with only the SHA-256 hash of HAR
with open(onlyharhash_txt_path, "w", encoding="utf-8") as f:
    f.write(harhash_value + "\n")

# Generate OTS timestamp for HAR and move it to the ots directory
stamp_and_move(harhash_txt_path, ots_dir_path)
stamp_and_move(onlyharhash_txt_path, ots_dir_path)

# Extract HAR flush time
flush_time = datetime.fromtimestamp(
    har_final_path.stat().st_mtime
)
flush_time = fmt_human(flush_time)

# Generate README.txt
readme_path = output_dir_path / "README.txt"
timestampforReadme = fmt_human(datetime.now())

readme_content = f"""\

Generated by: WebEvidenceCapturer v2.1.0

This folder follows the structure below and contains:
- The saved webpage
- Supporting files for verifying its authenticity (hashes, timestamps, etc.)
【Target URL】
URL: {url}

【Saved Files】
- main\\{base_name}.png
- main\\{base_name}.html
- main\\{base_name}.har
   Note: HAR file: Network Communication log when saving PNG and HTML
- main\\{base_name}.full.html

【By-producs generated during HAR creation】
- workspace\\<<various files>>

【SHA256 Hash Files】
- hashes\\{base_name}.htmlsha256.txt
- hashes\\{base_name}.onlyhtmlsha256.txt
- hashes\\{base_name}.harsha256.txt
- hashes\\{base_name}.onlyharsha256.txt
- hashes\\{base_name}.fullhtmlsha256.txt
- hashes\\{base_name}.onlyfullhtmlsha256.txt

【OTS Timestamp Files (for tamper detection)】
- ots\\{base_name}.htmlsha256.txt.ots
- ots\\{base_name}.onlyhtmlsha256.txt.ots
- ots\\{base_name}.harsha256.txt.ots
- ots\\{base_name}.onlyharsha256.txt.ots
- ots\\{base_name}.fullhtmlsha256.txt.ots
- ots\\{base_name}.onlyfullhtmlsha256.txt.ots

【TimeLine】
Full HTML saved at: {fullhtml_detected_at}
HAR finalized (flush) at: {flush_time}
README.txt Creation at: {timestampforReadme}

The HAR recording session was still active after the Full HTML was saved.
"""

# Write to README.txt
readme_path.write_text(readme_content, encoding="utf-8")

# Moving the output directory to the Downloads folder
if output_dir_path.exists():
    shutil.move(output_dir_path, DLfolder_path)

 
