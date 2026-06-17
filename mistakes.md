# Mistakes Log

Bu dosya, projede yapılan hataları ve öğrenilen dersleri kaydeder.

---

## [2026-06-17] - youtube-transcript-generator/main - cublas-gpu-fallback

**Specific Case:** 
Whisper modeli CUDA'da yüklendi ama transkripsiyon sırasında `cublas64_12.dll is not found` hatası oluştu.

**Root Cause:** 
CTranslate2 CUDA cihaz sayısını görse de runtime cuBLAS kütüphanesi sistem PATH'inde yoktu (Blackwell + CUDA 12 uyumsuzluğu).

**Fix (Step-by-step):** 
1. `transcribe_audio` içinde CUDA runtime hatalarını yakala.
2. Modeli CPU/int8 ile yeniden yükle.
3. Transkripsiyonu CPU'da tekrar dene.
4. `verify_gpu.py` ve README'ye not eklendi.

**Code (Before → After):**
```diff
- segments, info = _collect_segments(model, audio_path)
+ try:
+     segments, info = _collect_segments(model, audio_path)
+ except Exception:
+     model, device = _switch_to_cpu()
+     segments, info = _collect_segments(model, audio_path)
```

**Lesson Learned (1 sentence):** 
GPU model yüklemesi başarılı olsa bile inference aşamasında cuBLAS hatası için CPU fallback şart.

**Tags:** `#bug` `#deployment` `#performance`

---

## [2026-06-17] - youtube-transcript-generator/main - cublas-cuda12-pip-fix

**Specific Case:** 
RTX 5080 + CUDA 13.2 sürücüde `cublas64_12.dll` bulunamadı, GPU devre dışı kaldı.

**Root Cause:** 
CTranslate2 CUDA 12 DLL'leri ister; CUDA 13 toolkit farklı DLL adları kullanır, ABI uyumsuz.

**Fix (Step-by-step):** 
1. `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12`
2. `app/cuda_setup.py` ile bin yollarını process PATH'ine ekle (import öncesi).
3. `os.add_dll_directory` yetmez; C++ LoadLibrary PATH kullanır.

**Lesson Learned (1 sentence):** 
Windows + RTX 50xx'te pip CUDA 12 runtime paketleri + PATH en başta şart.

**Tags:** `#deployment` `#performance`

---

**Specific Case:** 
13+ dakika %87'de kalma; 231MB ses dosyasında CPU + large-v3 transkripsiyon.

**Root Cause:** 
cuBLAS eksik → CPU fallback; large-v3 CPU'da uzun videolarda çok yavaş. Progress çubuğu gerçek ilerlemeyi yansıtmıyordu.

**Fix (Step-by-step):** 
1. cuBLAS DLL yoksa baştan CPU kullan.
2. CPU'da `medium` modeli kullan (large-v3 yerine).
3. Segment bazlı gerçek progress + geçen süre göster.

**Lesson Learned (1 sentence):** 
CUDA fallback'te büyük Whisper modeli kullanma; segment progress ve süre göstergesi şart.

**Tags:** `#performance` `#bug`

---