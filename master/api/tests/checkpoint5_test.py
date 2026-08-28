"""Checkpoint 5 acceptance: API boundary layer."""
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.config.settings import Settings, StorageSettings
from app.main import create_app
from app.model.schemas import TaskStatus, WorkerInfo, WorkerStatus
from app.service.task_service import TaskService
from app.service.task_storage import StorageError, TaskStorage

results = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))


def make_storage(tmp_root: Path) -> TaskStorage:
    data_root = tmp_root / "data"
    tasks_path = data_root / "tasks"
    results_path = data_root / "results"
    tasks_path.mkdir(parents=True, exist_ok=True)
    results_path.mkdir(parents=True, exist_ok=True)
    settings = Settings(storage=StorageSettings())
    type(settings).data_root = property(lambda self: data_root)
    type(settings).tasks_path = property(lambda self: tasks_path)
    type(settings).results_path = property(lambda self: results_path)
    return TaskStorage(settings)


def api_shape(body: dict) -> bool:
    return set(body.keys()) >= {"success", "message", "code", "data"}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        storage = make_storage(root)
        settings = storage._settings

        offline_worker = WorkerInfo(
            id="w1", name="w1", worker_type="indicator-worker",
            host="127.0.0.1", port=8080, status=WorkerStatus.OFFLINE,
        )
        registry = MagicMock()
        registry.list_workers.return_value = [offline_worker]
        registry.worker_base_url.return_value = "http://127.0.0.1:8080"

        service = TaskService(settings=settings, registry=registry, storage=storage)

        with patch("app.api.routes._task_service", service), patch("app.api.routes._worker_registry", registry):
            client = TestClient(create_app())

            # Test4 Health - not wrapped
            r = client.get("/health")
            check("Test4 health 200", r.status_code == 200)
            body = r.json()
            check("Test4 health not ApiResponse", "success" not in body and body.get("status") == "healthy")

            # Test3 GET /workers
            r = client.get("/workers")
            check("Test3 workers 200", r.status_code == 200)
            body = r.json()
            check("Test5 ApiResponse shape /workers", api_shape(body))
            check("Test5 workers success", body["success"] is True and body["code"] == "TM-0000")
            check("Test3 workers data", "workers" in body["data"] and "count" in body["data"])

            # Test12 Worker OFFLINE -> TM-1002
            r = client.post("/task", json={
                "indicator": "MA",
                "data": {"close": [1, 2, 3]},
                "params": {},
            })
            check("Test12 offline not 500", r.status_code == 200)
            body = r.json()
            check("Test12 TM-1002", body["code"] == "TM-1002", body.get("code"))
            check("Test12 ApiResponse shape", api_shape(body))
            check("Test12 has task data", body["data"] is not None and body["data"]["status"] == "FAILED")

            # Test10 invalid request {}
            r = client.post("/task", json={})
            check("Test10 invalid not 500", r.status_code == 422)
            body = r.json()
            check("Test10 unified error", body["success"] is False and body["code"] == "TM-1003")
            check("Test10 data null", body["data"] is None)

            # Test1 POST /task with mocked online worker
            online_worker = WorkerInfo(
                id="w2", name="w2", worker_type="indicator-worker",
                host="127.0.0.1", port=8080, status=WorkerStatus.ONLINE, latency_ms=5,
            )
            registry.list_workers.return_value = [online_worker]
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {"indicator": "MA", "values": [1, 2, 3]}
            with patch("app.service.task_service.requests.post", return_value=mock_resp):
                r = client.post("/task", json={
                    "indicator": "MA",
                    "data": {"close": [1, 2, 3]},
                    "params": {},
                })
            check("Test1 post task 200", r.status_code == 200)
            body = r.json()
            check("Test1 ApiResponse", api_shape(body) and body["success"] is True)
            task_id = body["data"]["task_id"]
            check("Test1 task completed", body["data"]["status"] == "COMPLETED")

            # Test2 GET /task
            r = client.get(f"/task/{task_id}")
            check("Test2 get task 200", r.status_code == 200)
            body = r.json()
            check("Test2 ApiResponse", api_shape(body) and body["success"] is True)
            check("Test9 result_exists true", body["data"].get("result_exists") is True)

            # Test9 delete result, result_exists false
            meta = storage.load_metadata(task_id)
            abs_path = storage.result_absolute_path(meta["result_path"])
            abs_path.unlink()
            r = client.get(f"/task/{task_id}")
            body = r.json()
            check("Test9 result_exists false", body["data"].get("result_exists") is False)
            check("Test9 status completed", body["data"]["status"] == "COMPLETED")

            # Test11 non-existent task
            r = client.get("/task/tm-task-20990101-999999")
            check("Test11 not 500", r.status_code == 404)
            body = r.json()
            check("Test11 unified error", body["success"] is False and body["code"] == "TM-1003")
            check("Test11 no traceback", "Traceback" not in r.text)

            # Test13 StorageError
            with patch.object(storage, "load_metadata", side_effect=StorageError("corrupt")):
                with patch("app.api.routes._task_service", TaskService(settings=settings, registry=registry, storage=storage)):
                    client2 = TestClient(create_app())
                    created = TaskStorage.now()
                    tid = storage.generate_task_id(created)
                    r = client2.get(f"/task/{tid}")
            check("Test13 storage error not 500 traceback", "Traceback" not in r.text)
            check("Test13 TM-1003", r.json().get("code") == "TM-1003", str(r.json()))

            # Test7 worker offline already covered by Test12

    print()
    print("=== SUMMARY ===")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"PASS: {passed}, FAIL: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())