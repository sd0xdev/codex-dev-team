#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Launch Claude Code with Remote Control in tmux; dispatch only after PM readback.
Print mode requires an explicit, user-authorized --no-rc-reason.

Subcommands:
  launch  --repo R --mission M --runs-root D --model ID --permission-mode MODE [--effort LEVEL] [options]
  resume  --from RUN_DIR --mission M [options]
  dispatch RUN_DIR --remote-url URL --actual-model ID --confirm-rc-active-and-idle
  status  RUN_DIR [--json] [--result-chars N]

Every launch/resume creates a new 0700 run directory and never reuses or overwrites one.
Every tmux call names its server explicitly with `tmux -S <socket>` (default: an owned socket
`<runs-root>/tmux.sock`) and runs with TMUX/TMUX_TMPDIR removed, so an inherited $TMUX can never
redirect a call to another server. The socket is recorded in meta.json for status/resume. The
helper never runs kill-server.
`status` derives a state from the exit marker, the stream and tmux; it never treats a live
process, exit 0 or Claude's own prose as acceptance.
"""
import argparse
import pwd
import socket as host_socket
import uuid
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

FORBIDDEN_MODES = {"bypassPermissions"}
SETENV_RESERVED = {"HOME", "CODEX_HOME", "PATH"}  # compared case-insensitively: `home` is refused too
SETENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")  # portable ASCII shell name; anything else would fail `export`
PERMISSION_MODES = ["default", "auto", "acceptEdits", "manual", "dontAsk", "plan"]  # Check the installed CLI before selecting a mode.


def die(code, msg):
    print(f"{code}: {msg}", file=sys.stderr)
    sys.exit(2)


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def models_match(requested, actual):
    """Compare model IDs, allowing only the optional trailing [1m] qualifier.

    Keep the original values in metadata; this does not verify context capacity.
    """
    if not isinstance(requested, str) or not isinstance(actual, str):
        return False
    requested_base = requested.removesuffix("[1m]")
    actual_base = actual.removesuffix("[1m]")
    return bool(requested_base) and requested_base == actual_base


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True)
    if check and p.returncode != 0:
        die("COMMAND_FAILED", f"{' '.join(cmd)}: {p.stderr.decode(errors='replace').strip()}")
    return p


def git(repo, *args, check=True):
    return run(["git", "-C", str(repo), *args], check=check).stdout


def fingerprint(repo):
    """Repo identity plus a hash of the whole dirty state (tracked diff and untracked contents)."""
    top = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    head = git(top, "rev-parse", "HEAD", check=False).decode().strip() or None
    branch = git(top, "branch", "--show-current", check=False).decode().strip() or None
    h = hashlib.sha256()
    h.update(git(top, "diff", "HEAD", "--binary", check=False))
    untracked = [u for u in git(top, "ls-files", "--others", "--exclude-standard", "-z").decode().split("\0") if u]
    for rel in sorted(untracked):
        h.update(b"\0U\0" + rel.encode())
        f = top / rel
        if f.is_file() and not f.is_symlink():
            h.update(hashlib.sha256(f.read_bytes()).digest())
    status = git(top, "status", "--porcelain=v1", "-z").decode().split("\0")
    return {
        "repo": str(top), "head": head, "branch": branch,
        "dirty_entries": len([s for s in status if s]),
        "dirty_hash": "sha256:" + h.hexdigest(),
        "index_entries": len([x for x in git(top, "diff", "--cached", "--name-only", "-z").decode().split("\0") if x]),
        "stash_entries": len([x for x in git(top, "stash", "list").decode().splitlines() if x]),
    }


def inside(child, parent):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


RUN_DIR_PREFIXES = ("launch-", "resume-")


def check_runs_root(runs_root, repo):
    runs_root = runs_root.resolve()
    if runs_root.exists():
        foreign = [p.name for p in runs_root.iterdir()
                   if not (p.is_dir() and p.name.startswith(RUN_DIR_PREFIXES)) and p.name != "tmux.sock"]
        if foreign:
            die("RUNS_ROOT_NOT_DEDICATED", f"{runs_root} holds non-run entries {sorted(foreign)[:5]}; use a dedicated directory so no evidence can be overwritten")
    if inside(runs_root, repo):
        probe = runs_root.relative_to(repo) / "probe"
        if run(["git", "-C", str(repo), "check-ignore", "-q", str(probe)], check=False).returncode != 0:
            die("RUNS_ROOT_TRACKED", f"{runs_root} is inside the repo and not git-ignored; it would move the dirty baseline")
    return runs_root


def write_new(path, data, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())
    os.chmod(path, mode)


MAX_SOCKET_PATH = 100  # sun_path is 104 bytes on macOS, 108 on Linux


def tmux_env():
    env = dict(os.environ)
    env.pop("TMUX", None)
    env.pop("TMUX_TMPDIR", None)
    return env


def tmux(socket, *args, check=True):
    p = subprocess.run(["tmux", "-S", str(socket), *args], capture_output=True, env=tmux_env())
    if check and p.returncode != 0:
        die("TMUX_FAILED", f"tmux -S {socket} {' '.join(args)}: {p.stderr.decode(errors='replace').strip()}")
    return p


def tmux_alive(socket, name):
    """True only if the named session exists on that exact server. A missing server is False, never success."""
    if not socket or not name or not shutil.which("tmux") or not Path(socket).exists():
        return False
    return tmux(socket, "has-session", "-t", f"={name}", check=False).returncode == 0


def session_processes(session_id):
    if not session_id:
        return []
    out = run(["ps", "-axo", "pid=,command="], check=False).stdout.decode(errors="replace")
    me = os.getpid()
    pids = []
    for line in out.splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if session_id in cmd and "claude_run.py" not in cmd and pid.isdigit() and int(pid) != me:
            pids.append(int(pid))
    return pids


def runner_alive(run_dir):
    """PID of this run's run.sh if it is still alive (covers first launches, whose argv has no session id)."""
    try:
        pid = int((run_dir / "runner.pid").read_text().strip())
    except (OSError, ValueError):
        return None
    cmd = run(["ps", "-p", str(pid), "-o", "command="], check=False).stdout.decode(errors="replace")
    return pid if str(run_dir / "run.sh") in cmd else None


def parse_stream(path, result_chars=0):
    info = {"session_id": None, "actual_model": None, "claude_code_version": None, "permission_mode": None,
            "result_events": 0, "final_result": None, "permission_denials": 0, "malformed_lines": 0}
    if not path.exists():
        return info
    with open(path, "rb") as f:
        for raw in f:
            try:
                ev = json.loads(raw)
            except ValueError:
                info["malformed_lines"] += 1
                continue
            if not isinstance(ev, dict):
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init":
                info["session_id"] = ev.get("session_id") or info["session_id"]
                info["actual_model"] = ev.get("model")
                info["claude_code_version"] = ev.get("claude_code_version")
                info["permission_mode"] = ev.get("permissionMode")
            elif ev.get("type") == "result":
                info["result_events"] += 1
                info["session_id"] = info["session_id"] or ev.get("session_id")
                denials = ev.get("permission_denials") or []
                info["permission_denials"] = len(denials)
                text = ev.get("result") if isinstance(ev.get("result"), str) else ""
                info["final_result"] = {
                    "subtype": ev.get("subtype"), "is_error": ev.get("is_error"),
                    "terminal_reason": ev.get("terminal_reason"), "num_turns": ev.get("num_turns"),
                    "models_used": sorted((ev.get("modelUsage") or {}).keys()),
                    "result_excerpt": text[:result_chars] if result_chars > 0 else None,
                }
    return info


def read_exit(run_dir):
    p = run_dir / "exit.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except ValueError:
        return {"exit_code": None, "corrupt": True}


def status(run_dir, result_chars=0):
    run_dir = Path(run_dir).resolve()
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        die("NOT_A_RUN_DIR", str(run_dir))
    meta = json.loads(meta_path.read_text())
    stream = parse_stream(run_dir / "stream.jsonl", result_chars)
    interactive = meta.get("mode") == "interactive_rc"
    dispatch_path = run_dir / "dispatch.json"
    dispatch_info = json.loads(dispatch_path.read_text()) if dispatch_path.exists() else None
    if interactive:
        stream["session_id"] = meta.get("session_id")
        stream["actual_model"] = dispatch_info.get("actual_model") if dispatch_info else None
        stream["claude_code_version"] = meta.get("claude_version")
        stream["permission_mode"] = meta.get("permission_mode")
    exit_info = read_exit(run_dir)
    alive = tmux_alive(meta.get("tmux_socket"), meta.get("tmux_session"))
    procs = session_processes(stream["session_id"]) if meta.get("started") and not exit_info else []
    runner = runner_alive(run_dir) if not exit_info else None
    if runner:
        procs = sorted(set(procs) | {runner})
    final = stream["final_result"]
    reasons = []
    if exit_info is None:
        if not meta.get("started"):
            state = "prepared"
        elif alive or runner:
            state = "running"
        else:
            state = "unknown"
            reasons.append(f"no exit marker and tmux session gone from {meta.get('tmux_socket')}" + (f"; matching processes {procs}" if procs else ""))
    elif exit_info.get("exit_code") != 0:
        state = "failed"
        reasons.append(f"exit_code={exit_info.get('exit_code')}")
    elif interactive:
        state = "exited"
        reasons.append("interactive process exited; inspect final reply and handoff separately")
    elif not final:
        state = "unknown"
        reasons.append("exit 0 but no result event in stream")
    elif final.get("is_error") or final.get("subtype") != "success":
        state = "failed"
        reasons.append(f"result subtype={final.get('subtype')} is_error={final.get('is_error')}")
    else:
        state = "exited_ok"
    if interactive and state == "running":
        state = "interactive_alive" if dispatch_info else "awaiting_rc_readback"
    requested = meta.get("requested_model")
    actual = stream["actual_model"]
    model_match = None if actual is None else models_match(requested, actual)
    if model_match is False:
        reasons.append(f"model mismatch: requested {requested}, init reported {actual}")
    try:
        cur = fingerprint(meta["fingerprint"]["repo"])
        drift = {k: cur[k] for k in ("head", "branch", "dirty_hash", "index_entries", "stash_entries")
                 if cur[k] != meta["fingerprint"].get(k)}
    except SystemExit:
        cur, drift = None, {"error": "fingerprint unavailable"}
    return {
        "mode": meta.get("mode", "print"),
        "rc_current_state": "unverified; read the current /rc panel" if interactive else "disabled",
        "dispatch": dispatch_info,
        "run_id": meta["run_id"], "run_dir": str(run_dir), "kind": meta["kind"], "state": state,
        "reasons": reasons, "acceptance": "not decided by this tool; read the handoff and the raw gate evidence",
        "exit": exit_info, "tmux_socket": meta.get("tmux_socket"), "tmux_session": meta.get("tmux_session"), "tmux_alive": alive,
        "requested_model": requested, "actual_model": actual, "model_match": model_match,
        "requested_effort": meta.get("requested_effort"),
        "session_id": stream["session_id"], "resumed_from_session": meta.get("resume_session_id"),
        "claude_code_version": stream["claude_code_version"], "permission_mode": stream["permission_mode"],
        "result_events": stream["result_events"], "final_result": final,
        "permission_denials": stream["permission_denials"], "malformed_lines": stream["malformed_lines"],
        "runner_pid_alive": runner, "live_processes": procs,
        "stream_idle_s": int(dt.datetime.now().timestamp() - (run_dir / "stream.jsonl").stat().st_mtime) if (run_dir / "stream.jsonl").exists() else None,
        "repo_drift_since_launch": drift,
    }


def build_script(run_dir, repo, claude_bin, args_list, path_prepend, setenv, interactive=False):
    q = shlex.quote
    lines = ["#!/bin/bash", "set -u", "umask 077", f"RUN={q(str(run_dir))}",
             'finish() { printf \'{"exit_code": %s, "ended_at": "%s"}\\n\' "$1" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$RUN/exit.tmp" && mv "$RUN/exit.tmp" "$RUN/exit.json"; exit "$1"; }',
             'printf "%s\\n" "$$" > "$RUN/runner.pid"',
             f"cd -- {q(str(repo))} || finish 97"]
    if path_prepend:
        lines.append(f"export PATH={q(':'.join(path_prepend))}:\"$PATH\"")
    for k, v in setenv:
        lines.append(f"export {k}={q(v)} || finish 96")
    cmd = " ".join(q(a) for a in [claude_bin, *args_list])
    lines.append(cmd if interactive else f'{cmd} < "$RUN/mission.md" > "$RUN/stream.jsonl" 2> "$RUN/stderr.log"')
    lines.append("finish $?")
    return "\n".join(lines) + "\n"


def prepare_and_start(a, kind, repo, model, resume_session=None, parent_run=None):
    if a.permission_mode in FORBIDDEN_MODES:
        die("PERMISSION_MODE_FORBIDDEN", a.permission_mode)
    mission = Path(a.mission).resolve()
    if not mission.is_file() or mission.stat().st_size == 0:
        die("MISSION_MISSING", str(mission))
    claude_bin = a.claude_bin or shutil.which("claude")
    if not claude_bin:
        die("CLAUDE_NOT_FOUND", "pass --claude-bin")
    claude_bin = str(Path(claude_bin).resolve())
    for k, _ in a.setenv:
        if k.upper() in SETENV_RESERVED or not SETENV_NAME.fullmatch(k):
            die("SETENV_FORBIDDEN", k)
    if a.no_rc_reason is not None and not a.no_rc_reason.strip():
        die("RC_OPT_OUT_EMPTY", "record the user's explicit opt-out evidence")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.task_name):
        die("TASK_NAME_INVALID", "use a short ticket/name containing letters, digits, underscore or hyphen")
    interactive = not a.no_rc_reason
    if interactive or getattr(a, "effort", None):
        help_text = run([claude_bin, "--help"]).stdout.decode(errors="replace")
        if getattr(a, "effort", None) and "--effort" not in help_text:
            die("EFFORT_UNSUPPORTED", "CLI must support --effort; requested effort must not be silently dropped")
        if interactive and ("--remote-control" not in help_text or "--session-id" not in help_text):
            die("RC_UNSUPPORTED", "CLI must support --remote-control and --session-id; no print fallback")
    fp = fingerprint(repo)
    repo = Path(fp["repo"])
    runs_root = check_runs_root(Path(a.runs_root), repo)
    runs_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
    run_dir = runs_root / f"{kind}-{run_id}"
    os.mkdir(run_dir, 0o700)  # FileExistsError if it somehow exists: never reuse a run dir
    os.chmod(run_dir, 0o700)
    user = pwd.getpwuid(os.geteuid()).pw_name
    rc_name = f"dev-team-{a.task_name}-{run_id}"
    tmux_name = a.tmux_session or rc_name
    socket = Path(a.tmux_socket).absolute() if a.tmux_socket else runs_root / "tmux.sock"
    if len(str(socket)) > MAX_SOCKET_PATH:
        os.rmdir(run_dir)
        die("SOCKET_PATH_TOO_LONG", f"{socket} ({len(str(socket))} chars); pass a shorter --tmux-socket")
    if not a.prepare_only:
        if not shutil.which("tmux"):
            os.rmdir(run_dir)
            die("TMUX_NOT_FOUND", "install tmux or use --prepare-only")
        if tmux_alive(socket, tmux_name):
            os.rmdir(run_dir)
            die("TMUX_SESSION_EXISTS", f"{tmux_name} on {socket}")
    args_list = ["-p", "--model", model, "--permission-mode", a.permission_mode,
                 "--output-format", "stream-json", "--verbose"]
    session_id = resume_session or str(uuid.uuid4())
    if interactive:
        args_list = ["--model", model, "--permission-mode", a.permission_mode,
                     "--remote-control", rc_name]
        args_list += ["--resume", session_id] if resume_session else ["--session-id", session_id]
    elif resume_session:
        args_list[1:1] = ["--resume", resume_session]
    effort = getattr(a, "effort", None)
    if effort:
        args_list += ["--effort", effort]
    for d in a.add_dir:
        args_list += ["--add-dir", str(Path(d).resolve())]
    version = run([claude_bin, "--version"], check=False).stdout.decode(errors="replace").strip()
    write_new(run_dir / "mission.md", mission.read_bytes())
    for name in (() if interactive else ("stream.jsonl", "stderr.log")):
        write_new(run_dir / name, b"")
    write_new(run_dir / "run.sh", build_script(run_dir, repo, claude_bin, args_list, a.path_prepend, a.setenv, interactive), 0o700)
    meta = {
        "mode": "interactive_rc" if interactive else "print",
        "session_id": session_id if interactive else None,
        "rc_name": rc_name if interactive else None,
        "host": host_socket.gethostname(), "user": user,
        "no_rc_reason": a.no_rc_reason,
        "run_id": run_id, "kind": kind, "created_at": now(), "run_dir": str(run_dir),
        "fingerprint": fp, "tmux_socket": str(socket), "tmux_session": tmux_name, "requested_model": model, "requested_effort": effort,
        "permission_mode": a.permission_mode, "claude_bin": claude_bin, "claude_version": version,
        "path_prepend": a.path_prepend, "add_dirs": [str(Path(d).resolve()) for d in a.add_dir],
        "setenv_names": [k for k, _ in a.setenv], "resume_session_id": resume_session,
        "parent_run": parent_run, "argv": args_list, "started": False,
    }
    meta_path = run_dir / "meta.json"
    write_new(meta_path, json.dumps(meta, indent=2, ensure_ascii=False))
    if not a.prepare_only:
        pane = tmux(socket, "new-session", "-d", "-P", "-F", "#{pane_id}", "-x", "160", "-y", "45", "-s", tmux_name, "-c", str(repo), f"bash {shlex.quote(str(run_dir / 'run.sh'))}")
        meta["pane_id"] = pane.stdout.decode().strip()
        meta["started"], meta["started_at"] = True, now()
        tmp = run_dir / "meta.json.tmp"
        write_new(tmp, json.dumps(meta, indent=2, ensure_ascii=False))
        os.replace(tmp, meta_path)
    print(json.dumps({"run_dir": str(run_dir), "tmux_socket": str(socket), "tmux_session": tmux_name, "started": meta["started"],
                      "requested_model": model, "resume_session_id": resume_session,
                      "mode": meta["mode"], "mission_sent": meta["started"] and not interactive, "rc_verified": False}, ensure_ascii=False))


def dispatch(a):
    """PM attestation, not automated proof of remote-client access or ongoing connectivity.

    Claim before sending so a partial send/failure cannot silently replay the mission.
    """
    run_dir = Path(a.run_dir).resolve()
    meta = json.loads((run_dir / "meta.json").read_text())
    if meta.get("mode") != "interactive_rc" or not a.confirm_rc_active_and_idle:
        die("RC_READBACK_REQUIRED", "only a verified, idle interactive RC session can receive a mission")
    if not re.fullmatch(r"https://claude\.ai/code/session_[A-Za-z0-9_-]+", a.remote_url):
        die("RC_URL_INVALID", "copy the actual session URL from this run's current RC panel")
    if not models_match(meta["requested_model"], a.actual_model):
        die("MODEL_MISMATCH", "base model IDs must match (optional trailing [1m] is ignored)")
    socket, name = meta["tmux_socket"], meta["tmux_session"]
    if read_exit(run_dir) or not meta.get("started") or not tmux_alive(socket, name):
        die("RUN_NOT_LIVE", "no live owned session")
    target = meta.get("pane_id")
    if not target or not re.fullmatch(r"%[0-9]+", target):
        die("PANE_NOT_RECORDED", "inspect the owned run; do not guess a window/pane index")
    pane_session = tmux(socket, "display-message", "-p", "-t", target, "#{session_name}").stdout.decode().strip()
    if pane_session != name:
        die("PANE_IDENTITY_MISMATCH", "recorded pane does not belong to the owned session")
    claim = run_dir / "dispatch.json"
    info = {"state": "sending_or_unknown", "verified_at": now(), "remote_url": a.remote_url,
            "actual_model": a.actual_model, "verification": "PM attestation of current RC, session identity and empty idle prompt"}
    try:
        write_new(claim, json.dumps(info, indent=2))
    except FileExistsError:
        die("ALREADY_DISPATCHED", "inspect prior send; do not retry or delete evidence to replay")
    # Current visible pane only, not historical scrollback. Keep private; never print its contents.
    pane = tmux(socket, "capture-pane", "-p", "-t", target).stdout
    write_new(run_dir / "dispatch-pane.txt", pane)
    buffer = "dev-team-" + meta["run_id"]
    try:
        tmux(socket, "load-buffer", "-b", buffer, str(run_dir / "mission.md"))
        tmux(socket, "paste-buffer", "-b", buffer, "-p", "-d", "-t", target)
        tmux(socket, "send-keys", "-t", target, "Enter")
    finally:
        tmux(socket, "delete-buffer", "-b", buffer, check=False)
    info["state"] = "sent"
    write_new(run_dir / "dispatch.tmp", json.dumps(info, indent=2))
    os.replace(run_dir / "dispatch.tmp", claim)
    print(json.dumps({"run_dir": str(run_dir), "dispatch": info}))


def parse_setenv(values):
    out = []
    for v in values:
        k, sep, val = v.partition("=")
        if not sep or not k:
            die("SETENV_INVALID", v)
        out.append((k, val))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, resume):
        p.add_argument("--mission", required=True, help="mission saved locally; interactive mode waits for dispatch")
        p.add_argument("--model", required=not resume, help="explicit full model ID; resume inherits the recorded choice")
        p.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                       default=None, help="optional effort; omit to use CLI defaults, resume inherits recorded effort")
        p.add_argument("--runs-root", required=not resume, help="parent of run directories (outside the repo or git-ignored)")
        p.add_argument("--claude-bin")
        p.add_argument("--task-name", default="task", help="short RC title component")
        p.add_argument("--no-rc-reason", help="explicit user opt-out evidence; never use as an automatic fallback")
        p.add_argument("--permission-mode", required=not resume, choices=PERMISSION_MODES + sorted(FORBIDDEN_MODES), help="select a mode supported by the installed CLI; bypassPermissions is refused")
        p.add_argument("--path-prepend", action="append", default=None if resume else [], help="runtime bin dir, e.g. the repo's pinned node")
        p.add_argument("--add-dir", action="append", default=None if resume else [])
        p.add_argument("--setenv", action="append", default=[], help="non-secret KEY=VALUE for the run (meta.json keeps names only; run.sh holds the value)")
        p.add_argument("--tmux-session")
        p.add_argument("--tmux-socket", help="explicit tmux server socket (default <runs-root>/tmux.sock, owned by this helper)")
        p.add_argument("--prepare-only", action="store_true", help="write the run dir and run.sh but start nothing")

    lp = sub.add_parser("launch")
    lp.add_argument("--repo", required=True)
    common(lp, False)
    rp = sub.add_parser("resume")
    rp.add_argument("--from", dest="from_run", required=True, help="run dir whose Claude session is resumed")
    rp.add_argument("--ack-unknown-prior", action="store_true", help="prior run is 'unknown' and you verified no process holds its session")
    common(rp, True)
    sp = sub.add_parser("status")
    sp.add_argument("run_dir")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--result-chars", type=int, default=0, help="include the first N chars of the final result text")
    dp = sub.add_parser("dispatch", help="send saved mission once, after PM verifies current RC, model and idle")
    dp.add_argument("run_dir")
    dp.add_argument("--remote-url", required=True)
    dp.add_argument("--actual-model", required=True)
    dp.add_argument("--confirm-rc-active-and-idle", action="store_true", required=True,
                    help="PM just verified this session's active RC, identity and empty idle prompt")
    a = ap.parse_args()
    if a.cmd == "dispatch":
        dispatch(a)
        return

    if a.cmd == "status":
        s = status(a.run_dir, a.result_chars)
        if a.json:
            print(json.dumps(s, indent=2, ensure_ascii=False))
        else:
            print(f"{s['run_id']} state={s['state']} model={s['actual_model']} (requested {s['requested_model']}) "
                  f"session={s['session_id']} tmux_alive={s['tmux_alive']} denials={s['permission_denials']} drift={list(s['repo_drift_since_launch'])}")
            for r in s["reasons"]:
                print(f"  - {r}")
        sys.exit(0)

    a.setenv = parse_setenv(a.setenv)
    if a.cmd == "launch":
        prepare_and_start(a, "launch", Path(a.repo), a.model)
        return
    prior_dir = Path(a.from_run).resolve()
    prior = status(prior_dir)
    meta = json.loads((prior_dir / "meta.json").read_text())
    if prior["state"] in ("running", "prepared", "interactive_alive", "awaiting_rc_readback"):
        die("PRIOR_RUN_ACTIVE", f"{prior['run_id']} is {prior['state']}; wait for it to exit before resuming")
    if prior["state"] == "unknown" and not a.ack_unknown_prior:
        die("PRIOR_RUN_UNKNOWN", f"{prior['run_id']}: {'; '.join(prior['reasons'])}; verify the process is gone, then pass --ack-unknown-prior")
    if session_processes(prior["session_id"]) or prior["runner_pid_alive"]:
        die("PRIOR_SESSION_BUSY", f"a process of {prior['run_id']} is still alive {prior['live_processes']}")
    if not prior["session_id"]:
        die("NO_SESSION_ID", f"{prior['run_id']} recorded no Claude session id; start a new launch instead")
    a.runs_root = a.runs_root or str(prior_dir.parent)
    a.claude_bin = a.claude_bin or meta["claude_bin"]
    a.effort = a.effort or meta.get("requested_effort")
    a.permission_mode = a.permission_mode or meta["permission_mode"]
    a.path_prepend = meta["path_prepend"] if a.path_prepend is None else a.path_prepend
    a.add_dir = meta["add_dirs"] if a.add_dir is None else a.add_dir
    a.tmux_socket = a.tmux_socket or meta.get("tmux_socket")
    missing_env = sorted(set(meta.get("setenv_names") or []) - {k for k, _ in a.setenv})
    if missing_env:
        print(f"WARNING: prior run set {missing_env}; resume does not reuse --setenv values, pass --setenv again if still needed", file=sys.stderr)
    prepare_and_start(a, "resume", Path(meta["fingerprint"]["repo"]), a.model or meta["requested_model"],
                      resume_session=prior["session_id"], parent_run=str(prior_dir))


if __name__ == "__main__":
    main()
