"""Módulo comparador de estructuras de formularios AcroForm entre dos archivos PDF."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .extractor import FormFieldInfo


@dataclass
class FieldDiff:
    """Detalle de una diferencia o coincidencia entre variables."""

    name: str
    status: str  # 'MATCH', 'TYPE_MISMATCH', 'MISSING_IN_TARGET', 'EXTRA_IN_TARGET'
    base_field: Optional[FormFieldInfo] = None
    target_field: Optional[FormFieldInfo] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "note": self.note,
            "base_type": self.base_field.field_type if self.base_field else None,
            "target_type": self.target_field.field_type if self.target_field else None,
            "base_index": self.base_field.index if self.base_field else None,
            "target_index": self.target_field.index if self.target_field else None,
        }


@dataclass
class ComparisonReport:
    """Reporte estructurado de la comparación entre dos formularios AcroForm."""

    base_pdf: str
    target_pdf: str
    total_base_fields: int
    total_target_fields: int
    matching_fields: List[FieldDiff] = field(default_factory=list)
    type_mismatches: List[FieldDiff] = field(default_factory=list)
    missing_in_target: List[FieldDiff] = field(default_factory=list)
    extra_in_target: List[FieldDiff] = field(default_factory=list)
    order_mismatches: List[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        """Indica si ambos documentos tienen exactamente las mismas variables y tipos."""
        return (
            len(self.type_mismatches) == 0
            and len(self.missing_in_target) == 0
            and len(self.extra_in_target) == 0
        )

    def summary_text(self) -> str:
        """Genera un resumen en formato texto legible."""
        lines = [
            "=" * 60,
            " REPORTE DE COMPARACIÓN DE FORMULARIOS ACROFORM",
            "=" * 60,
            f"Archivo Base     (1): {self.base_pdf} ({self.total_base_fields} campos)",
            f"Archivo a Evaluar(2): {self.target_pdf} ({self.total_target_fields} campos)",
            "-" * 60,
            f" Coincidencias exactas (Nombre y Tipo) : {len(self.matching_fields)}",
            f" Discrepancias de Tipo                 : {len(self.type_mismatches)}",
            f" Variables faltantes en el segundo PDF : {len(self.missing_in_target)}",
            f" Variables adicionales en segundo PDF  : {len(self.extra_in_target)}",
            "-" * 60,
        ]

        if self.matching_fields:
            lines.append("\n[+] VARIABLES COINCIDENTES:")
            for item in self.matching_fields:
                lines.append(f"  ✓ {item.name:<30} [Tipo: {item.base_field.field_type}]")

        if self.type_mismatches:
            lines.append("\n[!] DISCREPANCIAS DE TIPO (Mismo nombre, distinto tipo):")
            for item in self.type_mismatches:
                b_type = item.base_field.field_type if item.base_field else "N/A"
                t_type = item.target_field.field_type if item.target_field else "N/A"
                lines.append(f"  ≠ {item.name:<30} [Base: {b_type} vs Segundo: {t_type}]")

        if self.missing_in_target:
            lines.append("\n[-] VARIABLES QUE FALTAN EN EL SEGUNDO PDF:")
            for item in self.missing_in_target:
                lines.append(f"  ✗ {item.name:<30} [Tipo esperado: {item.base_field.field_type}]")

        if self.extra_in_target:
            lines.append("\n[+] VARIABLES EXTRA EN EL SEGUNDO PDF (No presentes en Base):")
            for item in self.extra_in_target:
                lines.append(f"  + {item.name:<30} [Tipo encontrado: {item.target_field.field_type}]")

        if self.order_mismatches:
            lines.append("\n[~] DIFERENCIAS EN EL ORDEN SECUENCIAL (Para variables comunes):")
            for note in self.order_mismatches:
                lines.append(f"  ~ {note}")

        lines.append("=" * 60)
        return "\n".join(lines)


class AcroFormComparator:
    """Compara las estructuras de campos AcroForm extraídas de dos archivos PDF."""

    @staticmethod
    def compare(
        base_fields: List[FormFieldInfo],
        target_fields: List[FormFieldInfo],
        base_name: str = "PDF_1",
        target_name: str = "PDF_2",
    ) -> ComparisonReport:
        """Compara la lista de campos base con la del PDF objetivo y genera un ComparisonReport."""
        report = ComparisonReport(
            base_pdf=base_name,
            target_pdf=target_name,
            total_base_fields=len(base_fields),
            total_target_fields=len(target_fields),
        )

        base_dict: Dict[str, FormFieldInfo] = {f.name: f for f in base_fields}
        target_dict: Dict[str, FormFieldInfo] = {f.name: f for f in target_fields}

        # Analizar campos del PDF base frente al objetivo
        for base_field in base_fields:
            name = base_field.name
            if name in target_dict:
                target_field = target_dict[name]
                if base_field.field_type == target_field.field_type:
                    report.matching_fields.append(
                        FieldDiff(
                            name=name,
                            status="MATCH",
                            base_field=base_field,
                            target_field=target_field,
                            note="Nombre y tipo coinciden exactamente.",
                        )
                    )
                else:
                    report.type_mismatches.append(
                        FieldDiff(
                            name=name,
                            status="TYPE_MISMATCH",
                            base_field=base_field,
                            target_field=target_field,
                            note=f"Tipo distinto: '{base_field.field_type}' != '{target_field.field_type}'.",
                        )
                    )
            else:
                report.missing_in_target.append(
                    FieldDiff(
                        name=name,
                        status="MISSING_IN_TARGET",
                        base_field=base_field,
                        target_field=None,
                        note="Variable presente en PDF base pero ausente en segundo PDF.",
                    )
                )

        # Analizar campos extra en PDF objetivo
        for target_field in target_fields:
            name = target_field.name
            if name not in base_dict:
                report.extra_in_target.append(
                    FieldDiff(
                        name=name,
                        status="EXTRA_IN_TARGET",
                        base_field=None,
                        target_field=target_field,
                        note="Variable presente en segundo PDF pero no en PDF base.",
                    )
                )

        # Analizar discrepancias de orden secuencial en campos compartidos
        common_base_names = [f.name for f in base_fields if f.name in target_dict]
        common_target_names = [f.name for f in target_fields if f.name in base_dict]

        if common_base_names != common_target_names:
            report.order_mismatches.append(
                f"El orden secuencial de los campos comunes difiere entre ambos archivos.\n"
                f"    Orden en Base   : {common_base_names}\n"
                f"    Orden en Segundo: {common_target_names}"
            )

        return report
