# AcroInspect

Herramienta en Python para procesar formularios **AcroForm** en documentos PDF. Permite:
1. **Extraer en orden secuencial** los nombres y tipos de las variables/campos de formulario contenidos en el PDF.
2. **Comparar dos archivos PDF** para identificar qué variables coinciden, cuáles tienen diferente tipo, cuáles faltan y cuáles son adicionales, además de detectar inconsistencias en el orden.

---

## 🚀 Instalación de Dependencias

```bash
pip install -r requirements.txt
```

---

## 🛠️ Uso

### 1. Extracción de variables en orden secuencial

#### En formato tabla legible:
```bash
python3 main.py extract ruta/al/documento.pdf
```

#### En formato JSON estructurado:
```bash
python3 main.py extract ruta/al/documento.pdf --json
```

---

### 2. Comparación de dos documentos PDF

Compara un PDF base frente a un segundo PDF:

```bash
python3 main.py compare ruta/al/pdf_base.pdf ruta/al/pdf_segundo.pdf
```

También disponible con `--json` para integración con APIs o scripts automatizados:
```bash
python3 main.py compare ruta/al/pdf_base.pdf ruta/al/pdf_segundo.pdf --json
```

---

## 💻 Uso como Librería en Python

```python
from acroinspect import AcroFormExtractor, AcroFormComparator

# 1. Extraer variables
extractor1 = AcroFormExtractor("documento1.pdf")
fields1 = extractor1.extract_fields()

for field in fields1:
    print(f"#{field.index}: {field.name} -> {field.field_type} (Pág {field.page})")

# 2. Comparar con un segundo PDF
extractor2 = AcroFormExtractor("documento2.pdf")
fields2 = extractor2.extract_fields()

report = AcroFormComparator.compare(fields1, fields2, base_name="Doc1.pdf", target_name="Doc2.pdf")

# Imprimir resumen de texto
print(report.summary_text())

# O inspeccionar programáticamente:
print("Coincidencias:", len(report.matching_fields))
print("Diferencias de tipo:", len(report.type_mismatches))
print("Faltantes en Doc2:", len(report.missing_in_target))
print("Extras en Doc2:", len(report.extra_in_target))
```

---

## 🧪 Pruebas Unitarias y Generador de Muestras

Para generar PDFs de prueba con distintos tipos de campos (Texto, Checkbox, Dropdown, etc.):
```bash
python3 examples/generate_samples.py
```

Para ejecutar la suite de pruebas unitarias:
```bash
python3 -m unittest discover tests
```
