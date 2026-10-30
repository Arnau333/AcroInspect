"""Módulo extractor de campos AcroForm de archivos PDF."""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pypdf
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject


FIELD_TYPE_NAMES: Dict[str, str] = {
    "/Tx": "Text",
    "/Btn": "Button",
    "/Ch": "Choice",
    "/Sig": "Signature",
}


@dataclass
class FormFieldInfo:
    """Representa la información de un campo/variable de un formulario AcroForm."""

    index: int
    name: str
    field_type: str  # Ej: Text, Checkbox, Radio, PushButton, Dropdown, ListBox, Signature
    raw_type: str    # Código crudo en PDF: /Tx, /Btn, /Ch, /Sig o Unknown
    page: Optional[int] = None
    alternate_name: Optional[str] = None
    mapping_name: Optional[str] = None
    flags: int = 0
    read_only: bool = False
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AcroFormExtractor:
    """Extrae campos y variables de un formulario AcroForm en orden secuencial."""

    def __init__(self, pdf_source: Union[str, Path, bytes, pypdf.PdfReader]):
        if isinstance(pdf_source, pypdf.PdfReader):
            self.reader = pdf_source
        else:
            self.reader = pypdf.PdfReader(pdf_source)

    def extract_fields(self) -> List[FormFieldInfo]:
        """Extrae la lista secuencial de variables/campos con su nombre y tipo.

        Preserva el orden secuencial del documento (orden de campos de formulario / página).
        """
        # Obtenemos el diccionario raíz /Root y luego /AcroForm
        catalog = self.reader.trailer.get("/Root", {})
        if isinstance(catalog, IndirectObject):
            catalog = catalog.get_object()

        acro_form = catalog.get("/AcroForm")
        if isinstance(acro_form, IndirectObject):
            acro_form = acro_form.get_object()

        fields_array = []
        if isinstance(acro_form, (dict, DictionaryObject)):
            fields_obj = acro_form.get("/Fields", [])
            if isinstance(fields_obj, IndirectObject):
                fields_obj = fields_obj.get_object()
            if isinstance(fields_obj, (list, ArrayObject)):
                fields_array = list(fields_obj)

        results: List[FormFieldInfo] = []

        # Mapa para asociar indirect refs o diccionarios de widgets con el número de página (1-indexed)
        widget_page_map: Dict[int, int] = {}
        for page_idx, page in enumerate(self.reader.pages):
            annots = page.get("/Annots")
            if isinstance(annots, IndirectObject):
                annots = annots.get_object()
            if isinstance(annots, (list, ArrayObject)):
                for annot_ref in annots:
                    annot_obj = annot_ref.get_object() if isinstance(annot_ref, IndirectObject) else annot_ref
                    if isinstance(annot_obj, (dict, DictionaryObject)):
                        widget_page_map[id(annot_obj)] = page_idx + 1
                        if isinstance(annot_ref, IndirectObject):
                            widget_page_map[annot_ref.idnum] = page_idx + 1

        def resolve_obj(obj: Any) -> Any:
            if isinstance(obj, IndirectObject):
                return obj.get_object()
            return obj

        def determine_field_type(raw_ft: Optional[str], flags: int, dict_obj: Dict[str, Any]) -> str:
            raw_str = str(raw_ft) if raw_ft else ""
            if raw_str == "/Tx":
                if flags & (1 << 20):  # Password flag (bit 21)
                    return "Text (Password)"
                if flags & (1 << 12):  # Multiline flag (bit 13)
                    return "Text (Multiline)"
                return "Text"
            elif raw_str == "/Btn":
                # Bit 16: Pushbutton, Bit 15: Radio
                if flags & (1 << 16):
                    return "PushButton"
                elif flags & (1 << 15):
                    return "Radio"
                else:
                    return "Checkbox"
            elif raw_str == "/Ch":
                # Bit 18: Combo (Dropdown) vs ListBox
                if flags & (1 << 17):
                    return "Dropdown"
                return "ListBox"
            elif raw_str == "/Sig":
                return "Signature"
            return "Unknown"

        def traverse_node(node_ref: Any, inherited_name: str = "", inherited_ft: Optional[str] = None, inherited_flags: int = 0):
            node = resolve_obj(node_ref)
            if not isinstance(node, (dict, DictionaryObject)):
                return

            local_name = node.get("/T")
            full_name = inherited_name
            if local_name:
                local_name_str = str(local_name)
                full_name = f"{inherited_name}.{local_name_str}" if inherited_name else local_name_str

            ft = node.get("/FT", inherited_ft)
            flags = node.get("/Ff", inherited_flags)
            if isinstance(flags, int):
                combined_flags = flags
            else:
                combined_flags = inherited_flags

            kids = node.get("/Kids")
            resolved_kids = resolve_obj(kids)

            if isinstance(resolved_kids, (list, ArrayObject)) and len(resolved_kids) > 0:
                # Verificar si los hijos son campos hijos o anotaciones widget de este campo
                # Si algún hijo tiene /T, es una jerarquía de campos
                has_subfields = any(isinstance(resolve_obj(k), (dict, DictionaryObject)) and resolve_obj(k).get("/T") for k in resolved_kids)
                if has_subfields:
                    for child_ref in resolved_kids:
                        traverse_node(child_ref, inherited_name=full_name, inherited_ft=ft, inherited_flags=combined_flags)
                    return
                # De lo contrario, este nodo es el campo terminal y sus hijos son widgets (ej. opciones de Radio)

            # Nodo terminal representativo de un campo/variable
            if full_name:
                raw_ft_str = str(ft) if ft else "Unknown"
                type_name = determine_field_type(raw_ft_str, combined_flags, node)
                
                # Intentar determinar la página
                page_num = None
                p_ref = node.get("/P")
                if p_ref is not None:
                    # Encontrar índice de página
                    p_obj = resolve_obj(p_ref)
                    for p_i, p in enumerate(self.reader.pages):
                        if p is p_obj or (isinstance(p_ref, IndirectObject) and getattr(p, "indirect_reference", None) and p.indirect_reference.idnum == p_ref.idnum):
                            page_num = p_i + 1
                            break

                if page_num is None:
                    # Buscar en widget_page_map
                    page_num = widget_page_map.get(id(node))
                    if page_num is None and isinstance(node_ref, IndirectObject):
                        page_num = widget_page_map.get(node_ref.idnum)

                # Flags comunes: ReadOnly (bit 1), Required (bit 2)
                read_only = bool(combined_flags & 1)
                required = bool(combined_flags & 2)
                alt_name = str(node.get("/TU")) if node.get("/TU") is not None else None
                map_name = str(node.get("/TM")) if node.get("/TM") is not None else None

                results.append(
                    FormFieldInfo(
                        index=len(results) + 1,
                        name=full_name,
                        field_type=type_name,
                        raw_type=raw_ft_str,
                        page=page_num,
                        alternate_name=alt_name,
                        mapping_name=map_name,
                        flags=combined_flags,
                        read_only=read_only,
                        required=required,
                    )
                )

        for top_ref in fields_array:
            traverse_node(top_ref)

        return results
