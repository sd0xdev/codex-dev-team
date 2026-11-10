#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Install this checkout's Codex skill. No downloads, credentials, or CLI changes."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

NAME = 'codex-dev-team'
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'skills' / NAME


def contents(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError(f'Refusing symlink in skill: {p}')
        if '__pycache__' in p.parts or p.name.endswith('.pyc'):
            continue
        if p.is_file():
            result[str(p.relative_to(root))] = (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o111)
    return result


def install(target, update=False, dry_run=False):
    target = Path(target).expanduser().absolute()
    destination = target / NAME
    if target.is_symlink() or destination.is_symlink():
        raise ValueError('Refusing a symlink target or existing skill; choose the real skills directory explicitly.')
    if not (SOURCE / 'SKILL.md').is_file():
        raise ValueError('Missing packaged SKILL.md')
    source_contents = contents(SOURCE)
    if destination.exists():
        if not destination.is_dir():
            raise ValueError(f'Destination is not a directory: {destination}')
        if contents(destination) == source_contents:
            return {'status': 'already_current', 'path': str(destination)}
        if not update:
            raise ValueError(f'{destination} differs; use --update to back it up and replace it.')
    if dry_run:
        return {'status': 'would_update' if destination.exists() else 'would_install', 'path': str(destination)}
    target.mkdir(parents=True, exist_ok=True)
    # Serialize installers; never take over a lock left by another process.
    lock = target / '.codex-dev-team-install.lock'
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    stage = None
    backup = None
    try:
        # Recheck after acquiring the lock in case another installer completed.
        if destination.is_symlink():
            raise ValueError('Destination became a symlink')
        if destination.exists() and contents(destination) == source_contents:
            return {'status': 'already_current', 'path': str(destination)}
        if destination.exists() and not update:
            raise ValueError('Destination appeared; rerun with --update after inspecting it.')
        stage = Path(tempfile.mkdtemp(prefix='.codex-dev-team-stage-', dir=target))
        shutil.copytree(SOURCE, stage, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if contents(stage) != source_contents:
            raise ValueError('Staged copy failed verification')
        if destination.exists():
            backup_root = target.parent / '.codex-dev-team-backups'
            if backup_root.is_symlink():
                raise ValueError('Refusing a symlink backup directory')
            backup_root.mkdir(mode=0o700, exist_ok=True)
            stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            backup = backup_root / (stamp + '-' + uuid.uuid4().hex[:8])
            destination.rename(backup)
        try:
            stage.rename(destination)
            stage = None
        except OSError:
            if backup is not None and not destination.exists():
                backup.rename(destination)
            raise
        result = {'status': 'updated' if backup else 'installed', 'path': str(destination)}
        if backup:
            result['backup'] = str(backup)
        return result
    finally:
        if stage is not None:
            shutil.rmtree(stage)
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=Path.home() / '.agents' / 'skills', help='Skills root (default: ~/.agents/skills)')
    parser.add_argument('--update', action='store_true', help='Back up and replace a differing existing codex-dev-team')
    parser.add_argument('--dry-run', action='store_true', help='Inspect only; do not create directories or modify files')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.target, args.update, args.dry_run), indent=2))
    except (OSError, ValueError) as error:
        print(f'Install failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
