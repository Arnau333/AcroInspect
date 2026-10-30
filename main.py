#!/usr/bin/env python3
"""Punto de entrada ejecutable para AcroInspect."""

import sys
from pathlib import Path

# Añadir directorio .vendor empaquetado si las dependencias no están instaladas en el sistema del host
_vendor_dir = Path(__file__).resolve().parent / ".vendor"
if _vendor_dir.is_dir() and str(_vendor_dir) not in sys.path:
    sys.path.insert(0, str(_vendor_dir))

from acroinspect.cli import main

if __name__ == "__main__":
    main()
