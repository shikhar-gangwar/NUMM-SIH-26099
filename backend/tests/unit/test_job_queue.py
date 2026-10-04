import pytest
from app.jobs.queue import (
    DistributedJobQueue,
    InMemoryJobQueue,
    JobStatus,
    get_job_queue
)

def test_in_memory_job_queue_lifecycle():
    queue = InMemoryJobQueue()
    job_id = queue.enqueue(
        job_type="CATALOG_STREAM_INGESTION",
        payload={"cpse_code": "ONGC", "filename": "ongc_100k_materials.csv"}
    )
    assert job_id is not None
    
    # Check queued status
    record = queue.get_status(job_id)
    assert record is not None
    assert record.status == JobStatus.QUEUED
    assert record.progress_pct == 0.0

    # Progress update
    queue.update_progress(job_id, 45.5, current_state={"processed_rows": 45500})
    record = queue.get_status(job_id)
    assert record.progress_pct == 45.5
    assert record.result["processed_rows"] == 45500

    # Completion
    queue.complete(job_id, result={"total_materials_ingested": 100000, "status": "SUCCESS"})
    record = queue.get_status(job_id)
    assert record.status == JobStatus.COMPLETED
    assert record.progress_pct == 100.0

def test_job_queue_cancellation():
    queue = InMemoryJobQueue()
    job_id = queue.enqueue(job_type="DISTRIBUTED_BATCH_MATCH", payload={"batch_id": "b123"})
    assert queue.cancel(job_id) is True
    record = queue.get_status(job_id)
    assert record.status == JobStatus.CANCELLED
