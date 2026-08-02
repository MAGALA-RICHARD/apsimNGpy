import json
import os
from pathlib import Path

import redis
from apsimNGpy import ApsimModel
from apsimNGpy.core_utils.database_utils import dispose, write_df_to_sql

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

QUEUE = "jobs:pending"
RUNNING = "jobs:running"
COMPLETED = "jobs:completed"
FAILED = "jobs:failed"


def run_job(file: str, db: str, reports=None) -> dict:
    """
    Run one APSIM file and write results to an external SQLite database.
    """
    file_path = Path(file).resolve()
    db_path = Path(db).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"APSIM file not found: {file_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Dispose only the target database connection, if needed
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


if __name__ == "__main__":
    worker_loop(timeout=10)