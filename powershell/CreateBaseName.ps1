function Sanitize-Url {
    param([string]$rawUrl)

    # Remove BOM if present (Byte Order Mark)
    $url = $rawUrl -replace '^[\uFEFF]+', ''

    return $url
}

function Get-BaseName {
    param([string]$url)

    # Replace "/" and "・" with "_" and remove leading/trailing underscores
    $name = $url -replace '^https?://', '' -replace '/', '_' -replace '^_+|_+$', ''

    # URL-decode the string
    $name = [System.Net.WebUtility]::UrlDecode($name)

    # Replacing or remove specific character (For compatibility with Python scripts)
    $name = $name -replace '[\?=&\#]', '_'
    $name = $name -replace '[<>:"/\\|\*]', ''
    $name = $name -replace '[. ]+$', ''

    if ($name.Length -gt 200) {
        $name = $name.Substring(0, 200)
    }

    return $name
}
