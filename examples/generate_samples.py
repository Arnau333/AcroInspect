"""Generador de PDFs de prueba con formularios AcroForm variados."""

from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, blue, lightgrey
from pathlib import Path


def create_sample_pdf_1(filepath: str):
    """Crea PDF base con varios tipos de campos en un orden específico."""
    c = canvas.Canvas(filepath)
    c.setTitle("Formulario Base de Prueba 1")

    c.drawString(100, 750, "Formulario Base: Registro de Usuario")

    form = c.acroForm
    # 1. Campo de texto
    c.drawString(100, 700, "Nombre Completo:")
    form.textfield(name="nombre_completo", tooltip="Nombre completo del usuario",
                   x=220, y=695, width=250, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 2. Correo electrónico (Texto)
    c.drawString(100, 660, "Correo Electrónico:")
    form.textfield(name="correo", tooltip="Email de contacto",
                   x=220, y=655, width=250, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 3. Edad (Texto)
    c.drawString(100, 620, "Edad:")
    form.textfield(name="edad", tooltip="Edad en años",
                   x=220, y=615, width=60, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 4. Género / Turno (Choice / Dropdown)
    c.drawString(100, 580, "País / Región:")
    form.choice(name="pais", tooltip="Seleccione país",
                x=220, y=575, width=150, height=20,
                options=["España", "México", "Argentina", "Colombia", "Chile"],
                value="España")

    # 5. Checkbox de términos
    c.drawString(100, 540, "Acepto los términos:")
    form.checkbox(name="acepta_terminos", tooltip="Aceptar condiciones",
                  x=220, y=538, size=15, buttonStyle='check')

    # 6. Comentarios (Texto multilínea)
    c.drawString(100, 500, "Comentarios:")
    form.textfield(name="comentarios", tooltip="Comentarios adicionales",
                   x=220, y=430, width=250, height=60, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    c.save()


def create_sample_pdf_2(filepath: str):
    """Crea un segundo PDF para comparar:
       - Coinciden: nombre_completo (Text), correo (Text), comentarios (Text)
       - Diferente tipo: acepta_terminos (en vez de Checkbox, es Text)
       - Falta en este PDF: pais (Dropdown)
       - Extra en este PDF: telefono (Text), fecha_nacimiento (Text)
       - Orden alterado en algunos campos.
    """
    c = canvas.Canvas(filepath)
    c.setTitle("Formulario Modificado 2")

    c.drawString(100, 750, "Formulario Modificado: Registro de Usuario")

    form = c.acroForm

    # 1. Correo electrónico (orden alterado respecto a PDF 1)
    c.drawString(100, 700, "Correo Electrónico:")
    form.textfield(name="correo", tooltip="Email",
                   x=220, y=695, width=250, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 2. Nombre Completo
    c.drawString(100, 660, "Nombre Completo:")
    form.textfield(name="nombre_completo", tooltip="Nombre",
                   x=220, y=655, width=250, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 3. Teléfono (Campo EXTRA que no existía en PDF 1)
    c.drawString(100, 620, "Teléfono Móvil:")
    form.textfield(name="telefono", tooltip="Número telefónico",
                   x=220, y=615, width=150, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 4. acepta_terminos ahora como TEXTO en lugar de Checkbox (TYPE MISMATCH)
    c.drawString(100, 580, "Acepta Términos (Escriba SI):")
    form.textfield(name="acepta_terminos", tooltip="Escriba SI",
                   x=220, y=575, width=60, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 5. Edad (Coincide en nombre y tipo)
    c.drawString(100, 540, "Edad:")
    form.textfield(name="edad", tooltip="Edad",
                   x=220, y=535, width=60, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 6. Comentarios (Coincide)
    c.drawString(100, 500, "Comentarios:")
    form.textfield(name="comentarios", tooltip="Comentarios",
                   x=220, y=430, width=250, height=60, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # 7. Fecha de Nacimiento (EXTRA)
    c.drawString(100, 390, "Fecha Nacimiento:")
    form.textfield(name="fecha_nacimiento", tooltip="DD/MM/AAAA",
                   x=220, y=385, width=120, height=20, borderStyle='inset', borderColor=black, fillColor=lightgrey)

    # NOTA: Se omitió deliberadamente el campo 'pais' (Falta en este PDF)

    c.save()


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    pdf1 = out_dir / "formulario_base.pdf"
    pdf2 = out_dir / "formulario_evaluar.pdf"
    create_sample_pdf_1(str(pdf1))
    create_sample_pdf_2(str(pdf2))
    print(f"Generados:\n - {pdf1}\n - {pdf2}")
