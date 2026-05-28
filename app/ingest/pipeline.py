from sqlalchemy.orm import Session
from app.models.document import Document
from app.ingest.parser import extract_text_from_pdf
from app.ingest.chunker import chunk_text
from app.ingest.embedder import embed_and_store
from pathlib import Path


def run_pipeline(doc: Document):#, db: Session):
    try:
        doc.status = "parsing"
        #db.commit()
        pages = extract_text_from_pdf(Path(doc.filepath))

        doc.status = "chunking"
        #db.commit()
        chunks = chunk_text(pages)

        doc.status = "embedding"
        #db.commit()
        embed_and_store(chunks, doc_id=doc.id)

        doc.status = "done"
        #db.commit()

    except Exception as e:
        print(e)
     #   doc.status = "failed"
      #  doc.error = str(e)
       # db.commit()
        #raise


run_pipeline(...data\seed\4b8c5354-ca6a-45cd-b57a-c94aa69e9b49.pdf)