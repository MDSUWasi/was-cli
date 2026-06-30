import os, zipfile
import xml.etree.ElementTree as ET

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
}

def _read_txt(fp):
    """Plain text file reader."""
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
        if content.endswith('\n') and lines and lines[-1] == '':
            lines.pop()
        return lines

def _read_docx(fp):
    """Extract paragraphs from .docx."""
    if not zipfile.is_zipfile(fp):
        raise ValueError(f"Not valid DOCX: {fp}")
    lines = []
    with zipfile.ZipFile(fp, 'r') as z:
        doc_xml = z.read('word/document.xml')
        root = ET.fromstring(doc_xml)
        ns = NAMESPACES['w']
        for para in root.iter(f"{{{ns}}}p"):
            texts = [t.text for t in para.iter(f"{{{ns}}}t") if t.text]
            lines.append("".join(texts))
    return lines

def _read_odt(fp):
    """Extract paragraphs from .odt."""
    if not zipfile.is_zipfile(fp):
        raise ValueError(f"Not valid ODT: {fp}")
    lines = []
    with zipfile.ZipFile(fp, 'r') as z:
        content_xml = z.read('content.xml')
        root = ET.fromstring(content_xml)
        for para in root.iter(f"{{{NAMESPACES['text']}}}p"):
            lines.append("".join(para.itertext()))
    return lines

def extract_document_text(filepath):
    """Route to appropriate parser."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        return _read_docx(filepath)
    elif ext == '.odt':
        return _read_odt(filepath)
    elif ext in ['.txt', '.md', '.py', '.json', '.html', '.css']:
        return _read_txt(filepath)
    else:
        raise ValueError(f"Unsupported extension: '{ext}'")
