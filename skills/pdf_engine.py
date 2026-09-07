"""
Fronda 1.0 - Motor de Lectura e Ingesta de Documentos PDF
Extrae texto de documentos PDF locales para análisis, resúmenes o consulta.
"""

import os
from typing import Optional


def extract_text_from_pdf(file_path: str, max_pages: int = 5, max_chars: int = 2500) -> str:
    """Extrae el contenido de texto de un archivo PDF."""
    if not os.path.exists(file_path):
        return f"El archivo PDF '{file_path}' no fue encontrado."

    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        extracted = []
        for i in range(pages_to_read):
            text = reader.pages[i].extract_text() or ""
            if text.strip():
                extracted.append(f"--- [Página {i+1}] ---\n{text.strip()}")

        full_text = "\n\n".join(extracted)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + f"\n\n[... Truncado a {max_chars} caracteres de un total de {total_pages} páginas]."

        return (
            f"📄 **DOCUMENTO PDF LEÍDO EXITOSAMENTE: {os.path.basename(file_path)}**\n"
            f"• **Total de Páginas**: {total_pages} (Mostrando {pages_to_read})\n\n"
            f"{full_text}"
        )
    except Exception as e:
        return f"Error al procesar el archivo PDF: {e}"
