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

# Receive value from main.ps1
if len(sys.argv) < 5:
    print("The script's directory was not passed.")
    exit(1)

import sys
print("Checking command-line arguments")
for i, arg in enumerate(sys.argv):
    print(f"argv[{i}]: {arg}")

url_file_path = Path(sys.argv[4])
with open(url_file_path, 'r', encoding='utf-8') as f:
    url = f.readline().strip()
url = re.sub(r'^[\ufeff]+', '', url)  # Removing the BOM from URL if present
    
venv_root = Path(sys.prefix)
print("venv_root in GetHash.py=", venv_root)
base_name = sys.argv[3]
fullhtmlpath_org = Path(sys.argv[1])
fullhtmlpath_name = fullhtmlpath_org.name
scriptDLfolder = fullhtmlpath_org.parent
output_dir = venv_root / sys.argv[2]
main_dir = output_dir / "main"
main_dir.mkdir(parents=True, exist_ok=True)
hashes_dir = output_dir / "hashes"
hashes_dir.mkdir(parents=True, exist_ok=True)
ots_dir = output_dir / "ots"
ots_dir.mkdir(parents=True, exist_ok=True)
fullhtml_path = main_dir / fullhtmlpath_name
fullhash_txt_path = hashes_dir / f"{base_name}.fullsha256.txt"
onlyfullhash_txt_path = hashes_dir / f"{base_name}.onlyfullsha256.txt"
fullhtml_ots_path = fullhash_txt_path.with_name(fullhash_txt_path.name + ".ots")
onlyfullhtml_ots_path = onlyfullhash_txt_path.with_name(onlyfullhash_txt_path.name + ".ots")

# Temporarily moving the saved .full.html to WSL
if fullhtmlpath_org.exists():
    shutil.move(fullhtmlpath_org, fullhtml_path)

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

# Getting OTS timestamp
result = subprocess.run(["ots", "stamp", fullhash_txt_path])
if result.returncode != 0:
    print("Failed to obtain OTS timestamp for:", fullhash_txt_path)

result = subprocess.run(["ots", "stamp", onlyfullhash_txt_path])
if result.returncode != 0:
    print("Failed to obtain OTS timestamp for:", onlyfullhash_txt_path)

# Moving generated fullHash OTS file to the ots directory
if fullhtml_ots_path.exists():
    shutil.move(fullhtml_ots_path, ots_dir / fullhtml_ots_path.name)

# Moving generated onlyfullHash OTS file to the ots directory
if onlyfullhtml_ots_path.exists():
    shutil.move(onlyfullhtml_ots_path, ots_dir / onlyfullhtml_ots_path.name)

# Moving the output directory to the Downloads folder
if output_dir.exists():
    shutil.move(output_dir, scriptDLfolder)

print("\n Successfuly saved fullHTML, HASH, and OTS timestamp files.")

    
