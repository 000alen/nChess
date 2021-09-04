from kivy.uix.image import Image

class PieceWidget(Image):
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.handle_touch(self)
        else:
            return super().on_touch_up(touch)
