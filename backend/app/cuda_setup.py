"""CUDA 12 DLL path setup for CTranslate2 on Windows (RTX 50xx / CUDA 13 driver)."""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

_configured = False


def setup_cuda_libs() -> list[str]:
    """Add nvidia-*-cu12 package bin dirs to PATH before CTranslate2 loads."""
    global _configured

    if _configured:
        return []

    bin_dirs: list[str] = []

    for pkg_name in ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_nvrtc"):
        try:
            mod = __import__(pkg_name, fromlist=["__path__"])
        except ImportError:
            continue

        pkg_dir = next(iter(mod.__path__), None)
        if pkg_dir is None:
            continue

        candidate = os.path.join(pkg_dir, "bin" if sys.platform == "win32" else "lib")
        if os.path.isdir(candidate):
            bin_dirs.append(candidate)

    if not bin_dirs:
        logger.warning(
            "nvidia-cublas-cu12 paketleri bulunamadı. "
            "GPU için: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12"
        )
        _configured = True
        return []

    if sys.platform == "win32":
        os.environ["PATH"] = os.pathsep.join(bin_dirs) + os.pathsep + os.environ.get("PATH", "")
        for directory in bin_dirs:
            os.add_dll_directory(directory)
    else:
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(
            bin_dirs + ([existing] if existing else [])
        )

    logger.info("CUDA kütüphane yolları yapılandırıldı: %s", bin_dirs)
    _configured = True
    return bin_dirs
