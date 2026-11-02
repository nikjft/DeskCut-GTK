"""A row of removable category "pills" with a typeahead entry."""

from . import categories, gi_versions  # noqa: F401
from gi.repository import Adw, Gdk, Gtk


class CategoryRow(Adw.PreferencesRow):
    def __init__(self, on_changed):
        super().__init__(title="Categories", activatable=False, focusable=False)
        self._tags: list[str] = []
        self._on_changed = on_changed

        title = Gtk.Label(label="Categories", xalign=0)
        title.add_css_class("dim-label")
        title.add_css_class("caption")

        self.flow = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=False,
            max_children_per_line=30,
            column_spacing=6,
            row_spacing=6,
        )

        self.entry = Gtk.Entry(placeholder_text="Add category", width_chars=14, has_frame=False)
        self.entry.connect("activate", lambda e: self._commit(e.get_text()))
        self.entry.connect("changed", self._on_entry_changed)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.entry.add_controller(keys)

        self._store = Gtk.ListStore(str)
        for name in categories.KNOWN:
            self._store.append([name])
        completion = Gtk.EntryCompletion(
            model=self._store, text_column=0, minimum_key_length=1, popup_single_match=True
        )
        completion.set_match_func(self._match, None)
        completion.connect("match-selected", self._on_match_selected)
        self.entry.set_completion(completion)

        self.hint = Gtk.Label(
            label="Add a main category, like Utility, so the shortcut shows in the app menu.",
            xalign=0,
            wrap=True,
        )
        self.hint.add_css_class("dim-label")
        self.hint.add_css_class("caption")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for side, size in (("top", 10), ("bottom", 10), ("start", 12), ("end", 12)):
            getattr(box, f"set_margin_{side}")(size)
        box.append(title)
        box.append(self.flow)
        box.append(self.hint)
        self.set_child(box)

        click = Gtk.GestureClick()
        click.connect("released", lambda *_: self.entry.grab_focus())
        box.add_controller(click)

        self._render()

    # ------------------------------------------------------------------- API

    def get_tags(self) -> list[str]:
        return list(self._tags)

    def set_tags(self, tags: list[str]) -> None:
        self._tags = list(tags)
        self._render()

    # ------------------------------------------------------------- internals

    def _match(self, _completion, key, tree_iter, _data) -> bool:
        name = self._store.get_value(tree_iter, 0)
        return key.lower() in name.lower() and name not in self._tags

    def _on_match_selected(self, _completion, model, tree_iter) -> bool:
        self._commit(model.get_value(tree_iter, 0))
        return True

    def _on_entry_changed(self, entry) -> None:
        text = entry.get_text()
        if text.endswith((";", ",")):
            self._commit(text[:-1])

    def _on_key(self, _controller, keyval, _code, _state) -> bool:
        if keyval == Gdk.KEY_BackSpace and not self.entry.get_text() and self._tags:
            self._tags.pop()
            self._changed()
            return True
        return False

    def _commit(self, text: str) -> None:
        self.entry.set_text("")
        name = categories.normalize(text)
        if name and name not in self._tags:
            self._tags.append(name)
            self._changed()

    def _remove(self, name: str) -> None:
        self._tags.remove(name)
        self._changed()

    def _changed(self) -> None:
        self._render()
        self.entry.grab_focus()
        self._on_changed()

    def _pill(self, name: str) -> Gtk.Widget:
        label = Gtk.Label(label=name)
        remove = Gtk.Button(icon_name="window-close-symbolic", valign=Gtk.Align.CENTER)
        remove.add_css_class("flat")
        remove.add_css_class("circular")
        remove.set_tooltip_text(f"Remove {name}")
        remove.update_property([Gtk.AccessibleProperty.LABEL], [f"Remove {name}"])
        remove.connect("clicked", lambda *_: self._remove(name))
        pill = Gtk.Box(spacing=2, halign=Gtk.Align.START)
        pill.add_css_class("tag-pill")
        pill.append(label)
        pill.append(remove)
        return pill

    def _render(self) -> None:
        # Free the entry from its FlowBox wrapper before the wrapper is removed.
        wrapper = self.entry.get_parent()
        if wrapper is not None:
            wrapper.set_child(None)
        child = self.flow.get_first_child()
        while child is not None:
            following = child.get_next_sibling()
            self.flow.remove(child)
            child = following
        for name in self._tags:
            self.flow.append(self._pill(name))
        self.flow.append(self.entry)
        index = 0
        while (wrapper := self.flow.get_child_at_index(index)) is not None:
            wrapper.set_focusable(False)
            index += 1
        self.hint.set_visible(not categories.has_main(self._tags))
