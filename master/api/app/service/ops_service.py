"""Local lab ops: start/restart Xavier workers, detach-restart Master."""

import subprocess
import sys
from pathlib import Path

from app.model.schemas import OpsActionData, api_success
from app.service.exceptions import TaskFailedError, WorkerNotFoundError, WorkerOfflineError

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "start_xavier_workers.py"
RESTART_MASTER = ROOT / "scripts" / "restart_master.bat"
ALLOWED = {"worker-01", "worker-02", "worker-03", "worker-04"}


def _run_worker_script(worker_id: str, restart: bool):
    cmd = [sys.executable, str(SCRIPT), "--id", worker_id]
    if restart:
        cmd.append("--restart")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=70,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        raise TaskFailedError("Xavier 启动超时")
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode == 2:
        raise WorkerNotFoundError(worker_id)
    if "SSH_FAIL" in out:
        raise WorkerOfflineError(worker_id)
    if proc.returncode != 0:
        raise TaskFailedError("拉起失败。看 Master 日志或桌面一键启动。")
    already = "ALREADY_UP" in out
    return already, out


def start_worker(worker_id: str, restart: bool = False):
    if worker_id not in ALLOWED:
        raise WorkerNotFoundError(worker_id)
    action = "RESTART" if restart else "START"
    already, _out = _run_worker_script(worker_id, restart)
    if already and not restart:
        hint = "%s 已经在线，没有重复启动。" % worker_id
    elif restart:
        hint = "%s 已重启。刷新节点状态。" % worker_id
    else:
        hint = "%s 已启动。" % worker_id
    return api_success(
        OpsActionData(worker_id=worker_id, action=action, accepted=True, hint=hint),
        message=hint,
    )


def restart_master():
    if not RESTART_MASTER.exists():
        raise TaskFailedError("找不到 restart_master.bat")
    subprocess.Popen(
        ["cmd.exe", "/c", "start", "", str(RESTART_MASTER)],
        cwd=str(ROOT),
        close_fds=True,
    )
    hint = "调度中心正在重启，约 10 秒后自动刷新。若失败请用桌面 TradeMind-Lab。"
    return api_success(
        OpsActionData(worker_id=None, action="RESTART", accepted=True, hint=hint),
        message=hint,
    )
