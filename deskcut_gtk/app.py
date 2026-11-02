import sys

from . import APP_ID, gi_versions  # noqa: F401
from .window import DeskCutWindow
from gi.repository import Adw, Gdk, Gio, Gtk

CSS = """
.well {
  background-color: @card_bg_color;
  border: 1px solid @borders;
  border-radius: 22px;
}
.tag-pill {
  background-color: alpha(@accent_bg_color, 0.18);
  border-radius: 14px;
  padding: 2px 4px 2px 12px;
}
.tag-pill button {
  min-width: 20px;
  min-height: 20px;
  padding: 0;
}
.well:focus, .well.drop-active {
  outline: 2px solid @accent_bg_color;
  outline-offset: -2px;
}
"""


class DeskCutApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_startup(self):
        Adw.Application.do_startup(self)
        provider = Gtk.CssProvider()
        if hasattr(provider, "load_from_string"):
            provider.load_from_string(CSS)
        else:
            provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.get_active_window().close())
        self.add_action(quit_action)
        for action, accel in {
            "win.new": "<Control>n",
            "win.open": "<Control>o",
            "win.install": "<Control>s",
            "app.quit": "<Control>q",
        }.items():
            self.set_accels_for_action(action, [accel])

    def _window(self) -> DeskCutWindow:
        return self.props.active_window or DeskCutWindow(self)

    def do_activate(self):
        self._window().present()

    def do_open(self, files, _n_files, _hint):
        window = self._window()
        window.load_path(files[0].get_path())
        window.present()


def main() -> int:
    return DeskCutApp().run(sys.argv)
