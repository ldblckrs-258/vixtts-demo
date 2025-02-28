$PYTHON_VERSION = "3.10"

# Kiểm tra xem Python có được cài đặt không
$pythonPath = Get-Command "py" -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "Python version $PYTHON_VERSION is not installed. Please install it."
    exit 1
}

Write-Host "Using Python version: $PYTHON_VERSION"

# Kiểm tra và tạo virtual environment
if (Test-Path ".env/ok") {
    .\.env\Scripts\Activate
} else {
    Write-Host "The environment is not ok. Running setup..."
    Remove-Item -Recurse -Force ".env" -ErrorAction SilentlyContinue
    py -3.10 -m venv .env
    & .\.env\Scripts\Activate

    # Cập nhật submodule
    git submodule update --init --recursive

    # Cài đặt TTS
    Set-Location "TTS"
    git fetch --tags
    git checkout 0.1.1
    Write-Host "Installing TTS..."
    pip install --use-deprecated=legacy-resolver -e . -q
    Set-Location ..

    # Cài đặt requirements
    Write-Host "Installing other requirements..."
    pip install -r requirements.txt -q

    # Tải tokenizer Japanese/Chinese
    Write-Host "Downloading Japanese/Chinese tokenizer..."
    python -m unidic download

    # Đánh dấu môi trường đã được thiết lập
    New-Item ".env/ok" -ItemType File -Force
}

# Chạy vixtts_demo.py
python vixtts_demo.py
