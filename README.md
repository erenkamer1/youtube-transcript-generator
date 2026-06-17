# YouTube Transkript ve Çeviri Uygulaması

YouTube URL'sinden sesi indirip Whisper ile transkript çıkaran, Ollama ile çeviri ve prompt üretimi yapan yerel web uygulaması.

## Gereksinimler

- Python 3.11+
- Node.js 20+
- FFmpeg (yt-dlp ses dönüşümü için)
- CUDA destekli GPU (opsiyonel; cuBLAS eksikse CPU fallback devreye girer)
- Ollama (`ollama serve` çalışır durumda)

## Hızlı Başlangıç

### 1. Ollama modeli

Önerilen (hız/kalite dengesi):

```bash
ollama pull qwen2.5:14b
```

Kurulu modellerinizden biri de kullanılabilir (`qwen2.5:32b`, `qwen2.5-coder:14b`, `llama3.2`).

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Git Bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

GPU doğrulama:

```bash
python scripts/verify_gpu.py
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Uygulama: http://localhost:5173

## Özellikler

- YouTube URL → ses indirme → Whisper transkript (zaman damgalı)
- Ollama ile hedef dile çeviri (SSE stream)
- Prompt şablonları (NotebookLM / ChatGPT için tek tık kopyala)
- Video özeti
- Transkript içinde arama
- Geçmiş kayıtları (SQLite)
- TXT / SRT / VTT dışa aktarma

## Ortam Değişkenleri (opsiyonel)

`.env` dosyasını `backend/` altına koyabilirsiniz:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
DEFAULT_OLLAMA_MODEL=qwen2.5:14b
WHISPER_DEVICE=auto
WHISPER_MODEL=large-v3
```

CUDA/cuBLAS hatası alırsanız:

```env
WHISPER_DEVICE=cpu
```

## GPU (RTX 5080 / CUDA 13 sürücü)

CTranslate2, **CUDA 12** DLL'leri ister (`cublas64_12.dll`). Sürücünüz CUDA 13 desteklese bile bu DLL'ler ayrıca gerekir:

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12
```

Bu paketler `requirements.txt` içinde. Backend başlarken otomatik PATH'e eklenir.

Doğrulama: `GET http://127.0.0.1:8000/api/health` → `"cuda": {"cuda_available": true}`

Sorun devam ederse backend'i **yeniden başlatın** (PATH uygulama başında ayarlanır).

## Bilinen Notlar

- Kişisel/yerel kullanım içindir; YouTube kullanım koşullarına dikkat edin.
- RTX 5080 gibi yeni GPU'larda `cublas64_12.dll` eksikse transkripsiyon otomatik CPU'ya düşer.
- İlk transkriptte Whisper `large-v3` modeli indirilir (~3 GB).

## Proje Yapısı

```
backend/     FastAPI + Whisper + Ollama entegrasyonu
frontend/    React + Vite + Tailwind arayüz
docs/        Dokümantasyon
```
