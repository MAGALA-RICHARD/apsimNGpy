from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

app = FastAPI(title="APSIM Models.exe runner")

DEFAULT_TIMEOUT_SEC = 60 * 60
OUTPUT_EXTS = {".csv", ".txt", ".out", ".log"}
WORK_ROOT = Path("work").resolve()
WORK_ROOT.mkdir(parents=True, exist_ok=True)

os.environ['APSIM'] = r'D:\My_BOX\Box\PhD thesis\Objective two\morrow plots 20250821\APSIM2025.8.7844.0\bin'


def resolve_models_exe(user_supplied: Optional[str]) -> Path:
    candidates: List[Path] = []
    if user_supplied:
        candidates.append(Path(user_supplied))
    for envvar in ("APSIM_BIN_PATH", "MODELS", "APSIM"):
        p = os.getenv(envvar)
        if p:
            candidates.append(Path(p) / "Models.exe")
    which = shutil.which("Models.exe")
    if which:
        candidates.append(Path(which))

    for c in candidates:
        if c and c.exists() and c.is_file():
            return c.resolve()
    raise FileNotFoundError(
        "Models.exe not found. Supply exe_path or set APSIM_BIN_PATH/MODELS/APSIM or add to PATH."
    )


async def run_models(
        models_exe: Path,
        apsimx_path: Path,
        timeout_sec: int,
        extra_args: Optional[List[str]] = None,
        workdir: Optional[Path] = None,
) -> tuple[int, str, str]:
    args = [
        str(models_exe),
        "/Run",
        str(apsimx_path),
        "/Verbose",
        "/Csv",
    ]
    if extra_args:
        args.extend(extra_args)

    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=str(workdir or apsimx_path.parent),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"Models.exe timed out after {timeout_sec} s")

    return proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace")


SEM = asyncio.Semaphore(value=os.cpu_count() or 4)


class RunRequest(BaseModel):
    model_path: Optional[str] = Field(
        None, description="Path to .apsimx on server (use file upload endpoint otherwise)"
    )
    exe_path: Optional[str] = Field(
        None, description="Path to Models.exe (falls back to env/PATH if omitted)"
    )
    timeout_sec: int = Field(DEFAULT_TIMEOUT_SEC, ge=10, le=24 * 3600)
    extra_args: Optional[List[str]] = Field(
        default=None,
        description='Extra APSIM CLI args, e.g. ["\/Parallel", "4"]',
    )


@app.post("/run", response_class=PlainTextResponse)
async def run_from_path(req: RunRequest):
    models_exe = resolve_models_exe(req.exe_path)

    if not req.model_path:
        raise HTTPException(400, "model_path is required (or use /upload-run).")

    apsimx = Path(req.model_path).expanduser().resolve()
    if not apsimx.exists() or apsimx.suffix.lower() != ".apsimx":
        raise HTTPException(400, f"Invalid apsimx path: {apsimx}")

    job_dir = Path(tempfile.mkdtemp(prefix="apsim_", dir=str(WORK_ROOT)))
    model_copy = job_dir / apsimx.name
    shutil.copy2(apsimx, model_copy)

    async with SEM:
        try:
            code, out, err = await run_models(
                models_exe, model_copy, req.timeout_sec, req.extra_args, job_dir
            )
        except TimeoutError as e:
            raise HTTPException(504, str(e))

    log = f"Exit code: {code}\n\n--- STDOUT ---\n{out}\n\n--- STDERR ---\n{err}"
    if code != 0:
        raise HTTPException(500, log)
    return log


@app.post("/upload-run", response_class=PlainTextResponse)
async def upload_and_run(
        file: UploadFile = File(..., description="Upload a .apsimx model"),
        exe_path: Optional[str] = Form(default=None),
        timeout_sec: int = Form(default=DEFAULT_TIMEOUT_SEC),
        extra_args: Optional[str] = Form(default=None, description='Space-separated args, e.g. "/Parallel 4"'),
):
    if Path(file.filename).suffix.lower() != ".apsimx":
        raise HTTPException(400, "Please upload a .apsimx file")

    models_exe = resolve_models_exe(exe_path)
    job_dir = Path(tempfile.mkdtemp(prefix="apsim_", dir=str(WORK_ROOT)))
    dest = job_dir / Path(file.filename).name
    content = await file.read()
    dest.write_bytes(content)

    args_list = extra_args.split() if extra_args else None

    async with SEM:
        try:
            code, out, err = await run_models(models_exe, dest, timeout_sec, args_list, job_dir)
        except TimeoutError as e:
            raise HTTPException(504, str(e))

    log = f"Exit code: {code}\n\n--- STDOUT ---\n{out}\n\n--- STDERR ---\n{err}"
    if code != 0:
        raise HTTPException(500, log)
    return log


@app.get("/outputs/{job_id}")
def list_outputs(job_id: str):
    job_dir = WORK_ROOT / job_id
    if not job_dir.exists():
        raise HTTPException(404, "Unknown job_id")
    files = [p.name for p in job_dir.iterdir() if p.is_file() and p.suffix.lower() in OUTPUT_EXTS]
    return {"job_id": job_id, "files": files}


@app.get("/outputs/{job_id}/{filename}")
def download_output(job_id: str, filename: str):
    path = (WORK_ROOT / job_id / filename).resolve()
    if not path.exists() or path.suffix.lower() not in OUTPUT_EXTS:
        raise HTTPException(404, "File not found")
    if WORK_ROOT not in path.parents:
        raise HTTPException(400, "Invalid path")
    return FileResponse(path)

from typing import List, Optional  # (already imported in your file)

@app.post("/upload-run-multi", response_class=PlainTextResponse)
async def upload_and_run_multi(
    files: List[UploadFile] = File(..., description="Upload .apsimx plus any aux files (.met, .json, etc.)"),
    model_name: Optional[str] = Form(default=None, description="Which uploaded file is the .apsimx to run"),
    exe_path: Optional[str] = Form(default=None),
    timeout_sec: int = Form(default=DEFAULT_TIMEOUT_SEC),
    extra_args: Optional[str] = Form(default=None, description='Space-separated args, e.g. "/Parallel 4"'),
):
    # Resolve Models.exe
    models_exe = resolve_models_exe(exe_path)

    # New job directory
    job_dir = Path(tempfile.mkdtemp(prefix="apsim_", dir=str(WORK_ROOT)))

    # Save all files
    saved_paths: List[Path] = []
    for f in files:
        # prevent path traversal
        name = Path(f.filename).name
        dest = job_dir / name
        content = await f.read()
        dest.write_bytes(content)
        saved_paths.append(dest)

    # Pick the .apsimx to run
    apsimx_path: Optional[Path] = None
    if model_name:
        apsimx_path = job_dir / Path(model_name).name
        if not apsimx_path.exists() or apsimx_path.suffix.lower() != ".apsimx":
            raise HTTPException(400, f"model_name must be an uploaded .apsimx (got: {model_name})")
    else:
        # auto-detect: exactly one .apsimx required
        apsimx_candidates = [p for p in saved_paths if p.suffix.lower() == ".apsimx"]
        if len(apsimx_candidates) != 1:
            raise HTTPException(400, "Please upload exactly one .apsimx or specify model_name.")
        apsimx_path = apsimx_candidates[0]

    # Extra args parsing
    args_list = extra_args.split() if extra_args else None

    async with SEM:
        try:
            code, out, err = await run_models(models_exe, apsimx_path, timeout_sec, args_list, job_dir)
        except TimeoutError as e:
            raise HTTPException(504, str(e))

    log = (
        f"Job: {job_dir.name}\n"
        f"Model: {apsimx_path.name}\n"
        f"Exit code: {code}\n\n--- STDOUT ---\n{out}\n\n--- STDERR ---\n{err}"
    )
    if code != 0:
        raise HTTPException(500, log)
    return log

if __name__ == "__main__":
    import uvicorn

    # If this file is named e.g. apsimNGpy/cli/api_server.py:
    uvicorn.run(app, host="0.0.0.0", port=8000)
