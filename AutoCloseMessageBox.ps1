function Show-AutoClosingMessage {
    param (
        [string]$Message = "This message is automatically closed",
        [int]$Seconds = 5,  # Display duration in seconds
        [string]$Title = "Progress Information"   # Window title
    )

    # Initialize GUI componets
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    # Create the form
    $form = New-Object System.Windows.Forms.Form
    $form.Text = $Title
    $form.Size = New-Object System.Drawing.Size(400, 120)
    $form.StartPosition = "CenterScreen"
    $form.TopMost = $true

    # Add the message label
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Message
    $label.Dock = "Fill"
    $label.TextAlign = "MiddleCenter"
    $label.Font = New-Object System.Drawing.Font("Arial", 12)
    $form.Controls.Add($label)

    # Setup timer to auto-close the form
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = $Seconds * 1000
    $timer.Add_Tick({
        $timer.Stop()
        $form.Close()
    })
    $timer.Start()

    $form.ShowDialog() | Out-Null
}