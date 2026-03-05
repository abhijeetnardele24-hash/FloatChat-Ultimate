"""Lightweight in-memory background job queue with progress tracking."""

from __future__ import annotations

import time
import traceback
import uuid
from queue import Empty, Queue
from threading import Lock, Thread
from typing import Any, Callable, Dict, Optional


JobHandler = Callable[[Dict[str, Any], Callable[[int, Optional[str]], None]], Dict[str, Any]]


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._jobs_lock = Lock()
        self._queue: Queue = Queue()
        self._worker = Thread(target=self._run_worker, daemon=True)
        self._worker.start()

    def submit(self, job_type: str, payload: Dict[str, Any], handler: JobHandler) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = time.time()
        job = {
            "id": job_id,
            "job_type": job_type,
            "status": "queued",
            "progress": 0,
            "message": "Queued",
            "payload_meta": payload,
            "result": None,
            "error": None,
            "created_at_ts": now,
            "started_at_ts": None,
            "completed_at_ts": None,
        }
        with self._jobs_lock:
            self._jobs[job_id] = job
        self._queue.put((job_id, payload, handler))
        return self._serialize_job(job)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return self._serialize_job(job)

    def list(self, limit: int = 50) -> list[Dict[str, Any]]:
        with self._jobs_lock:
            jobs = list(self._jobs.values())
        jobs_sorted = sorted(jobs, key=lambda j: j.get("created_at_ts", 0), reverse=True)
        return [self._serialize_job(job) for job in jobs_sorted[: max(1, min(limit, 200))]]

    def _update_job(self, job_id: str, **updates: Any) -> None:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.update(updates)

    def _make_progress_callback(self, job_id: str) -> Callable[[int, Optional[str]], None]:
        def _progress(progress: int, message: Optional[str] = None) -> None:
            safe_progress = max(0, min(int(progress), 100))
            updates: Dict[str, Any] = {"progress": safe_progress}
            if message is not None:
                updates["message"] = str(message)[:500]
            self._update_job(job_id, **updates)

        return _progress

    def _run_worker(self) -> None:
        while True:
            try:
                job_id, payload, handler = self._queue.get(timeout=0.25)
            except Empty:
                continue

            started_at = time.time()
            self._update_job(job_id, status="running", started_at_ts=started_at, progress=5, message="Started")
            progress_cb = self._make_progress_callback(job_id)

            try:
                result = handler(payload, progress_cb)
                completed_at = time.time()
                self._update_job(
                    job_id,
                    status="completed",
                    progress=100,
                    message="Completed",
                    result=result,
                    completed_at_ts=completed_at,
                )
            except Exception as exc:
                completed_at = time.time()
                self._update_job(
                    job_id,
                    status="failed",
                    progress=100,
                    message="Failed",
                    error={
                        "message": str(exc),
                        "traceback": traceback.format_exc(limit=20),
                    },
                    completed_at_ts=completed_at,
                )

    @staticmethod
    def _serialize_job(job: Dict[str, Any]) -> Dict[str, Any]:
        def _iso(ts: Optional[float]) -> Optional[str]:
            if ts is None:
                return None
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

        return {
            "id": job.get("id"),
            "job_type": job.get("job_type"),
            "status": job.get("status"),
            "progress": job.get("progress"),
            "message": job.get("message"),
            "payload_meta": job.get("payload_meta"),
            "result": job.get("result"),
            "error": job.get("error"),
            "created_at": _iso(job.get("created_at_ts")),
            "started_at": _iso(job.get("started_at_ts")),
            "completed_at": _iso(job.get("completed_at_ts")),
        }


_JOB_QUEUE = InMemoryJobQueue()


def get_job_queue() -> InMemoryJobQueue:
    return _JOB_QUEUE
