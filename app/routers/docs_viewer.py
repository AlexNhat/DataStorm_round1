"""
Router phục vụ tài liệu và notebook viewer cho UI.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from typing import List
import os

from starlette.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = (BASE_DIR / "docs").resolve()
NOTEBOOKS_DIR = (BASE_DIR / "notebooks").resolve()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

router = APIRouter()


def list_files(base: Path) -> List[dict]:
    items = []
    if base.exists():
        for path in sorted(base.rglob("*")):
            if path.is_file():
                rel = path.relative_to(base).as_posix()
                items.append({
                    "name": path.name,
                    "rel_path": rel,
                    "size_kb": round(path.stat().st_size / 1024, 2),
                    "updated": path.stat().st_mtime
                })
    return items


def resolve_path(base: Path, file_path: str) -> Path:
    target = (base / file_path).resolve()
    if base not in target.parents and target != base:
        raise HTTPException(status_code=400, detail="Đường dẫn không hợp lệ")
    return target


@router.get("/doc-files/", response_class=HTMLResponse)
async def docs_index(request: Request):
    files = list_files(DOCS_DIR)
    return templates.TemplateResponse(
        "doc_files_index.html",
        {"request": request, "files": files, "title": "Tài liệu (docs)"}
    )


@router.get("/doc-files/{file_path:path}", response_class=HTMLResponse)
async def doc_file(request: Request, file_path: str, download: bool = Query(False)):
    if not file_path:
        return await docs_index(request)
    target = resolve_path(DOCS_DIR, file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    if download:
        return FileResponse(target, filename=target.name)
    content = target.read_text(encoding="utf-8", errors="ignore")
    html_content = None
    try:
        import markdown
        html_content = markdown.markdown(content)
    except Exception:
        pass
    return templates.TemplateResponse(
        "doc_file_view.html",
        {
            "request": request,
            "file_name": target.name,
            "rel_path": file_path,
            "content": content if html_content is None else None,
            "html_content": html_content,
        }
    )


@router.get("/notebooks/", response_class=HTMLResponse)
async def notebooks_index(request: Request):
    files = list_files(NOTEBOOKS_DIR)
    return templates.TemplateResponse(
        "notebook_files_index.html",
        {"request": request, "files": files, "title": "Notebooks"}
    )


@router.get("/notebooks/{file_path:path}", response_class=HTMLResponse)
async def notebook_file(request: Request, file_path: str, download: bool = Query(False)):
    if not file_path:
        return await notebooks_index(request)
    target = resolve_path(NOTEBOOKS_DIR, file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Notebook không tồn tại")
    if download:
        return FileResponse(target, filename=target.name, media_type="application/octet-stream")
    raw_preview = target.read_text(encoding="utf-8", errors="ignore")
    return templates.TemplateResponse(
        "notebook_file_view.html",
        {
            "request": request,
            "file_name": target.name,
            "rel_path": file_path,
            "raw_preview": raw_preview[:20000],  # limit preview
        }
    )
