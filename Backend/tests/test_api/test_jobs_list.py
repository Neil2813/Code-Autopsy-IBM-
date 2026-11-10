import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.api.v1.jobs import list_jobs


def test_list_jobs_uses_stored_filename_when_project_name_is_missing():
    job = SimpleNamespace(
        id="job-123",
        job_metadata={"original_filename": "snippet.java"},
        files=[SimpleNamespace(file_path="uploads\\job-123\\snippet.java")],
        status=SimpleNamespace(value="completed"),
        progress=100,
        created_at=datetime(2026, 11, 10),
    )
    repository = Mock()
    repository.list_jobs.return_value = [job]

    with patch("app.api.v1.jobs.get_job_repository", return_value=repository):
        response = asyncio.run(list_jobs(limit=50, offset=0, status=None, db=Mock()))

    assert response["total"] == 1
    assert response["jobs"][0]["project_name"] == "snippet.java"