"""Minimal TOML subset reader for Python 3.7-3.10 (tomllib used on 3.11+).

Supports exactly what Project Steward's config.toml needs:
  * ``[section]`` and ``[a.b]`` tables (nested dicts)
  * ``key = "string"`` / ``'string'`` / integer / float / true / false
  * full-line and trailing ``#`` comments (quote-aware)
It intentionally does NOT support arrays, multi-line strings, dates, or
inline tables. Keep config.toml flat and simple.
"""
from __future__ import annotations


class TomlMiniError(ValueError):
    pass


def _strip_comment(line):
    out = []
    quote = None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).strip()


def _parse_value(raw, lineno):
    raw = raw.strip()
    if not raw:
        raise TomlMiniError("line %d: empty value" % lineno)
    if raw[0] in ("'", '"'):
        if len(raw) < 2 or raw[-1] != raw[0]:
            raise TomlMiniError("line %d: unterminated string" % lineno)
        return raw[1:-1]
    low = raw.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    raise TomlMiniError("line %d: unsupported value %r" % (lineno, raw))


def loads(text):
    root = {}
    table = root
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw_line)
        if not line:
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise TomlMiniError("line %d: bad table header" % lineno)
            name = line[1:-1].strip()
            if not name:
                raise TomlMiniError("line %d: empty table name" % lineno)
            table = root
            for part in name.split("."):
                part = part.strip()
                if not part:
                    raise TomlMiniError("line %d: bad table name" % lineno)
                table = table.setdefault(part, {})
                if not isinstance(table, dict):
                    raise TomlMiniError("line %d: table/key clash" % lineno)
            continue
        if "=" not in line:
            raise TomlMiniError("line %d: expected key = value" % lineno)
        key, _, value = line.partition("=")
        key = key.strip().strip('"').strip("'")
        if not key:
            raise TomlMiniError("line %d: empty key" % lineno)
        table[key] = _parse_value(value, lineno)
    return root


def load_toml_text(text):
    """Parse TOML text with tomllib when available, else the mini reader."""
    try:
        import tomllib  # Python 3.11+

        return tomllib.loads(text)
    except ImportError:
        return loads(text)
