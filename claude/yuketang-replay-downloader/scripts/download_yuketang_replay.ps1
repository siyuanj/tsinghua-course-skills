[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReplayUrl,

    [string]$OutputDir = (Get-Location).Path,

    [string]$OutputBaseName,

    [switch]$Transcribe,

    [switch]$InstallTranscriptionDeps,

    [string]$WhisperModel = "small",

    [string]$Language = "zh"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Missing required command: $Name"
    }

    return $command.Source
}

function Get-SafeBaseName {
    param([Parameter(Mandatory = $true)][string]$Url)

    try {
        $uri = [System.Uri]$Url
        $candidate = [System.IO.Path]::GetFileNameWithoutExtension($uri.AbsolutePath)
    }
    catch {
        $candidate = $null
    }

    if ([string]::IsNullOrWhiteSpace($candidate)) {
        $candidate = "yuketang-replay"
    }

    foreach ($invalidChar in [System.IO.Path]::GetInvalidFileNameChars()) {
        $candidate = $candidate.Replace($invalidChar, "_")
    }

    return $candidate
}

function Invoke-Download {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$TargetPath
    )

    $curlPath = Require-Command -Name "curl.exe"
    $curlArgs = @(
        "-L",
        "--fail",
        "--retry", "3",
        "--retry-all-errors",
        "-C", "-",
        "-H", "Referer: https://pro.yuketang.cn/",
        "-H", "Origin: https://pro.yuketang.cn",
        "-o", $TargetPath,
        $Url
    )

    Write-Host "Downloading replay to $TargetPath"
    & $curlPath @curlArgs

    if ($LASTEXITCODE -ne 0) {
        throw "curl.exe failed with exit code $LASTEXITCODE"
    }

    if (-not (Test-Path $TargetPath)) {
        throw "Download finished without producing a file: $TargetPath"
    }

    $file = Get-Item $TargetPath
    if ($file.Length -le 0) {
        throw "Downloaded file is empty: $TargetPath"
    }

    Write-Host ("Download complete: {0} MB" -f [math]::Round($file.Length / 1MB, 2))
}

function Ensure-TranscriptionDependency {
    $pythonPath = Require-Command -Name "python"

    $importArgs = @("-c", "import faster_whisper")
    & $pythonPath @importArgs 2>$null
    if ($LASTEXITCODE -eq 0) {
        return $pythonPath
    }

    if (-not $InstallTranscriptionDeps) {
        throw "faster-whisper is not installed. Re-run with -InstallTranscriptionDeps to install it."
    }

    Write-Host "Installing faster-whisper into the current Python environment"
    & $pythonPath -m pip install faster-whisper
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install faster-whisper"
    }

    & $pythonPath @importArgs
    if ($LASTEXITCODE -ne 0) {
        throw "faster-whisper is still unavailable after installation"
    }

    return $pythonPath
}

function Invoke-Transcription {
    param(
        [Parameter(Mandatory = $true)][string]$VideoPath,
        [Parameter(Mandatory = $true)][string]$TranscriptPath,
        [Parameter(Mandatory = $true)][string]$ModelName,
        [Parameter(Mandatory = $true)][string]$TranscriptionLanguage
    )

    $pythonPath = Ensure-TranscriptionDependency
    $pythonScript = @'
import sys
from faster_whisper import WhisperModel

video_path, transcript_path, model_name, language = sys.argv[1:5]
model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, info = model.transcribe(video_path, language=language, vad_filter=True)

with open(transcript_path, "w", encoding="utf-8") as handle:
    for seg in segments:
        handle.write(f"[{seg.start:.1f}-{seg.end:.1f}] {seg.text}\n")

print(transcript_path)
'@

    Write-Host "Transcribing replay to $TranscriptPath"
    $pythonScript | & $pythonPath - $VideoPath $TranscriptPath $ModelName $TranscriptionLanguage
    if ($LASTEXITCODE -ne 0) {
        throw "Transcription failed"
    }
}

if (-not $OutputBaseName) {
    $OutputBaseName = Get-SafeBaseName -Url $ReplayUrl
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$videoPath = Join-Path $OutputDir ($OutputBaseName + ".mp4")
Invoke-Download -Url $ReplayUrl -TargetPath $videoPath

if ($Transcribe) {
    $transcriptPath = Join-Path $OutputDir ($OutputBaseName + ".txt")
    Invoke-Transcription -VideoPath $videoPath -TranscriptPath $transcriptPath -ModelName $WhisperModel -TranscriptionLanguage $Language
}

Write-Host "Done"
