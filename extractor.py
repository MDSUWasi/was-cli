import os
import zipfile
import xml.etree.ElementTree as ET

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
}

def read_text_file(filepath):
    """Safely reads a plain text file line by line."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read().splitlines()

def read_docx_file(filepath):
    """Extracts raw paragraphs from modern .docx OpenXML zip structures."""
    if not zipfile.is_zipfile(filepath):
        raise ValueError(f"File {filepath} is not a valid DOCX file.")
    lines = []
    with zipfile.ZipFile(filepath, 'r') as docx:
        doc_xml = docx.read('word/document.xml')
        root = ET.fromstring(doc_xml)
        for paragraph in root.iter(f"{{{NAMESPACES['w']}}}p"):
            p_text = [t.text for t in paragraph.iter(f"{{{NAMESPACES['w']}}}t") if t.text]
            lines.append("".join(p_text))
    return lines

def read_odt_file(filepath):
    """Extracts text paragraphs from LibreOffice .odt zip files."""
    if not zipfile.is_zipfile(filepath):
        raise ValueError(f"File {filepath} is not a valid ODT file.")
    lines = []
    with zipfile.ZipFile(filepath, 'r') as odt:
        content_xml = odt.read('content.xml')
        root = ET.fromstring(content_xml)
        for paragraph in root.iter(f"{{{NAMESPACES['text']}}}p"):
            p_text = "".join(paragraph.itertext())
            lines.append(p_text)
    return lines

def extract_document_text(filepath):
    """Central dispatcher to read text content depending on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        return read_docx_file(filepath)
    elif ext == '.odt':
        return read_odt_file(filepath)
    elif ext in ['.txt', '.md', '.py', '.json', '.html', '.css']:
        return read_text_file(filepath)
    else:
        raise ValueError(f"Unsupported extension: '{ext}'")