# Yerel Kurulum

## Ön koşullar

1. FFmpeg kurulu olmalı (`ffmpeg -version`)
2. Ollama servisi çalışmalı (`ollama list`)
3. Python venv ve Node bağımlılıkları kurulmalı

## Servisleri başlatma

Terminal 1:

```bash
cd backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

## GPU sorun giderme (RTX 5080)

**Sorun:** Sürücü CUDA 13 destekler ama CTranslate2 `cublas64_12.dll` (CUDA 12) arar.

**Çözüm:**
```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12
```

Backend otomatik olarak bu DLL yollarını PATH'e ekler (`app/cuda_setup.py`).

Doğrulama:
```bash
curl http://127.0.0.1:8000/api/health
# "cuda": {"cuda_available": true, "active_device": "cuda"}
```

`cublas64_12.dll` hatası devam ederse:

- CUDA Toolkit 12.x cuBLAS DLL'lerinin PATH'te olduğundan emin olun
- veya `WHISPER_DEVICE=cpu` kullanın

Doğrulama:

```bash
cd backend
source .venv/Scripts/activate
python scripts/verify_gpu.py
python scripts/e2e_smoke_test.py
```
