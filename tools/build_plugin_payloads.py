#!/usr/bin/env python3
"""Build clean Claude Code and Codex plugin payloads from plugin-src/.

This repository is a development workspace. The installable plugin folders
are generated artifacts so shared skills, references, and templates have one
canonical authoring location.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "plugin-src"
DEFAULT_OUT = ROOT / "dist" / "project-steward"
IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", "*.egg-info"
)


def _load_metadata():
    path = SOURCE / "metadata.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit("cannot read %s: %s" % (path, exc))


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _copy_tree(src, dst):
    if not src.is_dir():
        raise SystemExit("missing source directory: %s" % src)
    if dst.exists():
        shutil.rmtree(str(dst))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(src), str(dst), ignore=IGNORE)


def _copy_file(src, dst):
    if not src.is_file():
        raise SystemExit("missing source file: %s" % src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))


def _is_under(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _git_metadata_paths():
    marker = ROOT.resolve() / ".git"
    paths = [marker.resolve()]
    if marker.is_file() and not marker.is_symlink():
        try:
            first_line = marker.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, UnicodeError, IndexError):
            first_line = ""
        if first_line.lower().startswith("gitdir:"):
            git_dir = Path(first_line.split(":", 1)[1].strip())
            if not git_dir.is_absolute():
                git_dir = marker.parent / git_dir
            paths.append(git_dir.resolve())
    return paths


def _unsafe_output_entry(path):
    if path.is_symlink():
        return path, "symlink"
    if not path.is_dir():
        return None
    for current, directories, files in os.walk(str(path), followlinks=False):
        current_path = Path(current)
        for name in directories + files:
            candidate = current_path / name
            if name.lower() == ".git":
                return candidate, "Git metadata"
            if candidate.is_symlink():
                return candidate, "symlink"
    return None


def _output_trust_boundary(lexical, target, root):
    """Return the lexical ancestor shared with the resolved repository.

    Resolving the shared boundary before inspecting its descendants allows
    platform path aliases such as macOS /tmp -> /private/tmp while still
    exposing symlinks in the caller-controlled portion of the output path.
    """
    try:
        resolved_boundary = Path(
            os.path.commonpath([str(target), str(root)])
        )
    except ValueError:
        return Path(lexical.anchor)

    for candidate in (lexical,) + tuple(lexical.parents):
        if candidate.resolve() == resolved_boundary:
            return candidate
    return Path(lexical.anchor)


def _unsafe_output_ancestor(lexical, target, root):
    for candidate in (lexical,) + tuple(lexical.parents):
        if candidate.name.lower() == ".git":
            return candidate, "Git metadata"

    boundary = _output_trust_boundary(lexical, target, root)
    try:
        relative = lexical.relative_to(boundary)
    except ValueError:
        relative = lexical
        boundary = Path(lexical.anchor)
    candidate = boundary
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return candidate, "symlink"
    return None


def _read_generated_manifest(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _is_generated_output(path, meta):
    name = meta.get("name")
    marketplace = meta.get("marketplace")
    if not isinstance(name, str) or not isinstance(marketplace, dict):
        return False

    claude_plugin = _read_generated_manifest(
        path / "claude" / "plugins" / name
        / ".claude-plugin" / "plugin.json"
    )
    codex_plugin = _read_generated_manifest(
        path / "codex" / "plugins" / name
        / ".codex-plugin" / "plugin.json"
    )
    claude_marketplace = _read_generated_manifest(
        path / "claude" / ".claude-plugin" / "marketplace.json"
    )
    codex_marketplace = _read_generated_manifest(
        path / "codex" / ".agents" / "plugins" / "marketplace.json"
    )
    if not all((claude_plugin, codex_plugin,
                claude_marketplace, codex_marketplace)):
        return False

    stable_fields = ("name", "author", "homepage", "license")
    if any(claude_plugin.get(field) != meta.get(field)
           for field in stable_fields):
        return False
    if any(codex_plugin.get(field) != meta.get(field)
           for field in stable_fields):
        return False
    if codex_plugin.get("repository") != meta.get("repository"):
        return False

    marketplace_name = marketplace.get("name")
    if claude_marketplace.get("name") != marketplace_name:
        return False
    if codex_marketplace.get("name") != marketplace_name:
        return False
    expected_path = "./plugins/%s" % name
    claude_entries = claude_marketplace.get("plugins")
    codex_entries = codex_marketplace.get("plugins")
    if not isinstance(claude_entries, list) or len(claude_entries) != 1:
        return False
    if not isinstance(codex_entries, list) or len(codex_entries) != 1:
        return False
    if not isinstance(claude_entries[0], dict):
        return False
    if not isinstance(codex_entries[0], dict):
        return False
    if claude_entries[0].get("name") != name:
        return False
    if claude_entries[0].get("source") != expected_path:
        return False
    if codex_entries[0].get("name") != name:
        return False
    if codex_entries[0].get("source") != {
        "source": "local",
        "path": expected_path,
    }:
        return False
    return True


def _validate_output(path, meta):
    expanded = path.expanduser()
    lexical = Path(os.path.abspath(str(expanded)))
    target = lexical.resolve()
    root = ROOT.resolve()
    source = SOURCE.resolve()

    unsafe_ancestor = _unsafe_output_ancestor(lexical, target, root)
    if unsafe_ancestor:
        unsafe_path, reason = unsafe_ancestor
        raise SystemExit(
            "refusing unsafe output path (%s): %s" % (reason, unsafe_path)
        )
    if _is_under(root, target):
        raise SystemExit(
            "refusing unsafe output path (repository ancestor): %s" % target
        )
    if _is_under(target, source) or _is_under(source, target):
        raise SystemExit(
            "refusing unsafe output path (source-tree overlap): %s" % target
        )
    for git_path in _git_metadata_paths():
        if _is_under(target, git_path) or _is_under(git_path, target):
            raise SystemExit(
                "refusing unsafe output path (Git metadata): %s" % target
            )
    if target == Path.home().resolve() or target == Path(target.anchor).resolve():
        raise SystemExit("refusing unsafe output path: %s" % target)
    if target.name.lower() == ".git":
        raise SystemExit(
            "refusing unsafe output path (Git metadata): %s" % target
        )
    if target.exists() and not target.is_dir():
        raise SystemExit("refusing non-directory output path: %s" % target)

    unsafe = _unsafe_output_entry(target)
    if unsafe:
        unsafe_path, reason = unsafe
        raise SystemExit(
            "refusing output containing %s: %s" % (reason, unsafe_path)
        )
    if target.exists() and any(target.iterdir()):
        if not _is_generated_output(target, meta):
            raise SystemExit(
                "refusing unrecognized nonempty output directory: %s" % target
            )
    return target


def _base_fields(meta, description):
    return {
        "name": meta["name"],
        "version": meta["version"],
        "description": description,
        "author": meta["author"],
        "homepage": meta["homepage"],
        "license": meta["license"],
        "keywords": meta["keywords"],
    }


def _build_claude(out, meta):
    plugin = out / "claude" / "plugins" / meta["name"]
    _copy_tree(SOURCE / "skills", plugin / "skills")
    _copy_tree(SOURCE / "references", plugin / "references")
    _copy_tree(SOURCE / "src", plugin / "src")
    _copy_tree(SOURCE / "claude" / "bin", plugin / "bin")
    _copy_tree(SOURCE / "claude" / "commands", plugin / "commands")
    _copy_tree(SOURCE / "claude" / "hooks", plugin / "hooks")

    manifest = _base_fields(meta, meta["claude_description"])
    manifest["commands"] = "./commands"
    manifest["skills"] = "./skills"
    _write_json(plugin / ".claude-plugin" / "plugin.json", manifest)

    marketplace = {
        "name": meta["marketplace"]["name"],
        "owner": meta["author"],
        "metadata": {
            "description": "Marketplace for the Project Steward plugin",
            "version": meta["version"],
        },
        "plugins": [
            {
                "name": meta["name"],
                "source": "./plugins/%s" % meta["name"],
                "description": (
                    "Cross-agent project stewardship toolkit (init, "
                    "progress, handoff/resume, backend broker)."
                ),
            }
        ],
    }
    _write_json(out / "claude" / ".claude-plugin" / "marketplace.json",
                marketplace)


def _build_codex(out, meta):
    plugin = out / "codex" / "plugins" / meta["name"]
    _copy_tree(SOURCE / "skills", plugin / "skills")
    _copy_tree(SOURCE / "references", plugin / "references")
    _copy_tree(
        SOURCE / "src" / "project_steward" / "templates",
        plugin / "src" / "project_steward" / "templates",
    )
    _copy_tree(SOURCE / "codex" / "prompts", out / "codex" / "prompts")
    _copy_file(
        SOURCE / "src" / "project_steward" / "templates"
        / "codex-hooks.json.template",
        out / "codex" / "hooks" / "hooks.json",
    )

    manifest = _base_fields(meta, meta["description"])
    manifest["repository"] = meta["repository"]
    manifest["skills"] = "./skills/"
    manifest["interface"] = meta["interface"]
    _write_json(plugin / ".codex-plugin" / "plugin.json", manifest)

    marketplace = {
        "name": meta["marketplace"]["name"],
        "description": (
            "Marketplace exposing the Project Steward plugin to Codex "
            "(`codex plugin marketplace add <path-or-repo>`)."
        ),
        "interface": {
            "displayName": meta["marketplace"]["display_name"],
        },
        "plugins": [
            {
                "name": meta["name"],
                "source": {
                    "source": "local",
                    "path": "./plugins/%s" % meta["name"],
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": meta["marketplace"]["category"],
            }
        ],
    }
    _write_json(out / "codex" / ".agents" / "plugins" / "marketplace.json",
                marketplace)


def build(out, clean=False):
    meta = _load_metadata()
    out = _validate_output(out, meta)
    if clean:
        if out.exists():
            shutil.rmtree(str(out))
    out.mkdir(parents=True, exist_ok=True)
    _build_claude(out, meta)
    _build_codex(out, meta)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build Project Steward plugin payloads."
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="output directory (default: dist/project-steward)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="replace the output directory before building",
    )
    args = parser.parse_args(argv)

    out = build(Path(args.out), clean=args.clean)
    sys.stdout.write("Built plugin payloads in %s\n" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
