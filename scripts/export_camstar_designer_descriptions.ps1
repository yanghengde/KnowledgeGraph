param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot ".env"

if (-not (Test-Path -LiteralPath $envPath)) {
    throw "Project .env file was not found."
}

$settings = @{}
foreach ($line in Get-Content -LiteralPath $envPath -Encoding UTF8) {
    if ($line -match '^\s*#' -or $line -notmatch '=') {
        continue
    }
    $name, $value = $line -split '=', 2
    $settings[$name.Trim()] = $value.Trim().Trim('"').Trim("'")
}

foreach ($required in @("SRC_DB_HOST", "SRC_DB_NAME", "SRC_DB_USER", "SRC_DB_PASSWORD")) {
    if (-not $settings[$required]) {
        throw "Missing $required in .env."
    }
}

$builder = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
$port = if ($settings["SRC_DB_PORT"]) { $settings["SRC_DB_PORT"] } else { "1433" }
$builder["Data Source"] = "$($settings['SRC_DB_HOST']),$port"
$builder["Initial Catalog"] = $settings["SRC_DB_NAME"]
$builder["User ID"] = $settings["SRC_DB_USER"]
$builder["Password"] = $settings["SRC_DB_PASSWORD"]
$builder["Encrypt"] = $true
$builder["TrustServerCertificate"] = $true
$builder["ApplicationIntent"] = "ReadOnly"
$builder["Connect Timeout"] = 20

$connection = New-Object System.Data.SqlClient.SqlConnection($builder.ConnectionString)
$connection.Open()
try {
    $command = $connection.CreateCommand()
    $command.CommandTimeout = 120
    $command.CommandText = @"
SELECT
    d.CDODefID AS cdoId,
    d.CDOName AS cdoName,
    d.CDODescription AS cdoDescription,
    f.FieldID AS fieldId,
    f.FieldName AS fieldName,
    f.FieldDescription AS fieldDescription
FROM CamstarPRD_SCHEMA.CDODefinition AS d
LEFT JOIN CamstarPRD_SCHEMA.CDOFields AS f ON f.CDODefID = d.CDODefID
ORDER BY d.CDOName, f.FieldName
"@
    $reader = $command.ExecuteReader()
    $rows = New-Object System.Collections.Generic.List[object]
    while ($reader.Read()) {
        $rows.Add([PSCustomObject]@{
            cdoId = if ($reader.IsDBNull(0)) { $null } else { $reader.GetValue(0) }
            cdoName = if ($reader.IsDBNull(1)) { "" } else { $reader.GetString(1) }
            cdoDescription = if ($reader.IsDBNull(2)) { "" } else { $reader.GetString(2) }
            fieldId = if ($reader.IsDBNull(3)) { $null } else { $reader.GetValue(3) }
            fieldName = if ($reader.IsDBNull(4)) { "" } else { $reader.GetString(4) }
            fieldDescription = if ($reader.IsDBNull(5)) { "" } else { $reader.GetString(5) }
        })
    }
    $reader.Close()

    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = Split-Path -Parent $resolvedOutput
    if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    $rows | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $resolvedOutput -Encoding UTF8
    Write-Output "rows=$($rows.Count)"
    Write-Output "output=$resolvedOutput"
}
finally {
    $connection.Close()
    $connection.Dispose()
}
