from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import pdfplumber


def extract_text_from_pdf(path: Path) -> list:
    try:
        with pdfplumber.open(path) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages):
                page_content = []

                # extract tables as markdown first
                table_bboxes = [t.bbox for t in page.find_tables()]
                for table in page.extract_tables():
                    table_md = _table_to_markdown(table)
                    if table_md:
                        page_content.append(table_md)

                # crop out table areas before extracting text
                cropped_page = page
                for bbox in table_bboxes:
                    cropped_page = cropped_page.outside_bbox(bbox)

                text = cropped_page.extract_text() or ""
                if text.strip():
                    page_content.append(text)

                pages.append(Document(
                    page_content="\n\n".join(page_content),
                    metadata={"source": str(path), "page": i}
                ))

            if pages:
                return pages

    except Exception:
        pass

    # fallback — no table preservation
    try:
        loader = PyPDFLoader(str(path))
        return loader.load()
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed for {path}: {e}")


def _table_to_markdown(table: list) -> str:
    if not table:
        return ""

    rows = []
    for row in table:
        cleaned = [str(cell).strip() if cell is not None else "" for cell in row]
        rows.append("| " + " | ".join(cleaned) + " |")

    if len(rows) >= 1:
        col_count = len(table[0])
        separator = "| " + " | ".join(["---"] * col_count) + " |"
        rows.insert(1, separator)

    return "\n".join(rows)