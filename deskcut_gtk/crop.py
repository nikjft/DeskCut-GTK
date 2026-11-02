"""Crop dialog: drag to reposition, slide to zoom, apply to get a square icon."""

from . import gi_versions  # noqa: F401
from gi.repository import Adw, Gdk, Graphene, Gsk, Gtk

def _rgba(r, g, b, a=1.0) -> Gdk.RGBA:
    # PyGObject ignores constructor arguments for Gdk.RGBA, so set the fields.
    color = Gdk.RGBA()
    color.red, color.green, color.blue, color.alpha = r, g, b, a
    return color


STAGE = 280
CROP = 220
RADIUS = 48
OUTPUT = 256


class CropArea(Gtk.Widget):
    __gtype_name__ = "DeskCutCropArea"

    def __init__(self, texture: Gdk.Texture):
        super().__init__()
        self.texture = texture
        self.zoom = 1.0
        self.ox = 0.0
        self.oy = 0.0
        self._drag_origin = (0.0, 0.0)
        self.set_size_request(STAGE, STAGE)
        self.set_halign(Gtk.Align.CENTER)
        self.set_cursor_from_name("grab")

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", lambda *_: setattr(self, "_drag_origin", (self.ox, self.oy)))
        drag.connect("drag-update", self._on_drag)
        self.add_controller(drag)

    def set_zoom(self, zoom: float) -> None:
        self.zoom = zoom
        self.queue_draw()

    def _on_drag(self, _gesture, dx, dy):
        self.ox = self._drag_origin[0] + dx
        self.oy = self._drag_origin[1] + dy
        self.queue_draw()

    def _geometry(self):
        tw, th = self.texture.get_width(), self.texture.get_height()
        scale = max(CROP / tw, CROP / th) * self.zoom
        w, h = tw * scale, th * scale
        max_x, max_y = max(0.0, (w - CROP) / 2), max(0.0, (h - CROP) / 2)
        self.ox = max(-max_x, min(max_x, self.ox))
        self.oy = max(-max_y, min(max_y, self.oy))
        return w, h

    def _crop_outline(self) -> Gsk.RoundedRect:
        margin = (STAGE - CROP) / 2
        outline = Gsk.RoundedRect()
        outline.init_from_rect(Graphene.Rect().init(margin, margin, CROP, CROP), RADIUS)
        return outline

    def _draw_image(self, snapshot: Gtk.Snapshot) -> None:
        w, h = self._geometry()
        snapshot.save()
        snapshot.translate(Graphene.Point().init(STAGE / 2 + self.ox - w / 2, STAGE / 2 + self.oy - h / 2))
        rect = Graphene.Rect().init(0, 0, w, h)
        if hasattr(snapshot, "append_scaled_texture"):
            snapshot.append_scaled_texture(self.texture, Gsk.ScalingFilter.TRILINEAR, rect)
        else:
            snapshot.append_texture(self.texture, rect)
        snapshot.restore()

    def do_snapshot(self, snapshot: Gtk.Snapshot) -> None:
        stage = Graphene.Rect().init(0, 0, STAGE, STAGE)
        snapshot.push_clip(stage)
        snapshot.append_color(_rgba(0.13, 0.13, 0.13), stage)
        self._draw_image(snapshot)
        outline = self._crop_outline()
        snapshot.append_outset_shadow(outline, _rgba(0, 0, 0, 0.55), 0, 0, 400, 0)
        white = _rgba(1, 1, 1)
        snapshot.append_border(outline, [2, 2, 2, 2], [white] * 4)
        snapshot.pop()

    def render(self) -> Gdk.Texture:
        """The cropped region as a square texture with rounded corners."""
        margin = (STAGE - CROP) / 2
        snapshot = Gtk.Snapshot()
        factor = OUTPUT / CROP
        snapshot.scale(factor, factor)
        snapshot.translate(Graphene.Point().init(-margin, -margin))
        snapshot.push_rounded_clip(self._crop_outline())
        self._draw_image(snapshot)
        snapshot.pop()
        node = snapshot.to_node()
        renderer = self.get_native().get_renderer()
        return renderer.render_texture(node, Graphene.Rect().init(0, 0, OUTPUT, OUTPUT))


class CropDialog(Adw.Window):
    def __init__(self, parent: Gtk.Window, texture: Gdk.Texture, on_apply):
        super().__init__(transient_for=parent, modal=True, title="Adjust icon")
        self.set_resizable(False)
        self._on_apply = on_apply

        header = Adw.HeaderBar(show_start_title_buttons=False, show_end_title_buttons=False)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda *_: self.close())
        apply = Gtk.Button(label="Apply")
        apply.add_css_class("suggested-action")
        apply.connect("clicked", self._apply)
        header.pack_start(cancel)
        header.pack_end(apply)

        self.area = CropArea(texture)

        zoom = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1.0, 4.0, 0.01)
        zoom.set_draw_value(False)
        zoom.set_hexpand(True)
        zoom.update_property([Gtk.AccessibleProperty.LABEL], ["Zoom"])
        zoom.connect("value-changed", lambda s: self.area.set_zoom(s.get_value()))
        zoom_row = Gtk.Box(spacing=10)
        zoom_row.append(Gtk.Image.new_from_icon_name("zoom-out-symbolic"))
        zoom_row.append(zoom)
        zoom_row.append(Gtk.Image.new_from_icon_name("zoom-in-symbolic"))

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for side in ("top", "bottom", "start", "end"):
            getattr(body, f"set_margin_{side}")(18)
        body.append(self.area)
        body.append(zoom_row)

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(body)
        self.set_content(view)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._on_key)
        self.add_controller(keys)

    def _on_key(self, _controller, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _apply(self, _button):
        texture = self.area.render()
        self.close()
        self._on_apply(texture)
