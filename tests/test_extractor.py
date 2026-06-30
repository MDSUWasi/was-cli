"""Extractor tests - handles txt/docx/odt files."""
import os, zipfile, tempfile, shutil
import unittest
from was.extractor import extract_document_text


class TxtTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_basic_txt(self):
        fp = os.path.join(self.tmp, "test.txt")
        with open(fp, 'w') as f:
            f.write("Hello\nHi\n")
        self.assertEqual(extract_document_text(fp), ["Hello", "Hi"])

    def test_markdown_same_as_txt(self):
        fp = os.path.join(self.tmp, "doc.md")
        with open(fp, 'w') as f:
            f.write("# Title\nContent\n")
        lines = extract_document_text(fp)
        self.assertEqual(lines[0], "# Title")

    def test_python_ext_works(self):
        fp = os.path.join(self.tmp, "script.py")
        with open(fp, 'w') as f:
            f.write("print('hi')\n")
        lines = extract_document_text(fp)
        self.assertEqual(lines[0], "print('hi')")

    def test_empty_file(self):
        fp = os.path.join(self.tmp, "empty.txt")
        open(fp, 'w').close()
        self.assertEqual(extract_document_text(fp), [])

    def test_final_newline_stripped(self):
        fp = os.path.join(self.tmp, "nl.txt")
        with open(fp, 'w') as f:
            f.write("L1\nL2\n")
        lines = extract_document_text(fp)
        self.assertNotEqual(lines[-1], "")

    def test_unknown_ext_throws(self):
        fp = os.path.join(self.tmp, "weird.xyz")
        with open(fp, 'w') as f:
            f.write("data")
        with self.assertRaises(ValueError):
            extract_document_text(fp)


class DocxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        xml = b'''<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Para 1</w:t></w:r></w:p>
    <w:p><w:r><w:t>Para 2</w:t></w:r></w:p>
  </w:body>
</w:document>'''
        fp = os.path.join(self.tmp, "test.docx")
        with zipfile.ZipFile(fp, 'w') as z:
            z.writestr('word/document.xml', xml)
        self.fp = fp

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_parses_docx(self):
        lines = extract_document_text(self.fp)
        self.assertEqual(len(lines), 2)

    def test_corrupt_docx_fails(self):
        bad = os.path.join(self.tmp, "broken.docx")
        with open(bad, 'w') as f:
            f.write("garbage")
        with self.assertRaises(ValueError):
            extract_document_text(bad)


class OdtTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        xml = b'''<?xml version="1.0"?>
<office:document-content xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body><office:text>
    <text:p>P1</text:p>
    <text:p>P2</text:p>
  </office:text></office:body>
</office:document-content>'''
        fp = os.path.join(self.tmp, "test.odt")
        with zipfile.ZipFile(fp, 'w') as z:
            z.writestr('content.xml', xml)
        self.fp = fp

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_parses_odt(self):
        lines = extract_document_text(self.fp)
        self.assertEqual(lines, ["P1", "P2"])


if __name__ == "__main__":
    unittest.main()
