import weasyprint
from jinja2 import Template
from datetime import datetime
from typing import Dict

class PDFGenerator:
    @staticmethod
    def generate_pdf_from_html(html_template: str, context: Dict[str, str]) -> bytes:
        """
        Renders HTML with context and converts it to PDF bytes.
        """
        try:
            template = Template(html_template)
            rendered_html = template.render(**context)
            pdf_bytes = weasyprint.HTML(string=rendered_html).write_pdf()
            return pdf_bytes
        except Exception as e:
            raise RuntimeError(f"PDF generation failed: {e}")
