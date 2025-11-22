# WebEvidenceCapturer


## Overview
“WebEvidenceCapturer” is a practical tool for preserving verifiable evidence that a specific webpage was publicly available with the original content at a particular point in time.

When official certification or third-party archiving services are unavailable, costly, or too slow, this tool enables users to capture webpages independently and reliably.
It is especially useful in situations where:

- You want to preserve a webpage “just in case”
- You need to archive a large number of pages
- You’re unsure whether the page will be needed later as evidence
- You don’t have time to request a third-party preservation service

This project aims to provide a **self-contained, reproducible, and tamper-resistant evidence preservation method** without relying on external systems.
It is well-suited for individuals handling legal matters on their own, corporate legal teams, and practitioners who frequently need to capture online information.


## How It Works
This section outlines the steps WebEvidenceCapturer follows to preserve a webpage, along with the rationale behind each step.

### 1.  Capture HTML, PNG, and HAR using Playwright
   - The HTML and PNG files are captured to record the visual and structural content of the webpage.
   - A HAR (HTTP Archive) file is also saved, which is a JSON-formatted log of the browser’s full network activity during the browsing session, including the requests and responses involved in obtaining the HTML and PNG files.

### 2.  Generate SHA-256 hashes for HTML and HAR files
   - Two types of hash text files are created for each target file:
     (1) one including file information such as URL and timestamp, and
     (2) one containing only the hash value.
   - These hashes provide proof of content integrity and are used as input for timestamping.

### 3.  Obtain OTS timestamps for each hash text file
   - OpenTimestamps (OTS) is a blockchain-based timestamping protocol.
   - WEC applies OTS timestamps to both types of hash text files to prove that they have not been modified since the time of capture.

### 4.  Save Full HTML using SingleFile
   - [SingleFile](https://github.com/gildas-lormeau/SingleFile) is a Chrome extension that saves an entire webpage—including CSS, images, fonts, and frames—as a single standalone HTML file.
   - This format closely reflects how the webpage appears to users in a browser.
   - Full HTML serves as a visual complement, especially in cases where Playwright cannot capture the page correctly due to anti-bot mechanisms or dynamic content.


## Output Structure
WebEvidenceCapturer (WEC) creates an `output_<datetime>` directory in `$HOME/Downloads/`.  
This directory contains all captured data, HAR file, hash files, and timestamp files, organized as follows:  
A detailed explanation of the directory structure is also included in the `README.txt` file generated within the output directory.


output_<datetime>/
├── main/
│ ├── <base_name>.png
│ ├── <base_name>.html
│ ├── <base_name>.har
│ └── <base_name>.full.html
├── hash/
│ ├── <base_name>.sha256.txt
│ ├── <base_name>.onlysha256.txt
│ ├── <base_name>.harsha256.txt
│ ├── <base_name>.onlyharsha256.txt
│ ├── <base_name>.fullsha256.txt
│ └── <base_name>.onlyfullsha256.txt
├── ots/
│ ├── <base_name>.sha256.txt.ots
│ ├── <base_name>.onlysha256.txt.ots
│ ├── <base_name>.harsha256.txt.ots
│ ├── <base_name>.onlyharsha256.txt.ots
│ ├── <base_name>.fullsha256.txt.ots
│ └── <base_name>.onlyfullsha256.txt.ots
├── assets/
│ └── (temporary files generated during HAR creation)
└── README.txt


## Logical Structure of Evidence

- The HAR file serves as proof that network communication took place and that specific content was transmitted and received.
- The HTML and PNG files were obtained during the same session, and their consistency with the HAR data can be verified.
- When the OTS timestamps of the HAR hash and the Full HTML hash are close in time, and neither file shows signs of tampering, it provides strong presumptive evidence that the webpage was publicly available in that form at that time.
- The combination of SHA-256 hashes and OTS timestamps ensures that none of the captured files have been altered since the time of acquisition.


## Sample Output: README.txt

The following is a sample of the `README.txt` file automatically generated in each output directory.
Some parts are omitted for brevity.

```text
This folder follows the structure below and contains:
- The saved webpage
- Supporting files for verifying its authenticity (hashes, timestamps, etc.)
【Target URL】
URL: https://news.yahoo.co.jp/categories/science

【Saved Files】
- main\news.yahoo.co.jp_categories_science.png
- main\news.yahoo.co.jp_categories_science.html
- main\news.yahoo.co.jp_categories_science.har
  Note: HAR file：Network Communication log when saving PNG and HTML
- main\news.yahoo.co.jp_categories_science.full.html

【Assets generated during HAR creation】
- assets\<<various files>>
...

【OTS Timestamp Files】
ots\news.yahoo.co.jp_categories_science.sha256.txt.ots
...

【README.txt Creation Timestamp】
2025-11-18T13:58:04.5227441+09:00

```


## Installation (Windows 10 / 11 + WSL)

This project is tested on Windows 10 and 11 using WSL2 with Ubuntu 24.04.  
It uses Python 3.12 in a virtual environment, Playwright for page capture, and OpenTimestamps for verification.

---

### 1. Chrome & Extensions

- Install “Google Chrome”
- Add the “SingleFile” extension to Chrome
  - [SingleFile GitHub](https://github.com/gildas-lormeau/SingleFile)
  - [SingleFile on Chrome Web Store](https://chromewebstore.google.com/detail/singlefile/mpiodijhokgodhhofbcjdecpffjipkle)

---

### 2. Install AutoHotkey (AHK)

- Download from: [https://www.autohotkey.com/](https://www.autohotkey.com/)

---

### 3. Set Up WSL + Ubuntu 24.04

```powershell
wsl --install
wsl --install -d Ubuntu-24.04
```

---

### 4. Set Up Python Environment in WSL

```bash
# Install venv and pip
sudo apt update
sudo apt install -y python3.12-venv python3-pip

# Create virtual environment
python3 -m venv myenv_withPlayWright
```

---

### 5. Install Required Python Packages

The following commands should be executed **within the virtual environment**:

```bash
# Install Playwright and its dependencies
pip install playwright
playwright install

# Install OpenTimestamps client
pip install opentimestamps-client
```

## Usage
- Obtain this repository by running `git pull` or downloading the ZIP file.
- Move `GetHashOtsofFullHtml.py` and `ObtainPngHtml.py` to the home directory of the virtual environment in WSL (e.g., `/home/<username>/`).
- Place the remaining files (e.g., PowerShell scripts) into any directory on the Windows side (e.g., `C:\Users\<username>\Projects\WebEvidenceCapturer\`).
- Double-click `run_main.bat` to start the process.
- After execution, an `output_<datetime>` folder will be created in the `Downloads` folder (e.g., `C:\Users\<username>\Downloads\`).

For details about the file and folder structure, please refer to the `README.txt` file in the generated output folder.


## Notes / Limitations

- Saving a designated webpage from the Wayback Machine is not yet implemented.  
  Therefore, clicking “Yes” on the prompt ("Do you want to save from Wayback Machine?") currently has no effect.  

  This feature is planned for future implementation.

- In some cases, Playwright may be blocked by anti-bot mechanisms, resulting in a page that shows only an “access denied” message.  

  However, this **does not necessarily mean** that evidence preservation has failed.  
  This is because the HAR file may still contain valuable request/response logs that prove access attempts.  
  In addition, the Full HTML file is saved at nearly the same time the HAR file is generated.  
  These two facts together support the presumption that the designated webpage was publicly available in that form at that time.

  To handle such a case, a dedicated feature aimed at enhancing evidentiary reliability is planned for future implementation.



## License
MIT License


## Author
Copyright (c) 2025 Ashpega
