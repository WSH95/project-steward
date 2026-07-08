#!/usr/bin/env python3
"""Publish a generated agent skill/plugin artifact as a GitHub PR."""
from __future__ import annotations

import argparse
import datetime as _datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_MANIFEST = "agent-artifacts.json"


class UsageError(Exception):
    pass


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise UsageError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise UsageError("invalid JSON in %s: %s" % (path, exc))


def _write_json(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _select_artifact(manifest, name):
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise UsageError("manifest must contain a non-empty artifacts list")
    if name:
        for artifact in artifacts:
            if artifact.get("name") == name:
                return artifact
        raise UsageError("unknown artifact %r" % name)
    if len(artifacts) == 1:
        return artifacts[0]
    names = ", ".join(str(item.get("name", "<unnamed>")) for item in artifacts)
    raise UsageError("--artifact is required; available artifacts: %s" % names)


def _validate_rel_path(value, label):
    if not value or not isinstance(value, str):
        raise UsageError("%s is required" % label)
    path = Path(value)
    if path.is_absolute() or value in (".", os.curdir):
        raise UsageError("unsafe %s: %s" % (label, value))
    if any(part == ".." for part in path.parts):
        raise UsageError("unsafe %s: %s" % (label, value))
    return path


def _is_under(child, parent):
    child_s = str(child.resolve())
    parent_s = str(parent.resolve())
    return child_s == parent_s or child_s.startswith(parent_s + os.sep)


def _run(command, cwd, capture=False):
    if isinstance(command, str):
        shell = True
    else:
        shell = False
    if capture:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            shell=shell,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout.strip()
    subprocess.run(command, cwd=str(cwd), shell=shell, check=True)
    return ""


def _ensure_target_repo(manifest_path, manifest, artifact, args):
    repo = args.target_repo or artifact.get("target_repo", "")
    if repo:
        if args.target_repo and args.save_target_repo:
            artifact["target_repo"] = repo
            _write_json(manifest_path, manifest)
        return repo

    if args.non_interactive:
        raise UsageError(
            "target_repo is required; pass --target-repo or set it in %s"
            % manifest_path
        )

    prompt = (
        "Target repository for %s (for example "
        "git@github.com:USER/agent-%ss.git): "
    ) % (artifact.get("name", "artifact"), artifact.get("kind", "artifact"))
    repo = input(prompt).strip()
    if not repo:
        raise UsageError("target_repo is required")
    answer = input("Save target_repo to %s? [y/N] " % manifest_path).strip()
    if answer.lower() in ("y", "yes"):
        artifact["target_repo"] = repo
        _write_json(manifest_path, manifest)
    return repo


def _prepare_checkout(target_repo, args):
    if args.target_checkout:
        checkout = Path(args.target_checkout).expanduser().resolve()
        if args.dry_run:
            checkout.mkdir(parents=True, exist_ok=True)
        elif not (checkout / ".git").is_dir():
            raise UsageError("--target-checkout must be a git checkout")
        return checkout, None

    temp_dir = tempfile.mkdtemp(prefix="agent-artifact-pr-")
    checkout = Path(temp_dir) / "target"
    _run(["git", "clone", target_repo, str(checkout)], Path.cwd())
    return checkout, temp_dir


def _copy_source(project_root, checkout, artifact):
    source_path = _validate_rel_path(artifact.get("source_path"), "source_path")
    target_path = _validate_rel_path(artifact.get("target_path"), "target_path")
    source = (project_root / source_path).resolve()
    destination = (checkout / target_path).resolve()

    if not _is_under(source, project_root):
        raise UsageError("unsafe source_path: %s" % source_path)
    if not source.exists():
        raise UsageError("source_path does not exist: %s" % source_path)
    if not _is_under(destination, checkout):
        raise UsageError("unsafe target_path: %s" % target_path)

    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(str(destination))
        else:
            destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(str(source), str(destination))
    else:
        shutil.copy2(str(source), str(destination))
    return target_path


def _branch_name(artifact):
    stamp = _datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    raw = str(artifact.get("name", "artifact"))
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-").lower()
    return "publish/%s/%s" % (safe or "artifact", stamp)


def _git_has_changes(checkout, target_path):
    output = _run(["git", "status", "--short", "--", str(target_path)],
                  checkout, capture=True)
    return bool(output)


def _source_commit(project_root):
    try:
        return _run(["git", "rev-parse", "--short", "HEAD"],
                    project_root, capture=True)
    except Exception:
        return "unknown"


def publish(args):
    manifest_path = Path(args.manifest).expanduser().resolve()
    project_root = manifest_path.parent
    manifest = _load_json(manifest_path)
    artifact = _select_artifact(manifest, args.artifact)
    target_repo = _ensure_target_repo(manifest_path, manifest, artifact, args)
    build_command = artifact.get("build_command", "")

    if build_command:
        sys.stdout.write("Running build command: %s\n" % build_command)
        _run(build_command, project_root)

    checkout, temp_dir = _prepare_checkout(target_repo, args)
    try:
        base_branch = args.base or artifact.get("base_branch", "main")
        branch = args.branch or _branch_name(artifact)
        if not args.dry_run:
            _run(["git", "checkout", base_branch], checkout)
            _run(["git", "pull", "--ff-only", "origin", base_branch], checkout)
            _run(["git", "checkout", "-b", branch], checkout)

        target_path = _copy_source(project_root, checkout, artifact)

        if args.dry_run:
            sys.stdout.write(
                "DRY RUN: copied %s to %s in %s; no commit, push, or PR\n"
                % (artifact["source_path"], target_path, checkout)
            )
            return 0

        if not _git_has_changes(checkout, target_path):
            sys.stdout.write("No changes after copy; no PR created.\n")
            return 0

        _run(["git", "add", str(target_path)], checkout)
        title = args.pr_title or "Update %s" % artifact.get("name", "artifact")
        commit_message = args.commit_message or title
        _run(["git", "commit", "-m", commit_message], checkout)
        _run(["git", "push", "-u", "origin", branch], checkout)
        body = args.pr_body or (
            "Published from %s at %s." % (Path.cwd().name,
                                         _source_commit(project_root))
        )
        _run([
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            branch,
            "--title",
            title,
            "--body",
            body,
        ], checkout)
        return 0
    finally:
        if temp_dir and not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Publish an agent skill/plugin artifact as a GitHub PR."
    )
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--artifact")
    parser.add_argument("--target-repo")
    parser.add_argument("--save-target-repo", action="store_true")
    parser.add_argument("--target-checkout")
    parser.add_argument("--base")
    parser.add_argument("--branch")
    parser.add_argument("--pr-title")
    parser.add_argument("--pr-body")
    parser.add_argument("--commit-message")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args(argv)

    try:
        return publish(args)
    except UsageError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except subprocess.CalledProcessError as exc:
        sys.stderr.write("command failed with exit %s: %s\n" %
                         (exc.returncode, exc.cmd))
        return exc.returncode or 1


if __name__ == "__main__":
    sys.exit(main())
