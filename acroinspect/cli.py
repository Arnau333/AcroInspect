"""Interfaz de línea de comandos (CLI) para AcroInspect."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .extractor import AcroFormExtractor, FormFieldInfo
from .comparator import AcroFormComparator, ComparisonReport


def format_table(fields: List[FormFieldInfo]) -> str:
    """Formatea la lista de campos en una tabla de texto legible."""
    if not fields:
        return "No se encontraron variables/campos AcroForm en el archivo."

    headers = ["#", "Nombre de Variable", "Tipo de Campo", "Página", "Requerido", "Solo Lectura"]
    rows = []
    for f in fields:
        rows.append([
            str(f.index),
            f.name,
            f.field_type,
            str(f.page) if f.page else "-",
            "Sí" if f.required else "No",
            "Sí" if f.read_only else "No"
        ])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    separator = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_str = "| " + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)) + " |"

    lines = [separator, header_str, separator]
    for row in rows:
        row_str = "| " + " | ".join(f"{val:<{col_widths[i]}}" for i, val in enumerate(row)) + " |"
        lines.append(row_str)
    lines.append(separator)

    return "\n".join(lines)


def run_extract(pdf_path: str, as_json: bool = False):
    p = Path(pdf_path)
    if not p.is_file():
        print(f"Error: El archivo '{pdf_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    extractor = AcroFormExtractor(p)
    fields = extractor.extract_fields()

    if as_json:
        data = [f.to_dict() for f in fields]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"\nCampos AcroForm extraídos de: {p.name}")
        print(f"Total variables detectadas: {len(fields)}\n")
        print(format_table(fields))


def run_compare(base_pdf: str, target_pdf: str, as_json: bool = False):
    p_base = Path(base_pdf)
    p_target = Path(target_pdf)

    for p in (p_base, p_target):
        if not p.is_file():
            print(f"Error: El archivo '{p}' no existe.", file=sys.stderr)
            sys.exit(1)

    extractor_base = AcroFormExtractor(p_base)
    base_fields = extractor_base.extract_fields()

    extractor_target = AcroFormExtractor(p_target)
    target_fields = extractor_target.extract_fields()

    report: ComparisonReport = AcroFormComparator.compare(
        base_fields=base_fields,
        target_fields=target_fields,
        base_name=p_base.name,
        target_name=p_target.name,
    )

    if as_json:
        result = {
            "base_pdf": report.base_pdf,
            "target_pdf": report.target_pdf,
            "total_base_fields": report.total_base_fields,
            "total_target_fields": report.total_target_fields,
            "is_identical": report.is_identical,
            "matching_fields": [m.to_dict() for m in report.matching_fields],
            "type_mismatches": [m.to_dict() for m in report.type_mismatches],
            "missing_in_target": [m.to_dict() for m in report.missing_in_target],
            "extra_in_target": [m.to_dict() for m in report.extra_in_target],
            "order_mismatches": report.order_mismatches,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n" + report.summary_text() + "\n")


def main():
    parser = argparse.ArgumentParser(
        prog="acroinspect",
        description="AcroInspect: Extractor y comparador de campos y variables AcroForm en archivos PDF.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Subcomando: extract
    extract_parser = subparsers.add_parser("extract", help="Extraer en orden secuencial las variables de un PDF")
    extract_parser.add_argument("pdf", help="Ruta al archivo PDF con formulario AcroForm")
    extract_parser.add_argument("--json", action="store_true", help="Salida en formato JSON")

    # Subcomando: compare
    compare_parser = subparsers.add_parser(
        "compare", help="Comparar la estructura de campos entre dos archivos PDF"
    )
    compare_parser.add_argument("base_pdf", help="Archivo PDF base o de referencia")
    compare_parser.add_argument("target_pdf", help="Archivo PDF a comparar con la base")
    compare_parser.add_argument("--json", action="store_true", help="Salida en formato JSON")

    # Subcomando: ui / gui
    ui_parser = subparsers.add_parser("ui", help="Lanzar la interfaz gráfica en el navegador")
    ui_parser.add_argument("--port", type=int, default=8765, help="Puerto del servidor (por defecto: 8765)")
    ui_parser.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador")

    args = parser.parse_args()

    if args.command == "extract":
        run_extract(args.pdf, as_json=args.json)
    elif args.command == "compare":
        run_compare(args.base_pdf, args.target_pdf, as_json=args.json)
    elif args.command in ("ui", "gui"):
        from .app_gui import start_server
        start_server(port=args.port, open_browser=not args.no_browser)
    else:
        # Si no se pasan argumentos, iniciar directamente la interfaz gráfica
        from .app_gui import start_server
        start_server(port=8765, open_browser=True)


if __name__ == "__main__":
    main()
