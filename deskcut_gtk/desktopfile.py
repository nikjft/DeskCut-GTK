"""Reading and writing .desktop files.

Only the keys DeskCut manages are touched. Everything else in an existing
file (Categories, MimeType, localized names, other groups, comments) is kept
as it was, because GLib.KeyFile round-trips it.
"""

import os
import re
from dataclasses import dataclass, field

from gi.repository import GLib

from . import categories

GROUP = "Desktop Entry"
APPS_DIR = os.path.join(GLib.get_user_data_dir(), "applications")

_NEEDS_QUOTES = re.compile(r"[\s\"'`$\\<>~|&;*?#()]")


@dataclass
class Shortcut:
    name: str = ""
    comment: str = ""
    exec: str = ""
    icon: str = ""
    terminal: bool = False
    categories: list[str] = field(default_factory=list)


def format_exec(value: str) -> str:
    """Quote a bare path that needs it; pass command lines through untouched.

    A value that is already quoted, or that is not an existing file, is a
    command line the user typed on purpose (arguments, %U and so on).
    """
    value = value.strip()
    if value[:1] in ('"', "'"):
        return value
    if not _NEEDS_QUOTES.search(value) or not os.path.exists(value):
        return value
    quoted = re.sub(r'([\\"`$])', r"\\\1", value).replace("%", "%%")
    return f'"{quoted}"'


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_") or "shortcut"


def _unique_path(directory: str, base: str, ext: str) -> str:
    candidate = os.path.join(directory, base + ext)
    n = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}_{n}{ext}")
        n += 1
    return candidate


def _get(keyfile: GLib.KeyFile, key: str) -> str:
    try:
        return keyfile.get_string(GROUP, key)
    except GLib.Error:
        return ""


def load(path: str) -> Shortcut:
    keyfile = GLib.KeyFile()
    keyfile.load_from_file(path, GLib.KeyFileFlags.NONE)
    try:
        terminal = keyfile.get_boolean(GROUP, "Terminal")
    except GLib.Error:
        terminal = False
    return Shortcut(
        name=_get(keyfile, "Name"),
        comment=_get(keyfile, "Comment"),
        exec=_get(keyfile, "Exec"),
        icon=_get(keyfile, "Icon"),
        terminal=terminal,
        categories=categories.parse(_get(keyfile, "Categories")),
    )


def save(shortcut: Shortcut, path: str | None = None) -> str:
    """Write the shortcut and return the path of the .desktop file.

    With an existing `path` the file is updated in place; otherwise a new
    file is created in the user's applications folder.
    """
    keyfile = GLib.KeyFile()
    if path and os.path.exists(path):
        keyfile.load_from_file(
            path, GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS
        )
    else:
        os.makedirs(APPS_DIR, exist_ok=True)
        path = _unique_path(APPS_DIR, _slug(shortcut.name), ".desktop")

    # DeskCut only makes application launchers, so this is always Application.
    keyfile.set_string(GROUP, "Type", "Application")
    if shortcut.categories:
        keyfile.set_string(GROUP, "Categories", categories.join(shortcut.categories))
    else:
        try:
            keyfile.remove_key(GROUP, "Categories")
        except GLib.Error:
            pass

    keyfile.set_string(GROUP, "Name", shortcut.name)
    keyfile.set_string(GROUP, "Comment", shortcut.comment)
    keyfile.set_string(GROUP, "Exec", format_exec(shortcut.exec))
    keyfile.set_string(GROUP, "Icon", shortcut.icon)
    keyfile.set_boolean(GROUP, "Terminal", shortcut.terminal)

    GLib.file_set_contents(path, keyfile.to_data()[0].encode("utf-8"))
    os.chmod(path, 0o755)
    return path
