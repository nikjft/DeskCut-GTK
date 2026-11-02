"""Main window: icon well, shortcut fields, File and Edit menus."""

import os

from . import APP_NAME, desktopfile, gi_versions  # noqa: F401
from . import icons
from .crop import CropDialog
from .desktopfile import Shortcut
from .library import LibraryDialog
from .tags import CategoryRow
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

HINT = "Select the icon and paste, or drop an image on it."


def _menu(*sections) -> Gio.Menu:
    menu = Gio.Menu()
    for section in sections:
        part = Gio.Menu()
        for label, action in section:
            part.append(label, action)
        menu.append_section(None, part)
    return menu


class DeskCutWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title=APP_NAME, default_width=460, default_height=720)

        self.path: str | None = None  # the .desktop file being edited
        self.dirty = False
        self._loading = False
        self.icon_value = ""  # what gets written to Icon=
        self.icon_texture = None  # a cropped image not yet saved to disk
        self.icon_source = None  # the uncropped original, for adjusting again
        self._edit_target = None  # last focused text field or the icon well

        self._build_actions()
        self._build_ui()
        self.categories_row.set_tags(["Utility"])
        self._update_title()
        self._update_well()
        self.set_focus(self.name_row)
        self.connect("notify::focus-widget", self._remember_focus)
        self.connect("close-request", self._on_close_request)

    # ---------------------------------------------------------------- actions

    def _build_actions(self) -> None:
        handlers = {
            "new": lambda: self._guard(self.new_shortcut),
            "open": lambda: self._guard(self.open_dialog),
            "install": self.install,
            "edit-undo": lambda: self._edit("text.undo"),
            "edit-redo": lambda: self._edit("text.redo"),
            "edit-cut": lambda: self._edit("clipboard.cut"),
            "edit-copy": lambda: self._edit("clipboard.copy"),
            "edit-paste": lambda: self._edit("clipboard.paste"),
            "edit-delete": lambda: self._edit("selection.delete"),
            "edit-select-all": lambda: self._edit("selection.select-all"),
            "icon-paste": self.paste_icon,
            "icon-crop": self.adjust_crop,
            "icon-library": self.open_library,
            "icon-file": self.choose_image_file,
            "icon-remove": self.remove_icon,
        }
        for name, handler in handlers.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _a, _p, h=handler: h())
            self.add_action(action)

    def _edit(self, name: str) -> None:
        target = self._edit_target
        if target is None:
            return
        if target is self.well:
            if name == "clipboard.paste":
                self.paste_icon()
            return
        target.activate_action(name, None)

    def _remember_focus(self, *_args) -> None:
        widget = self.get_focus()
        if widget is self.well or isinstance(widget, Gtk.Text):
            self._edit_target = widget

    # --------------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        bar_model = Gio.Menu()
        bar_model.append_submenu(
            "File",
            _menu(
                [("New", "win.new"), ("Open…", "win.open")],
                [("Install", "win.install")],
                [("Quit", "app.quit")],
            ),
        )
        bar_model.append_submenu(
            "Edit",
            _menu(
                [("Undo", "win.edit-undo"), ("Redo", "win.edit-redo")],
                [
                    ("Cut", "win.edit-cut"),
                    ("Copy", "win.edit-copy"),
                    ("Paste", "win.edit-paste"),
                    ("Delete", "win.edit-delete"),
                ],
                [("Select All", "win.edit-select-all")],
            ),
        )
        menubar = Gtk.PopoverMenuBar.new_from_model(bar_model)

        self.title_widget = Adw.WindowTitle(title="New shortcut", subtitle=APP_NAME)
        header = Adw.HeaderBar(title_widget=self.title_widget)

        self.well = self._build_well()
        browse = Gtk.MenuButton(
            label="Browse",
            always_show_arrow=True,
            halign=Gtk.Align.CENTER,
            menu_model=_menu([("Library…", "win.icon-library"), ("File…", "win.icon-file")]),
        )
        browse.add_css_class("pill")
        self.hint = Gtk.Label(label=HINT, wrap=True, justify=Gtk.Justification.CENTER)
        self.hint.add_css_class("dim-label")
        self.hint.add_css_class("caption")

        self.name_row = Adw.EntryRow(title="Name")
        self.comment_row = Adw.EntryRow(title="Description")
        self.exec_row = Adw.EntryRow(title="Path")
        pick = Gtk.Button(icon_name="folder-symbolic", valign=Gtk.Align.CENTER)
        pick.add_css_class("flat")
        pick.set_tooltip_text("Choose application")
        pick.connect("clicked", lambda *_: self.choose_app())
        self.exec_row.add_suffix(pick)
        self.categories_row = CategoryRow(self._mark_dirty)
        self.terminal_row = Adw.SwitchRow(title="Open in terminal")
        for row in (self.name_row, self.comment_row, self.exec_row):
            row.connect("changed", self._mark_dirty)
        self.terminal_row.connect("notify::active", self._mark_dirty)

        group = Adw.PreferencesGroup()
        for row in (
            self.name_row,
            self.comment_row,
            self.exec_row,
            self.categories_row,
            self.terminal_row,
        ):
            group.add(row)

        self.destination = Gtk.Label(xalign=0, hexpand=True, ellipsize=3)
        self.destination.add_css_class("dim-label")
        self.destination.add_css_class("caption")
        install = Gtk.Button(label="Install")
        install.add_css_class("suggested-action")
        install.set_action_name("win.install")
        footer = Gtk.Box(spacing=12)
        footer.append(self.destination)
        footer.append(install)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.append(self.well)
        content.append(browse)
        content.append(self.hint)
        spacer = Gtk.Box()
        spacer.set_size_request(-1, 4)
        content.append(spacer)
        content.append(group)
        content.append(footer)

        clamp = Adw.Clamp(maximum_size=460, child=content)
        for side in ("top", "bottom", "start", "end"):
            getattr(clamp, f"set_margin_{side}")(18)
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=clamp)

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.add_top_bar(menubar)
        view.set_content(scroller)
        self.toasts = Adw.ToastOverlay(child=view)
        self.set_content(self.toasts)

    def _build_well(self) -> Gtk.Widget:
        well = Gtk.Overlay(focusable=True, halign=Gtk.Align.CENTER)
        well.add_css_class("well")
        well.set_overflow(Gtk.Overflow.HIDDEN)
        well.set_size_request(104, 104)
        well.set_tooltip_text("Icon. Select it, then paste an image or link")

        self.placeholder = Gtk.Image(icon_name="insert-image-symbolic", pixel_size=40)
        self.placeholder.add_css_class("dim-label")
        self.picture = Gtk.Picture(content_fit=Gtk.ContentFit.COVER, can_shrink=True)
        well.set_child(self.placeholder)
        well.add_overlay(self.picture)

        popover = Gtk.PopoverMenu.new_from_model(
            _menu(
                [("Paste", "win.icon-paste"), ("Adjust Crop…", "win.icon-crop")],
                [("Choose from Library…", "win.icon-library"), ("Choose File…", "win.icon-file")],
                [("Remove Icon", "win.icon-remove")],
            )
        )
        popover.set_parent(well)
        popover.set_has_arrow(False)
        popover.set_halign(Gtk.Align.START)

        click = Gtk.GestureClick(button=0)

        def on_press(gesture, _n, x, y):
            well.grab_focus()
            if gesture.get_current_button() == 3:
                point = Gdk.Rectangle()
                point.x, point.y, point.width, point.height = int(x), int(y), 1, 1
                popover.set_pointing_to(point)
                popover.popup()

        click.connect("pressed", on_press)
        well.add_controller(click)

        keys = Gtk.EventControllerKey()

        def on_key(_c, keyval, _code, state):
            if keyval in (Gdk.KEY_v, Gdk.KEY_V) and state & Gdk.ModifierType.CONTROL_MASK:
                self.paste_icon()
                return True
            return False

        keys.connect("key-pressed", on_key)
        well.add_controller(keys)

        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.set_gtypes([Gdk.Texture, Gdk.FileList, str])
        drop.connect("enter", lambda *_: (well.add_css_class("drop-active"), Gdk.DragAction.COPY)[1])
        drop.connect("leave", lambda *_: well.remove_css_class("drop-active"))
        drop.connect("drop", self._on_drop)
        well.add_controller(drop)
        return well

    # ------------------------------------------------------------- bookkeeping

    def toast(self, message: str) -> None:
        self.toasts.add_toast(Adw.Toast.new(message))

    def _mark_dirty(self, *_args) -> None:
        if not self._loading:
            self._set_dirty(True)

    def _set_dirty(self, dirty: bool) -> None:
        self.dirty = dirty
        self._update_title()

    def _update_title(self) -> None:
        name = os.path.basename(self.path) if self.path else "New shortcut"
        self.title_widget.set_title(("• " if self.dirty else "") + name)
        self.set_title(f"{name} — {APP_NAME}")
        self.destination.set_text(
            f"Editing {self.path}" if self.path else "Installs to ~/.local/share/applications"
        )

    def _update_well(self) -> None:
        paintable = self.icon_texture or icons.paintable_for(
            self.icon_value, 96, self.get_scale_factor()
        )
        self.picture.set_paintable(paintable)
        self.picture.set_visible(paintable is not None)
        self.placeholder.set_visible(paintable is None)
        croppable = self.icon_source is not None or icons.image_path(self.icon_value)
        self.lookup_action("icon-crop").set_enabled(croppable)

    def _guard(self, proceed) -> None:
        """Run `proceed` now, or after the user agrees to discard unsaved edits."""
        if not self.dirty:
            return proceed()
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Discard changes?",
            body="Your unsaved changes will be lost.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("discard", "Discard")
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", lambda _d, r: r == "discard" and proceed())
        dialog.present()

    def _on_close_request(self, _window) -> bool:
        if not self.dirty:
            return False
        self._guard(lambda: (setattr(self, "dirty", False), self.close()))
        return True

    # ------------------------------------------------------------ File actions

    def _populate(self, shortcut: Shortcut, path: str | None) -> None:
        self._loading = True
        self.name_row.set_text(shortcut.name)
        self.comment_row.set_text(shortcut.comment)
        self.exec_row.set_text(shortcut.exec)
        self.terminal_row.set_active(shortcut.terminal)
        self.categories_row.set_tags(shortcut.categories)
        self._loading = False
        self.path = path
        self.icon_value = shortcut.icon
        self.icon_texture = None
        self.icon_source = None
        self.hint.set_text(HINT)
        self._set_dirty(False)
        self._update_well()

    def new_shortcut(self) -> None:
        self._populate(Shortcut(categories=["Utility"]), None)

    def load_path(self, path: str) -> None:
        try:
            self._populate(desktopfile.load(path), path)
        except GLib.Error as e:
            self.toast(f"Couldn't open that file: {e.message}")

    def open_dialog(self) -> None:
        dialog = Gtk.FileDialog(title="Open shortcut")
        filt = Gtk.FileFilter(name="Desktop entries")
        filt.add_pattern("*.desktop")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filt)
        dialog.set_filters(filters)
        if os.path.isdir(desktopfile.APPS_DIR):
            dialog.set_initial_folder(Gio.File.new_for_path(desktopfile.APPS_DIR))

        def done(d, result):
            try:
                self.load_path(d.open_finish(result).get_path())
            except GLib.Error:
                pass  # dismissed

        dialog.open(self, None, done)

    def install(self) -> None:
        name = self.name_row.get_text().strip()
        exec_ = self.exec_row.get_text().strip()
        if not name or not exec_:
            return self.toast("Enter a name and a path first")
        try:
            icon = self.icon_value
            if self.icon_texture is not None:
                icon = icons.save_texture(name, self.icon_texture)
            existing = self.path
            path = desktopfile.save(
                Shortcut(
                    name=name,
                    comment=self.comment_row.get_text(),
                    exec=exec_,
                    icon=icon,
                    terminal=self.terminal_row.get_active(),
                    categories=self.categories_row.get_tags(),
                ),
                existing,
            )
        except (GLib.Error, OSError) as e:
            return self.toast(f"Couldn't save the shortcut: {getattr(e, 'message', e)}")
        self.icon_value, self.icon_texture, self.path = icon, None, path
        self.toast(("Updated " if existing else "Installed ") + os.path.basename(path))
        self._set_dirty(False)
        self._update_well()

    def choose_app(self) -> None:
        dialog = Gtk.FileDialog(title="Choose application")
        dialog.set_initial_folder(Gio.File.new_for_path("/usr/bin"))

        def done(d, result):
            try:
                self.exec_row.set_text(d.open_finish(result).get_path())
            except GLib.Error:
                pass

        dialog.open(self, None, done)

    # ------------------------------------------------------------ icon actions

    def open_crop(self, texture) -> None:
        def applied(cropped):
            self.icon_texture = cropped
            self.icon_source = texture
            self.icon_value = ""
            self.hint.set_text("Right-click the icon to adjust the crop again.")
            self._set_dirty(True)
            self._update_well()

        CropDialog(self, texture, applied).present()

    def adjust_crop(self) -> None:
        if self.icon_source is not None:
            return self.open_crop(self.icon_source)
        path = icons.resolve_image_path(self.icon_value)
        if path:
            try:
                self.open_crop(icons.texture_from_file(path))
            except GLib.Error as e:
                self.toast(e.message)

    def open_library(self) -> None:
        def chosen(name):
            self.icon_value, self.icon_texture, self.icon_source = name, None, None
            self._set_dirty(True)
            self._update_well()

        LibraryDialog(self, self.name_row.get_text(), chosen).present()

    def choose_image_file(self) -> None:
        dialog = Gtk.FileDialog(title="Choose icon image")
        filt = Gtk.FileFilter(name="Images")
        filt.add_mime_type("image/*")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filt)
        dialog.set_filters(filters)

        def done(d, result):
            try:
                path = d.open_finish(result).get_path()
            except GLib.Error:
                return
            self._open_crop_from_path(path)

        dialog.open(self, None, done)

    def remove_icon(self) -> None:
        self.icon_value, self.icon_texture, self.icon_source = "", None, None
        self._set_dirty(True)
        self._update_well()

    def _open_crop_from_path(self, path: str) -> None:
        try:
            self.open_crop(icons.texture_from_file(path))
        except GLib.Error:
            self.toast("That file isn't an image GTK can read")

    def _open_crop_from_url(self, url: str) -> None:
        self.hint.set_text("Downloading image…")

        def done(texture, error):
            self.hint.set_text(HINT)
            if error:
                self.toast(error)
            else:
                self.open_crop(texture)

        icons.fetch_image(url, done)

    def _open_crop_from_text(self, text: str) -> None:
        text = text.strip().splitlines()[0] if text.strip() else ""
        if text.startswith(("http://", "https://")):
            self._open_crop_from_url(text)
        elif text.startswith("file://"):
            self._open_crop_from_path(Gio.File.new_for_uri(text).get_path())
        elif os.path.isfile(text):
            self._open_crop_from_path(text)
        else:
            self.toast("That isn't an image or an image link")

    def paste_icon(self) -> None:
        clipboard = self.get_clipboard()
        formats = clipboard.get_formats()

        def read_texture(c, result):
            try:
                self.open_crop(c.read_texture_finish(result))
            except GLib.Error:
                self.toast("Couldn't read an image from the clipboard")

        def read_text(c, result):
            try:
                self._open_crop_from_text(c.read_text_finish(result) or "")
            except GLib.Error:
                self.toast("Nothing to paste")

        def read_files(c, result):
            try:
                files = c.read_value_finish(result).get_files()
                self._open_crop_from_path(files[0].get_path())
            except (GLib.Error, IndexError):
                self.toast("Couldn't read a file from the clipboard")

        if formats.contain_gtype(Gdk.Texture):
            clipboard.read_texture_async(None, read_texture)
        elif formats.contain_gtype(Gdk.FileList):
            clipboard.read_value_async(Gdk.FileList, GLib.PRIORITY_DEFAULT, None, read_files)
        else:
            clipboard.read_text_async(None, read_text)

    def _on_drop(self, target, value, _x, _y) -> bool:
        self.well.remove_css_class("drop-active")
        if isinstance(value, Gdk.Texture):
            self.open_crop(value)
        elif isinstance(value, Gdk.FileList):
            files = value.get_files()
            if not files:
                return False
            self._open_crop_from_path(files[0].get_path())
        elif isinstance(value, str):
            self._open_crop_from_text(value)
        else:
            return False
        return True
