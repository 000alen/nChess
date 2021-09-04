from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Rectangle, Color

from nChess.GUI.PieceWidget import PieceWidget


WHITE = (0.9, 0.9, 0.9, 1)
BLACK = (0.3, 0.3, 0.3, 1)
HIGHLIGHT = (0.9, 0.9, 0, 1)


class CellWidget(GridLayout):
    color: Color
    piece_widget: PieceWidget
    highlighted: bool

    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)

        self.rows = 1

        self.color = color
        self.piece_widget = None
        self.highlighted = False

        self.draw_cell()

        self.bind(pos=self.update_cell)
        self.bind(size=self.update_cell)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.handle_touch(self)
        else:
            return super().on_touch_up(touch)

    def toggle_highlight(self):
        if self.highlighted:
            self.draw_cell()
        else:
            with self.canvas.before:
                Color(*HIGHLIGHT)
                self.background = Rectangle(
                    pos=(self.x, self.y),
                    size=(self.width, self.height)
                )

        self.highlighted = not self.highlighted

    def draw_cell(self):
        with self.canvas.before:
            Color(*self.color)
            self.background = Rectangle(
                pos=(self.x, self.y),
                size=(self.width, self.height)
            )

    def update_cell(self, *args, **kwargs):
        self.background.pos = (self.x, self.y)
        self.background.size = (self.width, self.height)

    def has_piece_widget(self):
        return self.piece_widget is not None

    def set_piece_widget(self, piece):
        self.piece_widget = piece
        self.add_widget(self.piece_widget, index=0)

    def get_piece_widget(self):
        return self.piece_widget

    def remove_piece_widget(self):
        self.remove_widget(self.piece_widget)
        self.piece_widget = None

    def handle_touch(self, piece_instance):
        self.parent.handle_touch(self)
