# Changelog

## 2026-05-19 - PDF Knowledge Base Stabilization

This update completed phase 1 of the PDF knowledge base improvement plan. The goal was to make the existing ChromaDB + `all-MiniLM-L6-v2` pipeline stable, observable, and easy to rebuild before introducing retrieval-quality upgrades such as BM25, reranking, stronger embedding models, or structured PDF parsing.

Implemented changes:

- Stopped tracking generated Python `__pycache__/*.pyc` files.
- Kept `.venv/`, `knowledge_base/`, and Python cache files as local generated artifacts.
- Changed `pdf_search_status` to use lightweight ChromaDB metadata checks instead of loading the embedding model.
- Changed `scripts/build_knowledge_base.py --status` to use the same lightweight status path.
- Added more stable `chapter` metadata during PDF chunking.
- Fixed duplicate ChromaDB chunk IDs by including a text hash in chunk IDs.
- Verified a small sample build with `--limit 2 --rebuild --no-mirror`.

Validation performed:

- `python -m py_compile` passed for changed Python files.
- `python scripts/build_knowledge_base.py --status --no-mirror` passed.
- `python scripts/build_knowledge_base.py --limit 2 --rebuild --no-mirror` passed.
- MCP `pdf_search_status` passed.
- MCP `docs_list` passed.
- MCP `physics_get_guide heat_transfer` passed.
- MCP `comsol_status` passed.

Commits:

- `4956312 Stop tracking Python cache files`
- `473af5a Stabilize PDF knowledge base status`
