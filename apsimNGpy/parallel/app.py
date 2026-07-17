import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import redis
from fastapi import FastAPI
from pydantic import BaseModel

from apsimNGpy import ApsimModel
from apsimNGpy.core_utils.database_utils import dispose, write_df_to_sql


app = FastAPI()

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

QUEUE = "jobs:pending"
RUNNING = "jobs:running"
COMPLETED = "jobs:completed"
FAILED = "jobs:failed"
WORKERS = "jobs:workers"


class JobIn(BaseModel):
    job_id: str
    file: str
    db: str
    reports: Optional[str] = None


class WorkerRequest(BaseModel):
    n_workers: int = 4


def run_job(file: str, db: str, reports=None) -> dict:
    file_path = Path(file).resolve()
    db_path = Path(db).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"APSIM file not found: {file_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    dispose(db_path)

    model = ApsimModel(str(file_path))

    with model.run(report_name=reports):
        df = model.results

    table_name = file_path.stem.replace("-", "_").replace(" ", "_")

    write_df_to_sql(
        out=df,
        db_or_con=db_path,
        table_name=table_name,
        if_exists="replace",
        index=False,
        chunk_size=None,
    )

    return {
        "file": str(file_path),
        "db": str(db_path),
        "table": table_name,
        "rows": int(len(df)),
    }


def worker_loop(timeout: int = 10) -> None:
    worker_id = f"worker-{os.getpid()}"
    print(f"{worker_id} started")

    r.ping()

    while True:
        item = r.blpop(QUEUE, timeout=timeout)

        if item is None:
            print(f"{worker_id}: no jobs found for {timeout} seconds. Exiting.")
            break

        _, job_id = item

        job_key = f"job:{job_id}"
        raw_job = r.get(job_key)

        if raw_job is None:
            print(f"{worker_id}: missing job metadata for {job_id}")
            continue

        job = json.loads(raw_job)

        try:
            job["status"] = "running"
            job["worker"] = worker_id
            r.set(job_key, json.dumps(job))
            r.sadd(RUNNING, job_id)

            result = run_job(
                file=job["file"],
                db=job["db"],
                reports=job.get("reports", None),
            )

            job["status"] = "completed"
            job["result"] = result
            r.set(job_key, json.dumps(job))

            r.sadd(COMPLETED, job_id)

            print(f"{worker_id} completed {job_id}")

        except Exception as e:
            job["status"] = "failed"
            job["worker"] = worker_id
            job["error"] = repr(e)
            r.set(job_key, json.dumps(job))

            r.sadd(FAILED, job_id)

            print(f"{worker_id} failed {job_id}: {e}")

        finally:
            r.srem(RUNNING, job_id)

    print(f"{worker_id} closed cleanly")


@app.get("/")
def home():
    return {"message": "APSIM Redis worker API is running"}


@app.post("/stage")
def stage_job(job: JobIn):
    payload = job.model_dump()
    payload["status"] = "pending"

    r.set(f"job:{job.job_id}", json.dumps(payload))
    r.rpush(QUEUE, job.job_id)

    return {
        "message": "job staged",
        "job_id": job.job_id,
    }


@app.post("/run-workers")
def run_workers(request: WorkerRequest):
    started = []

    for i in range(request.n_workers):
        p = subprocess.Popen(
            [
                sys.executable,
                __file__,
                "worker",
            ]
        )

        r.sadd(WORKERS, p.pid)

        started.append(
            {
                "worker_number": i + 1,
                "pid": p.pid,
            }
        )

    return {
        "message": "workers started",
        "workers": started,
    }


@app.get("/status")
def status():
    return {
        "pending": r.llen(QUEUE),
        "running": r.scard(RUNNING),
        "completed": r.scard(COMPLETED),
        "failed": r.scard(FAILED),
        "workers": list(r.smembers(WORKERS)),
    }


@app.get("/job/{job_id}")
def get_job(job_id: str):
    raw_job = r.get(f"job:{job_id}")

    if raw_job is None:
        return {"error": f"job {job_id} not found"}

    return json.loads(raw_job)


@app.post("/clear")
def clear_jobs():
    r.delete(QUEUE)
    r.delete(RUNNING)
    r.delete(COMPLETED)
    r.delete(FAILED)
    r.delete(WORKERS)

    for key in r.scan_iter("job:*"):
        r.delete(key)

    return {"message": "all job keys cleared"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        worker_loop(timeout=10)