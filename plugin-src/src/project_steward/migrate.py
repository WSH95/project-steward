"""Lossless migration from legacy ``.projectforge/`` state.

Migration is split into a read-only preflight and an apply step. The preflight
decodes and validates every text input, computes every write, and rejects
destination conflicts. Apply first makes a unique raw backup, performs the
planned writes, verifies them, and only then removes the legacy tree.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import uuid
from pathlib import Path

from . import BLOCK_PREFIX, LEGACY_BLOCK_PREFIX, __version__
from .managed_blocks import markers, unified_diff
from .paths import legacy_dir, state_dir
from .scaffold import (build_mapping, gitignore_block, session_protocol_block,
                       workflow_text)
from .state import default_state, utcnow_iso, write_text_atomic


LEGACY_STATE_FILES = ["PROJECT.md", "PLAN.md", "PROGRESS.md", "HANDOFF.md",
                      "DECISIONS.md"]

CONFIG_KEY_MAP = {
    "AUTO_HANDOFF_MODE": ("session", "auto_handoff_mode", "str"),
    "AUTO_HANDOFF_COOLDOWN_MIN": ("session", "auto_handoff_cooldown_min", "int"),
    "AUTO_HANDOFF_MIN_EDITS": ("session", "auto_handoff_min_edits", "int"),
    "COMMIT_POLICY": ("git", "commit_policy", "str"),
}

LEGACY_HEADING_RE = re.compile(
    r"^##\s+Agent session protocol \(Projectforge\)\s*$")
MARKER_LINE_RE = re.compile(
    r"^(?:"
    r"<!-- (?P<html_prefix>PROJECT-STEWARD|PROJECTFORGE):"
    r"(?P<html_kind>BEGIN|END) (?P<html_name>[\w.-]+) -->"
    r"|"
    r"# (?P<hash_prefix>PROJECT-STEWARD|PROJECTFORGE):"
    r"(?P<hash_kind>BEGIN|END) (?P<hash_name>[\w.-]+)"
    r")[ \t]*(?:\r?\n)?$"
)
MIGRATION_PROGRESS_NOTE = (
    "Migrated Projectforge state to Project Steward "
    "(.projectforge/ -> .project-steward/). Backup at "
    ".project-steward/migration-backup-projectforge/."
)
MIGRATION_BACKEND_NOTE = (
    "Defaulted at migration; run `project-steward backend recommend` "
    "to revisit."
)
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
KNOWN_LEGACY_GITIGNORE_RULES = {
    ".projectforge/journal/",
    "/.projectforge/journal/",
}
FRESH_BACKUP_GITIGNORE = "*\n"
BACKUP_ORIGINALS_DIR = "original-instructions"


class MarkerError(ValueError):
    """A managed marker structure cannot be changed safely."""


class MigrationPlan(object):
    """Internal immutable-by-convention result of migration preflight."""

    def __init__(self, root, project_name):
        self.root = Path(root)
        self.project_name = project_name
        self.legacy = legacy_dir(root)
        self.ok = True
        self.error = ""
        self.conflicts = []
        self.writes = {}
        self.copies = []
        self.observed = {}
        self.observed_trees = {}
        self.legacy_manifest = {}
        self.backup_originals = []
        self.moved = []
        self.notes = []
        self.agents_diff = ""

    def report(self):
        report = {
            "ok": self.ok,
            "moved": list(self.moved),
            "notes": list(self.notes),
            "agents_diff": self.agents_diff,
            "changes": sorted(self.writes),
            "will_remove_legacy": bool(self.ok),
        }
        if self.error:
            report["error"] = self.error
        if self.conflicts:
            report["conflicts"] = list(self.conflicts)
        return report


def parse_legacy_config(text):
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _validate_legacy_config(values):
    mode = values.get("AUTO_HANDOFF_MODE")
    if mode is not None and mode not in ("block", "remind", "off"):
        raise ValueError(
            "legacy config AUTO_HANDOFF_MODE must be block, remind, or off")
    policy = values.get("COMMIT_POLICY")
    if policy is not None and policy not in ("auto", "ask", "never"):
        raise ValueError(
            "legacy config COMMIT_POLICY must be auto, ask, or never")
    for key in ("AUTO_HANDOFF_COOLDOWN_MIN", "AUTO_HANDOFF_MIN_EDITS"):
        if key not in values:
            continue
        try:
            value = int(values[key])
        except ValueError:
            raise ValueError("legacy config %s must be an integer" % key)
        if value < 0:
            raise ValueError("legacy config %s cannot be negative" % key)


def render_config_toml(legacy_values):
    sections = {}
    for legacy_key, (section, key, kind) in CONFIG_KEY_MAP.items():
        if legacy_key not in legacy_values:
            continue
        raw = legacy_values[legacy_key]
        value = raw
        if kind == "int":
            try:
                value = int(raw)
            except ValueError:
                continue
        sections.setdefault(section, {})[key] = value
    lines = ["# Project Steward config (migrated from Projectforge)", ""]
    for section in ("session", "git"):
        lines.append("[%s]" % section)
        for key, value in sections.get(section, {}).items():
            if isinstance(value, int):
                lines.append("%s = %d" % (key, value))
            else:
                escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
                lines.append('%s = "%s"' % (key, escaped))
        lines.append("")
    return "\n".join(lines)


def _path_snapshot(path):
    path = Path(path)
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return ("missing",)
    if stat.S_ISLNK(mode):
        return ("link", os.readlink(str(path)))
    if stat.S_ISDIR(mode):
        return ("dir",)
    if stat.S_ISREG(mode):
        return ("file", path.read_bytes())
    return ("unsupported", stat.S_IFMT(mode))


def _tree_manifest(root):
    root = Path(root)
    manifest = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        snapshot = _path_snapshot(path)
        if snapshot[0] == "unsupported":
            raise OSError("unsupported legacy entry: %s" % rel)
        manifest[rel] = snapshot
    return manifest


def _relative(plan, path):
    return Path(path).relative_to(plan.root).as_posix()


def _observe(plan, path):
    rel = _relative(plan, path)
    if rel not in plan.observed:
        plan.observed[rel] = _path_snapshot(path)
    return plan.observed[rel]


def _observe_destination(plan, path, label):
    """Snapshot a destination after rejecting unsafe ancestor entries."""
    path = Path(path)
    try:
        relative = path.relative_to(plan.root)
    except ValueError:
        raise OSError("%s is outside the project root" % label)
    ancestor = plan.root
    for part in relative.parts[:-1]:
        ancestor = ancestor / part
        snapshot = _observe(plan, ancestor)
        if snapshot[0] == "missing":
            continue
        ancestor_label = _relative(plan, ancestor)
        if snapshot[0] == "link":
            raise OSError(
                "%s has symlinked destination ancestor %s"
                % (label, ancestor_label))
        if snapshot[0] != "dir":
            raise OSError(
                "%s has non-directory destination ancestor %s"
                % (label, ancestor_label))
    return _observe(plan, path)


def _read_utf8(plan, path, label, missing_ok=False):
    snapshot = _observe(plan, path)
    if snapshot[0] == "missing" and missing_ok:
        return None
    if snapshot[0] != "file":
        raise OSError("%s is not a regular file" % label)
    try:
        return snapshot[1].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnicodeError(
            "%s is not valid UTF-8 at byte %d" % (label, exc.start))


def _marker_parts(match):
    if match.group("html_prefix"):
        return {
            "style": "html",
            "prefix": match.group("html_prefix"),
            "kind": match.group("html_kind"),
            "name": match.group("html_name"),
        }
    return {
        "style": "hash",
        "prefix": match.group("hash_prefix"),
        "kind": match.group("hash_kind"),
        "name": match.group("hash_name"),
    }


def _validate_markers(text, label):
    lines = text.splitlines(True)
    if text and not lines:
        lines = [text]
    open_marker = None
    seen = set()
    spans = []
    for index, line in enumerate(lines):
        match = MARKER_LINE_RE.match(line)
        if not match:
            stripped = line.strip()
            marker_like = any(
                stripped.startswith(prefix)
                for prefix in (
                    "<!-- " + BLOCK_PREFIX + ":",
                    "<!-- " + LEGACY_BLOCK_PREFIX + ":",
                    "# " + BLOCK_PREFIX + ":",
                    "# " + LEGACY_BLOCK_PREFIX + ":",
                )
            )
            if marker_like:
                raise MarkerError(
                    "%s has a malformed managed marker on line %d"
                    % (label, index + 1))
            continue
        marker = _marker_parts(match)
        marker["line"] = index
        identity = marker["name"]
        if marker["kind"] == "BEGIN":
            if open_marker is not None:
                raise MarkerError(
                    "%s has nested managed markers on line %d"
                    % (label, index + 1))
            if identity in seen:
                raise MarkerError(
                    "%s has duplicate managed marker block %s"
                    % (label, marker["name"]))
            seen.add(identity)
            open_marker = marker
            continue
        if open_marker is None:
            raise MarkerError(
                "%s has an END marker without a BEGIN on line %d"
                % (label, index + 1))
        if (marker["style"], marker["prefix"], marker["name"]) != (
                open_marker["style"], open_marker["prefix"],
                open_marker["name"]):
            raise MarkerError(
                "%s has mismatched managed markers ending on line %d"
                % (label, index + 1))
        spans.append({
            "style": marker["style"],
            "prefix": marker["prefix"],
            "name": marker["name"],
            "start": open_marker["line"],
            "end": index,
        })
        open_marker = None
    if open_marker is not None:
        raise MarkerError(
            "%s has an unclosed managed marker block %s"
            % (label, open_marker["name"]))
    return lines, spans


def _newline_for(lines, default="\n"):
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
    return default


def _render_block(name, content, style, newline):
    begin, end = markers(name, style=style)
    body = content.rstrip("\r\n").replace("\r\n", "\n").replace(
        "\n", newline)
    return begin + newline + body + newline + end + newline


def _rewrite_legacy_blocks(text, label, replacements=None):
    lines, spans = _validate_markers(text, label)
    replacements = replacements or {}
    starts = {span["start"]: span for span in spans}
    out = []
    index = 0
    while index < len(lines):
        span = starts.get(index)
        if span is None:
            out.append(lines[index])
            index += 1
            continue
        block_lines = lines[span["start"]:span["end"] + 1]
        if span["prefix"] == LEGACY_BLOCK_PREFIX \
                and span["name"] in replacements:
            newline = _newline_for(block_lines, _newline_for(lines))
            replacement = replacements[span["name"]]
            if isinstance(replacement, tuple):
                output_name, replacement = replacement
            else:
                output_name = span["name"]
            out.append(_render_block(
                output_name, replacement,
                span["style"], newline))
        elif span["prefix"] == LEGACY_BLOCK_PREFIX:
            block_lines[0] = block_lines[0].replace(
                LEGACY_BLOCK_PREFIX + ":BEGIN",
                BLOCK_PREFIX + ":BEGIN",
                1,
            )
            block_lines[-1] = block_lines[-1].replace(
                LEGACY_BLOCK_PREFIX + ":END",
                BLOCK_PREFIX + ":END",
                1,
            )
            out.extend(block_lines)
        else:
            out.extend(block_lines)
        index = span["end"] + 1
    rewritten = "".join(out)
    _validate_markers(rewritten, label)
    return rewritten


def _upsert_validated_block(text, name, content, style, label):
    lines, spans = _validate_markers(text, label)
    matching = [span for span in spans
                if span["prefix"] == BLOCK_PREFIX
                and span["style"] == style and span["name"] == name]
    newline = _newline_for(lines)
    rendered = _render_block(name, content, style, newline)
    if matching:
        span = matching[0]
        return "".join(lines[:span["start"]]) + rendered \
            + "".join(lines[span["end"] + 1:])
    if text:
        if text.endswith(newline + newline):
            separator = ""
        elif text.endswith(newline):
            separator = newline
        else:
            separator = newline + newline
        return text + separator + rendered
    return rendered


def _migrate_agents_text(old):
    old_lines, old_spans = _validate_markers(old, "AGENTS.md")
    protocol_spans = []
    for span in old_spans:
        if span["prefix"] != LEGACY_BLOCK_PREFIX:
            continue
        body_lines = old_lines[span["start"] + 1:span["end"]]
        has_protocol_heading = any(
            LEGACY_HEADING_RE.match(line.rstrip("\r\n"))
            for line in body_lines
        )
        if span["name"] == "agent-session-protocol" \
                or has_protocol_heading:
            protocol_spans.append(span)
    if len(protocol_spans) > 1:
        raise MarkerError(
            "AGENTS.md has duplicate legacy protocol managed blocks")
    replacements = {}
    if protocol_spans:
        replacements[protocol_spans[0]["name"]] = (
            "agent-session-protocol", session_protocol_block())
    new = _rewrite_legacy_blocks(
        old,
        "AGENTS.md",
        replacements,
    )
    lines, spans = _validate_markers(new, "AGENTS.md")
    covered = set()
    for span in spans:
        covered.update(range(span["start"], span["end"] + 1))
    headings = [
        index for index, line in enumerate(lines)
        if index not in covered
        and LEGACY_HEADING_RE.match(line.rstrip("\r\n"))
    ]
    if len(headings) > 1:
        raise MarkerError(
            "AGENTS.md has duplicate unmarked legacy protocol headings")
    if headings:
        start = headings[0]
        end = len(lines)
        span_starts = {span["start"] for span in spans}
        for index in range(start + 1, len(lines)):
            if index in span_starts \
                    or (index not in covered and lines[index].startswith("## ")):
                end = index
                break
        new = "".join(lines[:start]) + "".join(lines[end:])
        new = _upsert_validated_block(
            new,
            "agent-session-protocol",
            session_protocol_block(),
            "html",
            "AGENTS.md",
        )
    _validate_markers(new, "AGENTS.md")
    return new


def _migrate_gitignore_text(old):
    new = _rewrite_legacy_blocks(
        old,
        ".gitignore",
        {"runtime-state": gitignore_block()},
    )
    kept = []
    for line in new.splitlines(True):
        if line.rstrip("\r\n").strip() in KNOWN_LEGACY_GITIGNORE_RULES:
            continue
        kept.append(line)
    new = "".join(kept)
    return _upsert_validated_block(
        new, "runtime-state", gitignore_block(), "hash", ".gitignore")


def _remove_legacy_handoff_key(text):
    lines = text.splitlines(True)
    if not lines or lines[0].rstrip("\r\n").strip() != "---":
        return text, False
    end = None
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n").strip() == "---":
            end = index
            break
    if end is None:
        return text, False
    changed = False
    kept = [lines[0]]
    for line in lines[1:end]:
        if ":" in line and line.partition(":")[0].strip() == "last_commit":
            changed = True
            continue
        kept.append(line)
    kept.extend(lines[end:])
    return "".join(kept), changed


def _json_text(data):
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _append_progress_text(text, timestamp):
    lines = text.splitlines(True)
    newline = _newline_for(lines)
    entry = (
        "### %s — project-steward migrate%s%s%s%s"
        % (timestamp, newline, MIGRATION_PROGRESS_NOTE, newline, newline)
    )
    first_entry = None
    for index, line in enumerate(lines):
        if line.startswith("### "):
            first_entry = index
            break
    if first_entry is not None:
        return "".join(lines[:first_entry]) + entry + "".join(
            lines[first_entry:])
    base = text.rstrip("\r\n")
    if base:
        return base + newline + newline + entry
    return "# Progress log" + newline + newline + "Newest first." \
        + newline + newline + entry


def _progress_retry_matches(existing, base):
    header = re.compile(
        r"^### (?P<timestamp>[^\r\n]+) — project-steward migrate\r?$",
        re.MULTILINE,
    )
    matches = list(header.finditer(existing))
    if len(matches) != 1:
        return False
    timestamp = matches[0].group("timestamp")
    return bool(UTC_TIMESTAMP_RE.match(timestamp)) and existing == \
        _append_progress_text(base, timestamp)


def _state_retry_matches(text, project_name):
    try:
        data = json.loads(text)
    except ValueError:
        return False
    required = {
        "schema_version", "steward_version", "project_name", "created_at",
        "last_wrap_at", "last_checkpoint_at", "migrated_from", "migrated_at",
    }
    return isinstance(data, dict) and set(data) == required \
        and data.get("schema_version") == 1 \
        and data.get("steward_version") == __version__ \
        and data.get("project_name") == project_name \
        and data.get("last_wrap_at") is None \
        and data.get("last_checkpoint_at") is None \
        and data.get("migrated_from") == "projectforge" \
        and isinstance(data.get("created_at"), str) \
        and bool(UTC_TIMESTAMP_RE.match(data.get("created_at"))) \
        and isinstance(data.get("migrated_at"), str) \
        and bool(UTC_TIMESTAMP_RE.match(data.get("migrated_at")))


def _backend_retry_matches(text):
    try:
        data = json.loads(text)
    except ValueError:
        return False
    return isinstance(data, dict) and set(data) == {
        "schema_version", "name", "adopted_at", "notes",
    } and data.get("schema_version") == 1 \
        and data.get("name") == "markdown" \
        and isinstance(data.get("adopted_at"), str) \
        and bool(UTC_TIMESTAMP_RE.match(data.get("adopted_at"))) \
        and data.get("notes") == MIGRATION_BACKEND_NOTE


def _queue_exact_text(plan, rel, intended, source_label, moved_label=None):
    target = plan.root / rel
    snapshot = _observe_destination(plan, target, rel)
    if snapshot[0] == "missing":
        plan.writes[rel] = intended
        if moved_label:
            plan.moved.append(moved_label)
        return
    if snapshot[0] != "file":
        plan.conflicts.append("%s is not a regular file" % rel)
        return
    try:
        current = snapshot[1].decode("utf-8")
    except UnicodeDecodeError:
        plan.conflicts.append("%s is not valid UTF-8" % rel)
        return
    if current != intended:
        plan.conflicts.append(
            "%s differs from intended %s" % (rel, source_label))


def _queue_machine_text(plan, rel, intended, retry_matcher):
    target = plan.root / rel
    snapshot = _observe_destination(plan, target, rel)
    if snapshot[0] == "missing":
        plan.writes[rel] = intended
        return
    if snapshot[0] != "file":
        plan.conflicts.append("%s is not a regular file" % rel)
        return
    try:
        current = snapshot[1].decode("utf-8")
    except UnicodeDecodeError:
        plan.conflicts.append("%s is not valid UTF-8" % rel)
        return
    if current != intended and not retry_matcher(current):
        plan.conflicts.append(
            "%s is not recognized migration-generated metadata" % rel)


def plan_migration(root, project_name=""):
    """Return a read-only migration plan with all conflicts reported."""
    plan = MigrationPlan(Path(root), project_name)
    if not plan.legacy.is_dir() or plan.legacy.is_symlink():
        plan.ok = False
        plan.error = "No regular .projectforge/ directory found."
        return plan
    try:
        sdir_snapshot = _observe_destination(
            plan, state_dir(root), ".project-steward/")
    except Exception as exc:
        plan.ok = False
        plan.error = "Migration preflight failed: %s" % exc
        return plan
    if sdir_snapshot[0] not in ("missing", "dir"):
        plan.ok = False
        plan.error = ".project-steward/ is not a regular directory."
        return plan
    backup_root = state_dir(root) / "migration-backup-projectforge"
    try:
        backup_snapshot = _observe_destination(
            plan, backup_root,
            ".project-steward/migration-backup-projectforge/",
        )
    except Exception as exc:
        plan.ok = False
        plan.error = "Migration preflight failed: %s" % exc
        return plan
    if backup_snapshot[0] not in ("missing", "dir"):
        plan.ok = False
        plan.error = (
            ".project-steward/migration-backup-projectforge/ is not a "
            "regular directory.")
        return plan
    try:
        plan.legacy_manifest = _tree_manifest(plan.legacy)
    except Exception as exc:
        plan.ok = False
        plan.error = "Cannot preserve raw .projectforge/ tree: %s" % exc
        return plan

    issues = []
    now = utcnow_iso()
    transformed_progress = None
    for name in LEGACY_STATE_FILES:
        src = plan.legacy / name
        try:
            source_text = _read_utf8(
                plan, src, ".projectforge/%s" % name, missing_ok=True)
            if source_text is None:
                continue
            _validate_markers(source_text, ".projectforge/%s" % name)
            intended = _rewrite_legacy_blocks(
                source_text, ".projectforge/%s" % name)
            intended = intended.replace(".projectforge/", ".project-steward/")
            if name == "HANDOFF.md":
                intended, removed = _remove_legacy_handoff_key(intended)
                if removed:
                    plan.notes.append(
                        "Removed obsolete HANDOFF.md last_commit metadata.")
            if name == "PROGRESS.md":
                transformed_progress = intended
                continue
            _queue_exact_text(
                plan,
                ".project-steward/%s" % name,
                intended,
                "transformed .projectforge/%s" % name,
                name,
            )
        except Exception as exc:
            issues.append(str(exc))

    legacy_config = plan.legacy / "config"
    try:
        config_text = _read_utf8(
            plan, legacy_config, ".projectforge/config", missing_ok=True)
        if config_text is not None:
            config_values = parse_legacy_config(config_text)
            _validate_legacy_config(config_values)
            _queue_exact_text(
                plan,
                ".project-steward/config.toml",
                render_config_toml(config_values),
                "converted .projectforge/config",
                "config -> config.toml",
            )
    except Exception as exc:
        issues.append(str(exc))

    agents_path = plan.root / "AGENTS.md"
    try:
        agents_old = _read_utf8(
            plan, agents_path, "AGENTS.md", missing_ok=True)
        if agents_old is not None:
            agents_new = _migrate_agents_text(agents_old)
            if agents_new != agents_old:
                plan.writes["AGENTS.md"] = agents_new
                plan.backup_originals.append("AGENTS.md")
                plan.agents_diff = unified_diff(
                    agents_old, agents_new, "AGENTS.md")
            if ".project-steward/WORKFLOW.md" in agents_new:
                mapping = build_mapping({"backend_name": "markdown"})
                _queue_exact_text(
                    plan,
                    ".project-steward/WORKFLOW.md",
                    workflow_text(mapping),
                    "migration-generated workflow",
                )
    except Exception as exc:
        issues.append(str(exc))

    gitignore_path = plan.root / ".gitignore"
    try:
        gitignore_old = _read_utf8(
            plan, gitignore_path, ".gitignore", missing_ok=True)
        gitignore_old = gitignore_old if gitignore_old is not None else ""
        gitignore_new = _migrate_gitignore_text(gitignore_old)
        if gitignore_new != gitignore_old:
            plan.writes[".gitignore"] = gitignore_new
            plan.moved.append(".gitignore (managed block)")
            if _observe(plan, gitignore_path)[0] == "file":
                plan.backup_originals.append(".gitignore")
    except Exception as exc:
        issues.append(str(exc))

    try:
        state = default_state(project_name)
        state["migrated_from"] = "projectforge"
        state["migrated_at"] = now
        _queue_machine_text(
            plan,
            ".project-steward/state.json",
            _json_text(state),
            lambda text: _state_retry_matches(text, project_name),
        )
    except Exception as exc:
        issues.append("Cannot prepare .project-steward/state.json: %s" % exc)
    try:
        backend = {
            "schema_version": 1,
            "name": "markdown",
            "adopted_at": now,
            "notes": MIGRATION_BACKEND_NOTE,
        }
        _queue_machine_text(
            plan,
            ".project-steward/backend.json",
            _json_text(backend),
            _backend_retry_matches,
        )
    except Exception as exc:
        issues.append("Cannot prepare .project-steward/backend.json: %s" % exc)

    progress_base = transformed_progress
    if progress_base is None:
        progress_base = "# Progress log\n\nNewest first.\n"
    progress_path = state_dir(root) / "PROGRESS.md"
    try:
        progress_snapshot = _observe_destination(
            plan, progress_path, ".project-steward/PROGRESS.md")
        if progress_snapshot[0] == "missing":
            plan.writes[
                ".project-steward/PROGRESS.md"
            ] = _append_progress_text(progress_base, now)
            if transformed_progress is not None:
                plan.moved.append("PROGRESS.md")
        elif progress_snapshot[0] != "file":
            plan.conflicts.append(
                ".project-steward/PROGRESS.md is not a regular file")
        else:
            current_progress = progress_snapshot[1].decode("utf-8")
            if transformed_progress is not None:
                if current_progress == progress_base:
                    plan.writes[
                        ".project-steward/PROGRESS.md"
                    ] = _append_progress_text(progress_base, now)
                elif not _progress_retry_matches(
                        current_progress, progress_base):
                    plan.conflicts.append(
                        ".project-steward/PROGRESS.md differs from intended "
                        "transformed .projectforge/PROGRESS.md")
            elif current_progress == progress_base:
                plan.writes[
                    ".project-steward/PROGRESS.md"
                ] = _append_progress_text(progress_base, now)
            elif not _progress_retry_matches(current_progress, progress_base):
                plan.conflicts.append(
                    ".project-steward/PROGRESS.md is not recognized "
                    "migration-generated progress")
    except UnicodeDecodeError:
        plan.conflicts.append(
            ".project-steward/PROGRESS.md is not valid UTF-8")
    except Exception as exc:
        issues.append("Cannot inspect .project-steward/PROGRESS.md: %s" % exc)

    journal = plan.legacy / "journal"
    try:
        journal_snapshot = _path_snapshot(journal)
        if journal_snapshot[0] == "dir":
            target = state_dir(root) / "runtime/journal-legacy"
            target_snapshot = _observe_destination(
                plan, target,
                ".project-steward/runtime/journal-legacy/",
            )
            journal_manifest = _tree_manifest(journal)
            if target_snapshot[0] == "missing":
                plan.copies.append((journal, target, journal_manifest))
                plan.notes.append(
                    "journal/ will be preserved at runtime/journal-legacy/.")
            elif target_snapshot[0] != "dir":
                plan.conflicts.append(
                    ".project-steward/runtime/journal-legacy/ conflicts "
                    "with .projectforge/journal/")
            else:
                target_manifest = _tree_manifest(target)
                plan.observed_trees[_relative(plan, target)] = target_manifest
                if target_manifest != journal_manifest:
                    plan.conflicts.append(
                        ".project-steward/runtime/journal-legacy/ conflicts "
                        "with .projectforge/journal/")
        elif journal_snapshot[0] not in ("missing",):
            issues.append(".projectforge/journal is not a regular directory")
    except Exception as exc:
        issues.append("Cannot preserve legacy journal: %s" % exc)

    if issues:
        plan.ok = False
        plan.error = "Migration preflight failed: " + "; ".join(issues)
    if plan.conflicts:
        plan.ok = False
        detail = "; ".join(plan.conflicts)
        if plan.error:
            plan.error += "; conflicts: " + detail
        else:
            plan.error = "Migration preflight found conflicts: " + detail
    return plan


def _copy_raw_path(source, target):
    source = Path(source)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        os.symlink(os.readlink(str(source)), str(target))
    else:
        shutil.copy2(str(source), str(target))


def _fresh_backup(plan):
    backup_root = state_dir(plan.root) / "migration-backup-projectforge"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = utcnow_iso().replace("-", "").replace(":", "").replace("T", "-")
    attempt = backup_root / (
        "attempt-%s-%s" % (stamp, uuid.uuid4().hex[:12]))
    attempt.mkdir()
    attempt_ignore = attempt / ".gitignore"
    write_text_atomic(attempt_ignore, FRESH_BACKUP_GITIGNORE)
    if _path_snapshot(attempt_ignore) != (
            "file", FRESH_BACKUP_GITIGNORE.encode("utf-8")):
        raise OSError("write verification failed for %s" % _relative(
            plan, attempt_ignore))
    shutil.copytree(
        str(plan.legacy), str(attempt / ".projectforge"), symlinks=True)
    originals_root = attempt / BACKUP_ORIGINALS_DIR
    for rel in plan.backup_originals:
        _copy_raw_path(plan.root / rel, originals_root / rel)
    if _tree_manifest(attempt / ".projectforge") != plan.legacy_manifest:
        raise OSError("raw legacy backup verification failed")
    for rel in plan.backup_originals:
        if _path_snapshot(originals_root / rel) != plan.observed[rel]:
            raise OSError("backup verification failed for %s" % rel)
    return attempt


def _inputs_unchanged(plan):
    if _tree_manifest(plan.legacy) != plan.legacy_manifest:
        return False, ".projectforge/ changed after preflight"
    for rel, expected in plan.observed.items():
        if _path_snapshot(plan.root / rel) != expected:
            return False, "%s changed after preflight" % rel
    for rel, expected in plan.observed_trees.items():
        if _tree_manifest(plan.root / rel) != expected:
            return False, "%s changed after preflight" % rel
    return True, ""


def apply_migration(plan):
    """Apply one validated plan; keep legacy state on any failed attempt."""
    report = plan.report()
    if not plan.ok:
        return report
    try:
        unchanged, detail = _inputs_unchanged(plan)
        if not unchanged:
            report["ok"] = False
            report["error"] = "Migration stopped safely: %s." % detail
            report["will_remove_legacy"] = False
            return report
        backup = _fresh_backup(plan)
        report["backup"] = _relative(plan, backup)
        report["notes"].append("Backup written to %s" % backup)

        for rel, text in plan.writes.items():
            write_text_atomic(plan.root / rel, text)
        for source, target, _manifest in plan.copies:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(source), str(target), symlinks=True)

        for rel, text in plan.writes.items():
            snapshot = _path_snapshot(plan.root / rel)
            if snapshot != ("file", text.encode("utf-8")):
                raise OSError("write verification failed for %s" % rel)
        for _source, target, expected in plan.copies:
            if _tree_manifest(target) != expected:
                raise OSError(
                    "write verification failed for %s"
                    % _relative(plan, target))
        if _tree_manifest(backup / ".projectforge") != plan.legacy_manifest:
            raise OSError("raw legacy backup changed before removal")
        if _tree_manifest(plan.legacy) != plan.legacy_manifest:
            raise OSError(
                ".projectforge/ changed during migration; legacy state retained")

        shutil.rmtree(str(plan.legacy))
        report["notes"].append(
            ".projectforge/ removed after backup and write verification.")
        report["will_remove_legacy"] = False
        return report
    except Exception as exc:
        report["ok"] = False
        report["will_remove_legacy"] = False
        report["error"] = (
            "Migration write failed before completion: %s. Inspect the "
            "legacy tree and the fresh backup before retrying." % exc)
        return report


def migrate_agents_md(root):
    """Compatibility helper for callers that only convert AGENTS.md."""
    path = Path(root) / "AGENTS.md"
    if not path.is_file():
        return ""
    old = path.read_bytes().decode("utf-8")
    new = _migrate_agents_text(old)
    if new == old:
        return ""
    write_text_atomic(path, new)
    return unified_diff(old, new, "AGENTS.md")


def migrate(root, project_name=""):
    """Preflight and apply a migration without bypassing validation."""
    plan = plan_migration(root, project_name=project_name)
    return apply_migration(plan)
