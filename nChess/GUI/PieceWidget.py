from kivy.uix.image import Image


class PieceWidget(Image):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.parent.handle_touch(self)
            return True
        return super().on_touch_up(touch)
