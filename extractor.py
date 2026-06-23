import os
import zipfile
import xml.etree.ElementTree as ET

# XML Namespaces used in standard OpenXML Word documents (.docx)
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

def read_text_file(filepath):
    """Reads a plain text file and returns a list of lines."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read().splitlines()

def write_text_file(filepath, lines):
    """Writes a list of lines to a plain text file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

def read_docx_file(filepath):
    """
    Extracts raw text line-by-line from a .docx file without external dependencies.
    Under the hood, a docx is a zip file. We parse word/document.xml.
    """
    if not zipfile.is_zipfile(filepath):
        raise ValueError(f"File {filepath} is not a valid DOCX file.")
        
    lines = []
    with zipfile.ZipFile(filepath, 'r') as docx:
        # Read the main document XML structure
        doc_xml = docx.read('word/document.xml')
        root = ET.fromstring(doc_xml)
        
        # Search for all paragraph tags <w:p>
        for paragraph in root.iter(f"{{{NAMESPACES['w']}}}p"):
            p_text = []
            # Search for text elements <w:t> within the paragraph
            for text_node in paragraph.iter(f"{{{NAMESPACES['w']}}}t"):
                if text_node.text:
                    p_text.append(text_node.text)
            lines.append("".join(p_text))
            
    return lines

def write_docx_file(filepath, lines):
    """
    Saves a list of text lines back into a clean, minimal, valid .docx document structure.
    This creates standard paragraphs that any office suite (Microsoft Word, LibreOffice) can read.
    """
    # Create the minimal XML structure of a document.xml file
    root = ET.Element(f"{{{NAMESPACES['w']}}}document", nsmap={'w': NAMESPACES['w']})
    body = ET.SubElement(root, f"{{{NAMESPACES['w']}}}body")
    
    for line in lines:
        p = ET.SubElement(body, f"{{{NAMESPACES['w']}}}p")
        r = ET.SubElement(p, f"{{{NAMESPACES['w']}}}r")
        t = ET.SubElement(r, f"{{{NAMESPACES['w']}}}t")
        # Ensure we preserve space formatting
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = line
        
    # Standard boilerplate files required inside a zip archive to make it a valid .docx
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
        <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
        <Default Extension="xml" ContentType="application/xml"/>
        <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    </Types>"""
    
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    </Relationships>"""
    
    # Register namespaces globally to prevent ElementTree from writing ugly ns0 prefixes
    ET.register_namespace('w', NAMESPACES['w'])
    
    # Render XML string
    document_xml_data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    
    # Package into docx zip file format
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types_xml.strip())
        docx.writestr('_rels/.rels', rels_xml.strip())
        docx.writestr('word/document.xml', document_xml_data)

def extract_document_text(filepath):
    """Helper dispatcher to extract text based on file format extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        return read_docx_file(filepath)
    elif ext in ['.txt', '.md', '.py', '.json']:
        return read_text_file(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only .docx, .txt, .md, .py files are supported.")

def write_document_text(filepath, lines):
    """Helper dispatcher to write text back into its native file format."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        write_docx_file(filepath, lines)
    elif ext in ['.txt', '.md', '.py', '.json']:
        write_text_file(filepath, lines)
    else:
        raise ValueError(f"Unsupported file format: {ext}")