"""Icon helpers: theme lookup, image loading, URL download, saving crops."""

import os
import re
import threading
import time
import urllib.request

from . import __version__, gi_versions  # noqa: F401
from gi.repository import Gdk, GLib, Gtk

ICONS_DIR = os.path.join(GLib.get_user_data_dir(), "icons", "deskcut")
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _theme() -> Gtk.IconTheme:
    return Gtk.IconTheme.get_for_display(Gdk.Display.get_default())


def theme_icon_names() -> list[str]:
    """Every icon name in the current theme, minus symbolic variants."""
    return sorted(n for n in _theme().get_icon_names() if not n.endswith("-symbolic"))


def has_theme_icon(name: str) -> bool:
    return bool(name) and not os.path.isabs(name) and _theme().has_icon(name)


def image_path(value: str) -> bool:
    return bool(value) and os.path.isabs(value) and os.path.isfile(value)


def paintable_for(value: str, size: int = 96, scale: int = 1) -> Gdk.Paintable | None:
    """What to draw for an Icon= value: a theme icon or an image file."""
    if image_path(value):
        try:
            return Gdk.Texture.new_from_filename(value)
        except GLib.Error:
            return None
    if has_theme_icon(value):
        return _theme().lookup_icon(
            value, None, size, scale, Gtk.TextDirection.NONE, Gtk.IconLookupFlags(0)
        )
    return None


def texture_from_file(path: str) -> Gdk.Texture:
    return Gdk.Texture.new_from_filename(path)


def texture_from_bytes(data: bytes) -> Gdk.Texture:
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(data))


def save_texture(name: str, texture: Gdk.Texture) -> str:
    """Store a cropped icon under ~/.local/share/icons/deskcut and return its path."""
    os.makedirs(ICONS_DIR, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_") or "icon"
    path = os.path.join(ICONS_DIR, f"{slug}-{int(time.time())}.png")
    if not texture.save_to_png(path):
        raise OSError("Couldn't write the icon image")
    return path


def suggestion_words(app_name: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", app_name.lower()) if len(w) > 1]


def fetch_image(url: str, on_done) -> None:
    """Download an image off the main thread.

    `on_done(texture, error)` is called on the main thread with one of them set.
    """

    def finish(data, error):
        texture = None
        if data is not None:
            try:
                texture = texture_from_bytes(data)
            except GLib.Error:
                error = "That file isn't an image GTK can read"
        on_done(texture, error)
        return GLib.SOURCE_REMOVE

    def work():
        try:
            if not re.match(r"https?://", url, re.I):
                raise ValueError("That isn't a web address")
            request = urllib.request.Request(
                url, headers={"User-Agent": f"DeskCut-GTK/{__version__}"}
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                if not response.headers.get_content_type().startswith("image/"):
                    raise ValueError("That link isn't an image")
                data = response.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise ValueError("That image is too large")
        except Exception as e:  # network, HTTP and validation errors alike
            GLib.idle_add(finish, None, str(e))
        else:
            GLib.idle_add(finish, data, None)

    threading.Thread(target=work, daemon=True).start()
