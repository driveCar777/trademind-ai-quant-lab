"""Checkpoint 4 acceptance: TaskStorage atomic writes and unified I/O."""
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import Settings, StorageSettings
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

    settings = Settings(
        storage=StorageSettings(root="data", tasks_dir="tasks", results_dir="results")
    )
    type(settings).data_root = property(lambda self: data_root)
    type(settings).tasks_path = property(lambda self: tasks_path)
    type(settings).results_path = property(lambda self: results_path)
    return TaskStorage(settings)


def sample_metadata(storage: TaskStorage, task_id: str, created_at: datetime) -> dict:
    result_path = storage.plan_result_path(task_id, created_at)
    return storage.create_metadata(
        task_id=task_id,
        worker_type="indicator-worker",
        result_path=result_path,
        created_at=created_at,
        request={"indicator": "MA", "data": {}, "params": {}},
    )


def test1_metadata_atomic(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    sample_metadata(storage, task_id, created)
    path = storage._task_file(task_id)
    check("Test1 metadata file exists", path.exists(), str(path))
    content = path.read_text(encoding="utf-8")
    check("Test1 metadata readable JSON", json.loads(content)["task_id"] == task_id)
    tmp_files = list(storage._tasks_path.glob("*.tmp"))
    check("Test1 no tmp leftovers", len(tmp_files) == 0, str(len(tmp_files)))


def test2_result_atomic(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    meta = sample_metadata(storage, task_id, created)
    result_path = meta["result_path"]
    payload = {"indicator": "MA", "values": [1, 2, 3]}
    abs_path = storage.save_result(result_path, payload)
    check("Test2 result file exists", abs_path.exists(), str(abs_path))
    loaded = json.loads(abs_path.read_text(encoding="utf-8"))
    check("Test2 result content correct", loaded == payload)
    check("Test2 UTF-8 indent readable", "\n" in abs_path.read_text(encoding="utf-8"))
    tmp_files = list(abs_path.parent.glob("*.tmp"))
    check("Test2 no tmp leftovers", len(tmp_files) == 0)


def test3_recovery(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    meta = sample_metadata(storage, task_id, created)
    meta = storage.transition_status(meta, "RUNNING", started_at=created)
    recovered = storage.load_metadata(task_id)
    check("Test3 recovery metadata readable", recovered is not None)
    check("Test3 status preserved", recovered["status"] == "RUNNING")
    check("Test3 result_path preserved", recovered["result_path"] == meta["result_path"])


def test4_exists(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    check("Test4 exists before create", not storage.exists(task_id))
    sample_metadata(storage, task_id, created)
    check("Test4 exists after create", storage.exists(task_id))


def test5_list_tasks(storage: TaskStorage):
    base = TaskStorage.now()
    ids = []
    for i in range(3):
        created = base + timedelta(seconds=i)
        tid = storage.generate_task_id(created)
        sample_metadata(storage, tid, created)
        ids.append(tid)
    listed = storage.list_tasks()
    check("Test5 list count", len(listed) == 3, str(len(listed)))
    created_times = [r["created_at"] for r in listed]
    check("Test5 sorted by created_at", created_times == sorted(created_times))


def test6_load_result(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    meta = sample_metadata(storage, task_id, created)
    payload = {"ok": True, "data": [1]}
    storage.save_result(meta["result_path"], payload)
    loaded = storage.load_result(meta["result_path"])
    check("Test6 load_result", loaded == payload)
    check("Test6 result_exists", storage.result_exists(meta["result_path"]))


def test7_counter_100(storage: TaskStorage):
    created = TaskStorage.now()
    ids = [storage.generate_task_id(created) for _ in range(100)]
    check("Test7 100 ids generated", len(ids) == 100)
    check("Test7 no duplicates", len(set(ids)) == 100, f"unique={len(set(ids))}")
    check("Test7 counter file exists", storage._counter_path.exists())


def test8_counter_1000(storage: TaskStorage):
    created = TaskStorage.now()
    ids = [storage.generate_task_id(created) for _ in range(1000)]
    check("Test8 1000 ids generated", len(ids) == 1000)
    check("Test8 no duplicates", len(set(ids)) == 1000, f"unique={len(set(ids))}")
    nums = [int(t.split("-")[-1]) for t in ids]
    check("Test8 sequential counters", nums == list(range(1, 1001)), f"first={nums[:3]}, last={nums[-3:]}")


def test9_missing_result(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    meta = sample_metadata(storage, task_id, created)
    started = created
    finished = created + timedelta(milliseconds=50)
    meta = storage.transition_status(meta, "RUNNING", started_at=started)
    result_path = meta["result_path"]
    storage.save_result(result_path, {"value": 42})
    meta = storage.transition_status(meta, "COMPLETED", finished_at=finished)
    abs_path = storage.result_absolute_path(result_path)
    abs_path.unlink()
    check("Test9 result file deleted", not abs_path.exists())
    loaded_meta = storage.load_metadata(task_id)
    check("Test9 metadata still readable", loaded_meta["status"] == "COMPLETED")
    result = storage.load_result(result_path)
    check("Test9 load_result returns None when missing", result is None)
    check("Test9 result_exists false", not storage.result_exists(result_path))
    try:
        result_exists = storage.result_exists(result_path)
        response = {"status": loaded_meta["status"], "result_exists": result_exists}
        check("Test9 graceful response shape", response == {"status": "COMPLETED", "result_exists": False})
    except Exception as exc:
        check("Test9 no crash on missing result", False, str(exc))


def test_corrupt_metadata_raises(storage: TaskStorage):
    created = TaskStorage.now()
    task_id = storage.generate_task_id(created)
    path = storage._task_file(task_id)
    path.write_text("{not valid json", encoding="utf-8")
    raised = False
    try:
        storage.load_metadata(task_id)
    except StorageError:
        raised = True
    check("Corrupt metadata raises StorageError", raised)


def test_cleanup_interface(storage: TaskStorage):
    try:
        storage.cleanup()
        check("cleanup() callable", True)
    except Exception as exc:
        check("cleanup() callable", False, str(exc))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        test1_metadata_atomic(make_storage(root / "t1"))
        test2_result_atomic(make_storage(root / "t2"))
        test3_recovery(make_storage(root / "t3"))
        test4_exists(make_storage(root / "t4"))
        test5_list_tasks(make_storage(root / "t5"))
        test6_load_result(make_storage(root / "t6"))
        test7_counter_100(make_storage(root / "t7"))
        test8_counter_1000(make_storage(root / "t8"))
        test9_missing_result(make_storage(root / "t9"))
        test_corrupt_metadata_raises(make_storage(root / "terr"))
        test_cleanup_interface(make_storage(root / "tcleanup"))

    print()
    print("=== SUMMARY ===")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"PASS: {passed}, FAIL: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())