"""Icon library dialog: browse the icons of the user's current icon theme."""

from . import gi_versions  # noqa: F401
from . import icons
from gi.repository import Adw, Gdk, Gtk


class LibraryDialog(Adw.Window):
    def __init__(self, parent: Gtk.Window, app_name: str, on_choose):
        super().__init__(transient_for=parent, modal=True, title="Choose icon")
        self.set_default_size(420, 520)
        self._on_choose = on_choose
        self._all = icons.theme_icon_names()
        self._words = icons.suggestion_words(app_name)

        header = Adw.HeaderBar(show_start_title_buttons=False, show_end_title_buttons=False)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda *_: self.close())
        self.select = Gtk.Button(label="Select", sensitive=False)
        self.select.add_css_class("suggested-action")
        self.select.connect("clicked", lambda *_: self._choose_selected())
        header.pack_start(cancel)
        header.pack_end(self.select)

        self.search = Gtk.SearchEntry(placeholder_text="Search icons")
        self.search.connect("search-changed", lambda *_: self._rebuild())

        self.note = Gtk.Label(xalign=0, wrap=True)
        self.note.add_css_class("dim-label")
        self.note.add_css_class("caption")

        self.model = Gtk.StringList()
        self.selection = Gtk.SingleSelection(model=self.model, autoselect=False, can_unselect=True)
        self.selection.connect(
            "notify::selected",
            lambda *_: self.select.set_sensitive(
                self.selection.get_selected() != Gtk.INVALID_LIST_POSITION
            ),
        )

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_item)
        factory.connect("bind", self._bind_item)

        grid = Gtk.GridView(model=self.selection, factory=factory, min_columns=3, max_columns=5)
        grid.connect("activate", lambda _g, pos: self._choose_at(pos))
        scroller = Gtk.ScrolledWindow(vexpand=True, child=grid)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("top", "bottom", "start", "end"):
            getattr(body, f"set_margin_{side}")(12)
        body.append(self.search)
        body.append(self.note)
        body.append(scroller)

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(body)
        self.set_content(view)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.add_controller(keys)

        self._rebuild()
        self.search.grab_focus()

    def _on_key(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _rebuild(self) -> None:
        query = self.search.get_text().strip().lower()
        if query:
            names = [n for n in self._all if query in n.lower()]
            self.note.set_visible(False)
        else:
            hits = [n for n in self._all if any(w in n.lower() for w in self._words)]
            hit_set = set(hits)
            rest = [n for n in self._all if n not in hit_set]
            names = hits + rest
            self.note.set_visible(bool(hits))
            self.note.set_text("Icons matching the name come first.")
        self.model.splice(0, self.model.get_n_items(), names)

    def _setup_item(self, _factory, item: Gtk.ListItem) -> None:
        image = Gtk.Image(pixel_size=48)
        label = Gtk.Label(ellipsize=3, max_width_chars=12)
        label.add_css_class("caption")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for side in ("top", "bottom"):
            getattr(box, f"set_margin_{side}")(8)
        box.append(image)
        box.append(label)
        item.set_child(box)

    def _bind_item(self, _factory, item: Gtk.ListItem) -> None:
        name = item.get_item().get_string()
        image, label = item.get_child().get_first_child(), item.get_child().get_last_child()
        image.set_from_icon_name(name)
        label.set_text(name)
        item.get_child().set_tooltip_text(name)

    def _choose_at(self, position: int) -> None:
        self.close()
        self._on_choose(self.model.get_string(position))

    def _choose_selected(self) -> None:
        position = self.selection.get_selected()
        if position != Gtk.INVALID_LIST_POSITION:
            self._choose_at(position)
