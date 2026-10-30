"""AcroInspect: Herramienta para inspeccionar y comparar formularios AcroForm en archivos PDF."""

import sys
from pathlib import Path

_vendor_dir = Path(__file__).resolve().parent.parent / ".vendor"
if _vendor_dir.is_dir() and str(_vendor_dir) not in sys.path:
    sys.path.insert(0, str(_vendor_dir))

from .extractor import AcroFormExtractor, FormFieldInfo
from .comparator import AcroFormComparator, ComparisonReport, FieldDiff

__all__ = [
    "AcroFormExtractor",
    "FormFieldInfo",
    "AcroFormComparator",
    "ComparisonReport",
    "FieldDiff",
]
