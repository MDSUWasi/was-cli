"""
Unit tests for the WAS extractor module.
Run with: python -m pytest tests/ -v
"""
import os
import zipfile
import tempfile
import unittest
from was.extractor import extract_document_text, read_text_file, read_docx_file, read_odt_file


class TestTextFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_txt_extraction(self):
        path = os.path.join(self.test_dir, "test.txt")
        with open(path, 'w') as f:
            f.write("Hello\nWorld\n")
        lines = extract_document_text(path)
        self.assertEqual(lines, ["Hello", "World"])

    def test_md_extraction(self):
        path = os.path.join(self.test_dir, "test.md")
        with open(path, 'w') as f:
            f.write("# Header\nSome content\n")
        lines = extract_document_text(path)
        self.assertEqual(lines, ["# Header", "Some content"])

    def test_py_extraction(self):
        path = os.path.join(self.test_dir, "test.py")
        with open(path, 'w') as f:
            f.write("import os\nprint('hello')\n")
        lines = extract_document_text(path)
        self.assertEqual(lines, ["import os", "print('hello')"])

    def test_empty_file(self):
        path = os.path.join(self.test_dir, "empty.txt")
        with open(path, 'w') as f:
            pass
        lines = extract_document_text(path)
        self.assertEqual(lines, [])

    def test_trailing_newline_handling(self):
        path = os.path.join(self.test_dir, "trailing.txt")
        with open(path, 'w') as f:
            f.write("Line 1\nLine 2\n")
        lines = extract_document_text(path)
        self.assertEqual(lines, ["Line 1", "Line 2"])
        self.assertFalse(lines[-1] == "")

    def test_unsupported_extension_raises(self):
        path = os.path.join(self.test_dir, "test.xyz")
        with open(path, 'w') as f:
            f.write("data")
        with self.assertRaises(ValueError):
            extract_document_text(path)


class TestDocxExtraction(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.docx_path = os.path.join(self.test_dir, "test.docx")
        # Create a minimal valid DOCX (OpenXML) file
        document_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Hello World</w:t></w:r></w:p>
    <w:p><w:r><w:t>Second paragraph</w:t></w:r></w:p>
  </w:body>
</w:document>'''
        with zipfile.ZipFile(self.docx_path, 'w') as zf:
            zf.writestr('word/document.xml', document_xml)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_docx_extraction(self):
        lines = extract_document_text(self.docx_path)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "Hello World")
        self.assertEqual(lines[1], "Second paragraph")

    def test_invalid_docx_raises(self):
        bad_path = os.path.join(self.test_dir, "bad.docx")
        with open(bad_path, 'w') as f:
            f.write("Not a real docx")
        with self.assertRaises(ValueError):
            extract_document_text(bad_path)


class TestODTExtraction(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.odt_path = os.path.join(self.test_dir, "test.odt")
        # Create a minimal valid ODT file
        content_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                         xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body>
    <office:text>
      <text:p>First paragraph</text:p>
      <text:p>Second paragraph</text:p>
    </office:text>
  </office:body>
</office:document-content>'''
        with zipfile.ZipFile(self.odt_path, 'w') as zf:
            zf.writestr('content.xml', content_xml)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_odt_extraction(self):
        lines = extract_document_text(self.odt_path)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "First paragraph")
        self.assertEqual(lines[1], "Second paragraph")


if __name__ == "__main__":
    unittest.main()