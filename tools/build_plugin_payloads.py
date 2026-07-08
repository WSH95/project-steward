#!/usr/bin/env python3
"""Build clean Claude Code and Codex plugin payloads from plugin-src/.

This repository is a development workspace. The installable plugin folders
are generated artifacts so shared skills, references, and templates have one
canonical authoring location.
"""
from __future__ import annotations

import argparse
import json
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


def _safe_clean(path):
    target = path.expanduser().resolve()
    forbidden = {
        ROOT.resolve(),
        SOURCE.resolve(),
        Path.home().resolve(),
        Path(target.anchor).resolve(),
    }
    if target in forbidden:
        raise SystemExit("refusing to clean unsafe output path: %s" % target)
    if target.exists():
        shutil.rmtree(str(target))


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
    _copy_tree(SOURCE / "claude" / "commands", plugin / "commands")
    _copy_tree(SOURCE / "claude" / "hooks", plugin / "hooks")
    _copy_file(
        SOURCE / "codex" / "hooks" / "hooks.json",
        plugin / "hooks" / "codex.hooks.json",
    )

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
        SOURCE / "codex" / "hooks" / "hooks.json",
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
    if clean:
        _safe_clean(out)
    out.mkdir(parents=True, exist_ok=True)
    meta = _load_metadata()
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
