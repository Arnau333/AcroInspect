"""Pruebas unitarias para AcroInspect."""

import unittest
from pathlib import Path
from acroinspect.extractor import AcroFormExtractor
from acroinspect.comparator import AcroFormComparator
from examples.generate_samples import create_sample_pdf_1, create_sample_pdf_2


class TestAcroInspect(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(__file__).resolve().parent / "test_data"
        cls.test_dir.mkdir(exist_ok=True)
        cls.pdf1_path = cls.test_dir / "sample1.pdf"
        cls.pdf2_path = cls.test_dir / "sample2.pdf"

        create_sample_pdf_1(str(cls.pdf1_path))
        create_sample_pdf_2(str(cls.pdf2_path))

    def test_extract_pdf_1(self):
        extractor = AcroFormExtractor(self.pdf1_path)
        fields = extractor.extract_fields()

        # 6 campos definidos en sample 1
        self.assertEqual(len(fields), 6)

        # Verificar orden secuencial
        expected_sequence = [
            ("nombre_completo", "Text"),
            ("correo", "Text"),
            ("edad", "Text"),
            ("pais", "Dropdown"),
            ("acepta_terminos", "Checkbox"),
            ("comentarios", "Text"),
        ]

        extracted_pairs = [(f.name, f.field_type) for f in fields]
        self.assertEqual(extracted_pairs, expected_sequence)

    def test_compare_pdfs(self):
        ext1 = AcroFormExtractor(self.pdf1_path)
        ext2 = AcroFormExtractor(self.pdf2_path)

        fields1 = ext1.extract_fields()
        fields2 = ext2.extract_fields()

        report = AcroFormComparator.compare(fields1, fields2)

        self.assertFalse(report.is_identical)
        self.assertEqual(report.total_base_fields, 6)
        self.assertEqual(report.total_target_fields, 7)

        # Coincidencias exactas (nombre y tipo)
        matching_names = [m.name for m in report.matching_fields]
        self.assertIn("nombre_completo", matching_names)
        self.assertIn("correo", matching_names)
        self.assertIn("edad", matching_names)
        self.assertIn("comentarios", matching_names)
        self.assertEqual(len(matching_names), 4)

        # Discrepancias de tipo
        mismatch_names = [m.name for m in report.type_mismatches]
        self.assertIn("acepta_terminos", mismatch_names)

        # Faltantes en PDF objetivo
        missing_names = [m.name for m in report.missing_in_target]
        self.assertIn("pais", missing_names)

        # Variables extra en PDF objetivo
        extra_names = [m.name for m in report.extra_in_target]
        self.assertIn("telefono", extra_names)
        self.assertIn("fecha_nacimiento", extra_names)

        # Reporte de orden
        self.assertTrue(len(report.order_mismatches) > 0)

    def test_compare_identical(self):
        ext1 = AcroFormExtractor(self.pdf1_path)
        fields1 = ext1.extract_fields()

        report = AcroFormComparator.compare(fields1, fields1)
        self.assertTrue(report.is_identical)
        self.assertEqual(len(report.matching_fields), 6)
        self.assertEqual(len(report.type_mismatches), 0)
        self.assertEqual(len(report.missing_in_target), 0)
        self.assertEqual(len(report.extra_in_target), 0)
        self.assertEqual(len(report.order_mismatches), 0)


if __name__ == "__main__":
    unittest.main()
