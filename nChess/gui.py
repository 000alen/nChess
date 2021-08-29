from nChess.utils import PNG, WhiteQueen, BlackQueen

from kivy.core.window import Window
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import DragBehavior
from kivy.graphics import Color, Rectangle

Window.size = (600, 600)

WHITE = (0.9, 0.9, 0.9, 1)
BLACK = (0.3, 0.3, 0.3, 1)
HIGHLIGHT = (0.9, 0.9, 0, 1)


class Piece(Image):
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.handle_touch(self)
        else:
            return super().on_touch_up(touch)


class Cell(GridLayout):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)

        self.rows = 1

        self.color = color
        self.piece = None
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
        self.canvas.clear()

        if self.highlighted:
            self.draw_cell()
        else:
            with self.canvas:
                Color(*HIGHLIGHT)
                self.background = Rectangle(
                    pos=(self.x, self.y),
                    size=(self.width, self.height)
                )

        self.highlighted = not self.highlighted

        if self.has_piece():
            source = self.get_piece().source
            self.remove_widget(self.piece)
            self.add_widget(Piece(source=source), index=0)

    def draw_cell(self):
        with self.canvas:
            Color(*self.color)
            self.background = Rectangle(
                pos=(self.x, self.y),
                size=(self.width, self.height)
            )

    def update_cell(self, *args, **kwargs):
        self.background.pos = (self.x, self.y)
        self.background.size = (self.width, self.height)

    def has_piece(self):
        return self.piece is not None

    def set_piece(self, piece):
        self.piece = piece
        self.add_widget(self.piece, index=0)

    def get_piece(self):
        return self.piece

    def remove_piece(self):
        self.remove_widget(self.piece)
        self.piece = None

    def handle_touch(self, piece_instance):
        self.parent.handle_touch(self)


class Board(GridLayout):
    def __init__(self, board_rows: int, board_columns: int, n_board=False, **kwargs):
        super().__init__(**kwargs)

        self.rows = board_rows

        self.board_rows = board_rows
        self.board_columns = board_columns
        self.n_board = n_board

        self.cells = []
        for i in range(self.board_rows):
            self.cells.append([])
            for j in range(self.board_columns):
                cell = Cell(BLACK if (i + j) % 2 == 0 else WHITE)
                self.cells[i].append(cell)
                self.add_widget(cell, index=100)

    def has_piece(self, i, j):
        return self.cells[i][j].has_piece()

    def set_piece(self, piece, i, j):
        self.cells[i][j].set_piece(piece)

    def get_piece(self, i, j):
        return self.cells[i][j].get_piece()

    def remove_piece(self, i, j):
        self.cells[i][j].remove_piece()

    def move_piece(self, i_1, j_1, i_2, j_2):
        piece = self.get_piece(i_1, j_1)
        self.remove_piece(i_1, j_1)
        self.set_piece(piece, i_2, j_2)

    def find_cell(self, cell):
        for i in range(self.board_rows):
            for j in range(self.board_columns):
                if self.cells[i][j] == cell:
                    return i, j

    def toggle_highlight(self, i, j):
        self.cells[i][j].toggle_highlight()

    def handle_touch(self, cell_instance):
        if self.n_board:
            i, j = self.find_cell(cell_instance)
            self.parent.handle_touch(self, i, j)
        else:
            print("Board", cell_instance)


class nBoard(GridLayout):
    def __init__(self, board_dimension: int, board_size: int, **kwargs):
        assert 2 <= board_dimension <= 4
        
        super().__init__(**kwargs)

        self.spacing = [10, 10]
        self.padding = [10, 10]

        self.board_dimension = board_dimension
        self.board_size = board_size

        self.position_a = None

        self.boards = []
        if self.board_dimension == 2:
            self.rows = 1
            board = Board(*board_size, n_board=True)
            self.boards.append(board)
            self.add_widget(board)
        elif self.board_dimension == 3:
            self.rows = 1
            for i in range(board_size[2]):
                board = Board(*board_size[:2], n_board=True)
                self.boards.append(board)
                self.add_widget(board)
        elif self.board_dimension == 4:
            self.rows = board_size[2]
            for i in range(board_size[2]):
                self.boards.append([])
                for j in range(board_size[3]):
                    board = Board(*board_size[:2], n_board=True)
                    self.boards[i].append(board)
                    self.add_widget(board)
        else:
            raise Exception

    def has_piece(self, position: tuple[int, ...]):
        if self.board_dimension == 2:
            return self.boards[0].has_piece(*position)
        elif self.board_dimension == 3:
            return self.boards[position[2]].has_piece(*position[:2])
        elif self.board_dimension == 4:
            return self.boards[position[2]][position[3]].has_piece(*position[:2])
        else:
            raise Exception

    def set_piece(self, piece, position: tuple[int, ...]):
        if self.board_dimension == 2:
            self.boards[0].set_piece(piece, *position)
        elif self.board_dimension == 3:
            self.boards[position[2]].set_piece(piece, *position[:2])
        elif self.board_dimension == 4:
            self.boards[position[2]][position[3]].set_piece(piece, *position[:2])
        else:
            raise Exception

    def get_piece(self, position: tuple[int, ...]):
        if self.board_dimension == 2:
            return self.boards[0].get_piece(*position)
        elif self.board_dimension == 3:
            return self.boards[position[2]].get_piece(*position[:2])
        elif self.board_dimension == 4:
            return self.boards[position[2]][position[3]].get_piece(*position[:2])
        else:
            raise Exception

    def remove_piece(self, position: tuple[int, ...]):
        if self.board_dimension == 2:
            self.boards[0].remove_piece(*position)
        elif self.board_dimension == 3:
            self.boards[position[2]].remove_piece(*position[:2])
        elif self.board_dimension == 4:
            self.boards[position[2]][position[3]].remove_piece(*position[:2])
        else:
            raise Exception

    def move_piece(self, initial_position, final_position):
        source = self.get_piece(initial_position).source
        self.remove_piece(initial_position)
        self.set_piece(Piece(source=source), final_position)

    def find_board(self, board):
        if self.board_dimension == 2:
            return 0
        elif self.board_dimension == 3:
            for i in range(self.board_size[2]):
                if self.boards[i] == board:
                    return i
        elif self.board_dimension == 4:
            for i in range(self.board_size[2]):
                for j in range(self.board_size[3]):
                    if self.boards[i][j] == board:
                        return i, j
        else:
            raise Exception

    def toggle_highlight(self, position: tuple[int, ...]):
        if self.board_dimension == 2:
            self.boards[0].toggle_highlight(*position)
        elif self.board_dimension == 3:
            self.boards[position[2]].toggle_highlight(*position[:2])
        elif self.board_dimension == 4:
            self.boards[position[2]][position[3]].toggle_highlight(*position[:2])
        else:
            raise Exception

    def handle_touch(self, board, i, j):
        if self.board_dimension == 2:
            position = (i, j)            
        elif self.board_dimension == 3:
            k = self.find_board(board)
            position = (i, j, k)
        elif self.board_dimension == 4:
            k, h = self.find_board(board)
            position = (i, j, k, h)
        else:
            raise Exception

        self.toggle_highlight(position)

        if self.has_piece(position):
            if self.position_a is None:
                self.position_a = position
            elif self.position_a == position:
                self.toggle_highlight(self.position_a)
                self.position_a = None
            else:
                self.remove_piece(position)
                self.move_piece(self.position_a, position)
                self.toggle_highlight(self.position_a)
                self.toggle_highlight(position)
                self.position_a = None
        else:
            if self.position_a is None:
                self.toggle_highlight(position)
            elif self.position_a == position:
                self.toggle_highlight(self.position_a)
                self.position_a = None
            else:
                self.move_piece(self.position_a, position)
                self.toggle_highlight(self.position_a)
                self.toggle_highlight(position)
                self.position_a = None


class ChessApp(App):
    def __init__(self, board_dimension: int, board_size: int, **kwargs):
        assert 2 <= board_dimension <= 4

        super().__init__(**kwargs)

        self.board_dimension = board_dimension
        self.board_size = board_size

    def build(self):
        self.n_board = nBoard(self.board_dimension, self.board_size)
        
        self.n_board.set_piece(Piece(source=PNG[WhiteQueen]), (0, 0, 0, 0))
        self.n_board.set_piece(Piece(source=PNG[BlackQueen]), (3, 3, 3, 3))

        return self.n_board


if __name__ == "__main__":
    chess_app = ChessApp(4, (4, 4, 4, 4))
    chess_app.run()
