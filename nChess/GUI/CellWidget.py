from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color as KivyColor, Rectangle

from nChess.GUI.PieceWidget import PieceWidget


WHITE = (0.9, 0.9, 0.9, 1)
BLACK = (0.3, 0.3, 0.3, 1)
HIGHLIGHT = (0.9, 0.9, 0, 1)


class CellWidget(GridLayout):
    base_color: tuple[float, float, float, float]
    piece_widget: PieceWidget | None
    highlighted: bool

    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)

        self.rows = 1

        self.base_color = color
        self.piece_widget = None
        self.highlighted = False

        with self.canvas.before:
            self.fill_color = KivyColor(*self.base_color)
            self.background = Rectangle(
                pos=(self.x, self.y),
                size=(self.width, self.height)
            )

        self.bind(pos=self.update_cell)
        self.bind(size=self.update_cell)

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

    def toggle_highlight(self):
        self.set_highlighted(not self.highlighted)

    def set_highlighted(self, highlighted):
        self.highlighted = highlighted
        self.fill_color.rgba = HIGHLIGHT if highlighted else self.base_color

    def update_cell(self, *args, **kwargs):
        self.background.pos = (self.x, self.y)
        self.background.size = (self.width, self.height)

    def has_piece_widget(self):
        return self.piece_widget is not None

    def set_piece_widget(self, piece_widget):
        if self.piece_widget is not None:
            self.remove_piece_widget()
        self.piece_widget = piece_widget
        self.add_widget(self.piece_widget)

    def get_piece_widget(self):
        return self.piece_widget

    def remove_piece_widget(self):
        if self.piece_widget is None:
            return None
        piece_widget = self.piece_widget
        self.remove_widget(piece_widget)
        self.piece_widget = None
        return piece_widget

    def handle_touch(self, piece_widget=None):
        self.parent.handle_touch(self)
