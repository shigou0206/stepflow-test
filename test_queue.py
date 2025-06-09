import asyncio
import httpx
import uuid
import json

BASE_URL = "http://127.0.0.1:3000"

async def enqueue_task():
    run_id = str(uuid.uuid4())
    state_name = "TestState"
    task = {
        "run_id": run_id,
        "state_name": state_name,
        "input": {"key": "value"},
        "task_type": "http",
        "priority": 128
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/v1/worker/update", json={
            "run_id": run_id,
            "state_name": state_name,
            "status": "PROCESSING",
            "result": task["input"]
        })
        print("Enqueue (update fake):", resp.status_code, resp.text)

    return run_id, state_name

async def poll_task(worker_id="python-worker-1"):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/v1/worker/poll", json={
            "worker_id": worker_id,
            "capabilities": ["http"]
        })
        print("Poll:", resp.status_code, resp.json())
        return resp.json()

async def update_task(run_id, state_name, status="SUCCEEDED", result={"out": "ok"}):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/v1/worker/update", json={
            "run_id": run_id,
            "state_name": state_name,
            "status": status,
            "result": result
        })
        print("Update:", resp.status_code, resp.text)

async def main():
    run_id, state_name = await enqueue_task()
    await asyncio.sleep(1)

    task = await poll_task()
    if task.get("has_task"):
        await update_task(task["run_id"], task["state_name"])

if __name__ == "__main__":
    asyncio.run(main())