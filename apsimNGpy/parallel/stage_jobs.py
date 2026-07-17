import json
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

QUEUE = "jobs:pending"


def job_generator(n=2_000_000):
    for i in range(n):
        yield {
            "job_id": f"sim_{i:07d}",
            "file": f"D:/simulations/sim_{i:07d}.apsimx",
            "status": "pending",
        }


def stage_jobs(job_iter, chunk_size=1000):
    pipe = r.pipeline()

    for count, job in enumerate(job_iter, start=1):
        job_id = job["job_id"]

        pipe.set(f"job:{job_id}", json.dumps(job))
        pipe.rpush(QUEUE, job_id)

        if count % chunk_size == 0:
            pipe.execute()
            pipe = r.pipeline()
            print(f"Staged {count} jobs")

    pipe.execute()
    print("Finished staging jobs")


if __name__ == "__main__":
    stage_jobs(job_generator())