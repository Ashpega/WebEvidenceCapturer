[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms

$autoClosePath = "$PSScriptRoot\AutoCloseMessageBox.ps1"
$baseNamePath = "$PSScriptRoot\CreateBaseName.ps1"

if (!(Test-Path $autoClosePath) -or !(Test-Path $baseNamePath)) {
    Write-Host "Missing required module file. Exiting." -ForegroundColor Red
    return
}

. $autoClosePath
. $baseNamePath

$flag = 0
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$output_dir_name = "output_$timestamp"
$url_txt_path = (Join-Path $PSScriptRoot "../examples/tmp_url.txt")
$wslScriptUrlTxtPath = wsl wslpath "'$url_txt_path'"
Write-Host "wslScriptUrlTxtPath = $wslScriptUrlTxtPath"

$url = [Microsoft.VisualBasic.Interaction]::InputBox("Enter URL you would like to save.", "URL input")

if ([string]::IsNullOrWhiteSpace($url) -or $url -notmatch '^https?://') {
    Show-AutoClosingMessage -Message "Please input a valid URL." -Seconds 3
    return
}

$url = Sanitize-Url -rawUrl $url

$url | Out-File -FilePath $url_txt_path -Encoding utf8

$result = [System.Windows.Forms.MessageBox]::Show(
	"Do you want to save from Wayback Machine? `nYes: Use Wayback `nNo: Save from live Webpage `nCancel: Abort",
	"Select Capture Method",
	[System.Windows.Forms.MessageBoxButtons]::YesNoCancel,
	[System.Windows.Forms.MessageBoxIcon]::Question
)

# Use it as a file name by Python Script
$base_name = Get-BaseName -url $url

# Change save directory and saving way according to user choice
if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
   Show-AutoClosingMessage -Message "Starting to save the webpage from Wayback Machine..." -Seconds 3
   $flag = 1
} elseif ($result -eq [System.Windows.Forms.DialogResult]::No) {
	Show-AutoClosingMessage -Message "Starting to save the webpage directly from the URL..." -Seconds 3
} elseif  ($result -eq [System.Windows.Forms.DialogResult]::Cancel) {
 	Show-AutoClosingMessage -Message "Quitting without saving." -Seconds 3
	return
	}

Write-Host "wsl runnnig.."

if ($flag -eq 0) {
    wsl bash -c "source ~/dev/myenv_withPlayWright/bin/activate && python3 ~/dev/myenv_withPlayWright/ObtainHashOts.py '$wslScriptUrlTxtPath' '$output_dir_name' '$base_name'"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "An error occurred (CODE: $LASTEXITCODE)"
        return
    }
}


if ($flag -eq 0) {
    wsl bash -c "source ~/dev/myenv_withPlayWright/bin/activate && python3 ~/dev/myenv_withPlayWright/ObtainHashOts.py '$wslScriptUrlTxtPath' '$output_dir_name' '$base_name'"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "An error occurred (CODE: $LASTEXITCODE)"
        return
    }
}

<#
if ($flag -eq 0) {
   $command = "source ~/dev/myenv_withPlayWright/bin/activate && python3 ~/dev/myenv_withPlayWright/ObtainHashOts.py '$wslScriptUrlTxtPath' '$output_dir_name' '$base_name'"

   Start-Process cmd.exe -ArgumentList "/c wsl bash -c '$command'"

}
#>

if ($flag -eq 1){
   Show-AutoClosingMessage -Message "Wayback save is not implemented yet. Exiting." -Seconds 3
   # TODO: Plan to implement for saving process via Wayback machine
    # 1. Saving request using Wayback API
    # 2. enable user to opt saving scope if possible
    return
}


# success.txt path output by Python
$htmlFetchedPath = Join-Path $PSScriptRoot "../examples/htmlFetched.txt"

$timeoutSec = 60

Write-Host "Waiting for htmlFetched signal from Python..."

# Start time
$startTime = Get-Date

while (-not (Test-Path $htmlFetchedPath)) {
   Start-Sleep -Seconds 1

       # Timeout judgement
   if ((Get-Date) - $startTime -gt (New-TimeSpan -Seconds $timeoutSec)) {
      Write-Host "Timeout: htmlFetched.txt did not appear within $timeoutSec seconds."
      exit 1   # quit main.ps1
   }
}

Write-Host "Detected success.txt! Proceeding to the next step..."


if ($flag -eq 1){
   Show-AutoClosingMessage -Message "Wayback save is not implemented yet. Exiting." -Seconds 3
   # TODO: Plan to implement for saving process via Wayback machine
    # 1. Saving request using Wayback API
    # 2. enable user to opt saving scope if possible
    return
}

# Saving Full HTML by means of Chrome + SingleFile

# Launching Chrome...
Write-Host "Launching Chrome for saving using SingleFile."

Start-Process "chrome.exe" -ArgumentList @("--profile-directory=Default", "$url")

# Check for saved HTML files in Downloads directory
# Obtain the file list (as a dictionary) in the Downloads folder before saveing
$DLdirPath = "$env:USERPROFILE\Downloads"
$beforeFiles = Get-ChildItem -Path $DLdirPath -File -Filter *.html | Sort-Object Name
$beforeNames = @($beforeFiles | Select-Object -ExpandProperty Name)

# After a short wait, send the save Shortcut using AHK
Write-Host "Executing AHK script..."
Start-Process (Join-Path $PSScriptRoot "..\ahk\SingleFileSave1.ahk")
# If needed, wait briefly

# Detect new files by comparing current and previous file lists in the Downloads folder
$timeout = 60
$elapsed = 0
$newFile = $null

while ($elapsed -lt $timeout) {
      $afterFiles = Get-ChildItem -Path $DLdirPath -File -Filter *.html | Sort-Object Name
      $afterNames  = @($afterFiles  | Select-Object -ExpandProperty Name)

      $newItems = @(Compare-Object -ReferenceObject $beforeNames -DifferenceObject $afterNames |
                Where-Object { $_.SideIndicator -eq "=>" } |
                Select-Object -ExpandProperty InputObject)

        
	if ($newItems.Count -gt 0) {
	   Write-Host "newItem = $newItems[0]"
	   $newFile = Get-Item -Path (Join-Path $DLdirPath $newItems[0])
           break
	   }

       Start-Sleep -Seconds 1
       $elapsed++
}

# Close the open Chrome tab using AHK
Write-Host " Executing AHK script for closing Chrome tab..."
Start-Process (Join-Path $PSScriptRoot "..\ahk\CloseChromeTab1.ahk")


# Rename the full HTML file and create fullhtmlReady.txt
if ($newFile) {
   $targetPath = Join-Path -Path (Split-Path $newFile) -ChildPath "$base_name.full.html"
   Move-Item -Path $newFile.FullName -Destination $targetPath -Force
   Write-Host "Renamed file path: $targetPath"
   $wslScriptFullHtmlPath = wsl wslpath "'$targetPath'"
   Write-Host "Renamed WSL path for Full HTML: $wslScriptFullHtmlPath"

$FullHtmlPathTxtPath = (Join-Path $PSScriptRoot "../examples/fullhtmlReady.txt")

$wslScriptFullHtmlPath | Out-File -FilePath $FullHtmlPathTxtPath -Encoding utf8
}

# success.txt path output by Python
$successFilePath = Join-Path $PSScriptRoot "../examples/success.txt"

$timeoutSec = 60

Write-Host "Waiting for success signal from Python..."

# wait for success.txt output by Python
$startTime = Get-Date

while (-not (Test-Path $successFilePath)) {
   Start-Sleep -Seconds 1

       # Timeout judgement
   if ((Get-Date) - $startTime -gt (New-TimeSpan -Seconds $timeoutSec)) {
      Write-Host "Timeout: success.txt did not appear within $timeoutSec seconds."
      exit 1   # quit main.ps1
   }
}

Write-Host "Detected success.txt! Proceeding to the next step..."


# Check if the output folder has been created in the Downloads folder
$expectedPath = Join-Path $DLdirPath $output_dir_name

if (!(Test-Path $expectedPath)) {
   Write-Warning "The output folder was not found."
   return
}

# Generate README.txt
$timestamp2 = (Get-Date).ToString("o")
$readme_path = "$expectedPath\README.txt"

$readmeContent = @"

Generated by: WebEvidenceCapturer v1.1

This folder follows the structure below and contains:
- The saved webpage
- Supporting files for verifying its authenticity (hashes, timestamps, etc.)
【Target URL】
URL: $url

【Saved Files】
- main\$base_name.png
- main\$base_name.html
- main\$base_name.har
   Note: HAR file: Network Communication log when saving PNG and HTML
- main\$base_name.full.html

【Assets generated during HAR creation】
- assets\<<various files>>

【SHA256 Hash Files】
- hashes\$base_name.sha256.txt
- hashes\$base_name.onlysha256.txt
- hashes\$base_name.harsha256.txt
- hashes\$base_name.onlyharsha256.txt
- hashes\$base_name.fullsha256.txt
- hashes\$base_name.onlyfullsha256.txt

【OTS Timestamp Files (for tamper detection)】
- ots\$base_name.sha256.txt.ots
- ots\$base_name.onlysha256.txt.ots
- ots\$base_name.harsha256.txt.ots
- ots\$base_name.onlyharsha256.txt.ots
- ots\$base_name.fullsha256.txt.ots
- ots\$base_name.onlyfullsha256.txt.ots

【README.txt Creation Timestamp】
$timestamp2
"@

$readmeContent | Out-File -FilePath $readme_path -Encoding utf8
