import json
import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8081"
API_STREAM_URL = f"{API_BASE}/chat/stream"
API_DOCS_URL = f"{API_BASE}/documents"

st.set_page_config(page_title="Health Insurance RAG", layout="wide")
st.title("Health Insurance RAG")

st.warning(
    "**Disclaimer:** This is an educational demo. It does not provide medical, legal, or "
    "enrollment advice. Do not upload PHI (real SSNs, member IDs, or personal health records).",
    icon="⚠️",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Upload a PDF to index", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Index Document"):
            with st.spinner("Uploading…"):
                try:
                    resp = requests.post(
                        f"{API_DOCS_URL}/",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                        timeout=30,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("already_exists"):
                        st.info(f"Already indexed: **{data['data']['filename']}**")
                    else:
                        st.success(
                            f"Queued for indexing: **{data['data']['filename']}**  \n"
                            "Status will update to *ready* in ~30–60 s."
                        )
                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach API. Make sure the server is running on port 8081.")
                except requests.exceptions.HTTPError as e:
                    st.error(f"Upload failed: {e.response.json().get('detail', str(e))}")

    st.divider()
    st.header("Knowledge Base")

    if st.button("Refresh documents"):
        st.session_state.pop("doc_list", None)

    if "doc_list" not in st.session_state:
        try:
            r = requests.get(f"{API_DOCS_URL}/", timeout=10)
            r.raise_for_status()
            st.session_state.doc_list = r.json().get("documents", [])
        except Exception:
            st.session_state.doc_list = []

    docs = st.session_state.get("doc_list", [])
    if not docs:
        st.caption("No documents indexed yet.")
    else:
        for doc in docs:
            status = doc.get("status", "unknown")
            source_type = doc.get("source_type", "upload")
            status_badge = {"ready": "🟢", "processing": "🟡", "failed": "🔴"}.get(status, "⚪")
            type_badge = "seed" if source_type == "seed" else "uploaded"
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"{status_badge} **{doc.get('filename', 'unknown')}**  \n`{type_badge}` — *{status}*")
            with col2:
                if st.button("✕", key=f"del_{doc['id']}", help="Delete"):
                    try:
                        requests.delete(f"{API_DOCS_URL}/{doc['id']}", timeout=10)
                        st.session_state.pop("doc_list", None)
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))

    st.divider()
    st.header("Retrieval Settings")
    k = st.slider("Chunks to retrieve (k)", 1, 20, 5)
    alpha = st.slider(
        "Vector weight (alpha)", 0.0, 1.0, 0.5, 0.05,
        help="0 = BM25 only, 1 = vector only",
    )

# ── Chat ─────────────────────────────────────────────────────────────────────
question = st.chat_input("Ask a question about your documents…")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        answer_box = st.empty()
        full_answer = ""
        sources = []

        try:
            with requests.post(
                API_STREAM_URL,
                json={"message": question, "k": k, "alpha": alpha},
                stream=True,
                timeout=300,
            ) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines():
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if not line.startswith("data: "):
                        continue
                    payload = json.loads(line[len("data: "):])
                    if "token" in payload:
                        full_answer += payload["token"]
                        answer_box.markdown(full_answer + "▌")
                    if payload.get("done"):
                        sources = payload.get("sources", [])

            answer_box.markdown(full_answer)

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Make sure the server is running on port 8081.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"API error: {e}")
            st.stop()

        if sources:
            with st.expander(f"Sources ({len(sources)} chunks)"):
                for i, src in enumerate(sources, 1):
                    meta = src.get("metadata", {})
                    label = meta.get("filename") or meta.get("source") or f"Chunk {i}"
                    page = meta.get("page", "")
                    st.markdown(f"**{i}. {label}**" + (f" — p. {page}" if page != "" else ""))
                    st.caption(src["content"])
