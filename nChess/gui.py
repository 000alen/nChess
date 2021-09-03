from nChess.Piece import Move
from nChess.Piece.King import King
from nChess.Piece.Queen import Queen
from nChess.Piece.Rook import Rook
from nChess.nBoard.Classic import ClassicColor
from nChess.Piece.Pawn import Pawn
from nChess.utils import to_PNG
from nChess.nBoard import IntegerVector, nBoard, Color

from kivy.core.window import Window
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle

Window.size = (600, 600)

WHITE = (0.9, 0.9, 0.9, 1)
BLACK = (0.3, 0.3, 0.3, 1)
HIGHLIGHT = (0.9, 0.9, 0, 1)


class PieceWidget(Image):
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.handle_touch(self)
        else:
            return super().on_touch_up(touch)


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

    def has_piece(self):
        return self.piece_widget is not None

    def set_piece(self, piece):
        self.piece_widget = piece
        self.add_widget(self.piece_widget, index=0)

    def get_piece(self):
        return self.piece_widget

    def remove_piece(self):
        self.remove_widget(self.piece_widget)
        self.piece_widget = None

    def handle_touch(self, piece_instance):
        self.parent.handle_touch(self)


class BoardWidget(GridLayout):
    board_rows: int
    board_columns: int
    is_n_board: bool
    cells_widgets: list[CellWidget]

    def __init__(self, board_rows: int, board_columns: int, is_n_board=False, **kwargs):
        super().__init__(**kwargs)

        self.rows = board_rows

        self.board_rows = board_rows
        self.board_columns = board_columns
        self.is_n_board = is_n_board

        self.cells_widgets = []
        for i in range(self.board_rows):
            self.cells_widgets.append([])
            for j in range(self.board_columns):
                cell = CellWidget(BLACK if (i + j) % 2 == 0 else WHITE)
                self.cells_widgets[i].append(cell)
                self.add_widget(cell, index=100)

    def has_piece(self, i, j):
        return self.cells_widgets[i][j].has_piece()

    def set_piece(self, piece, i, j):
        self.cells_widgets[i][j].set_piece(piece)

    def get_piece(self, i, j):
        return self.cells_widgets[i][j].get_piece()

    def remove_piece(self, i, j):
        self.cells_widgets[i][j].remove_piece()

    def move_piece(self, i_1, j_1, i_2, j_2):
        piece = self.get_piece(i_1, j_1)
        self.remove_piece(i_1, j_1)
        self.set_piece(piece, i_2, j_2)

    def select_piece(self, i, j):
        pass

    def unselect_piece(self, i, j):
        pass

    def get_cell(self, i, j):
        return self.cells_widgets[i][j]

    def find_cell(self, cell):
        for i in range(self.board_rows):
            for j in range(self.board_columns):
                if self.cells_widgets[i][j] == cell:
                    return i, j

    def toggle_highlight(self, i, j):
        self.cells_widgets[i][j].toggle_highlight()

    def handle_touch(self, cell_instance):
        if self.is_n_board:
            i, j = self.find_cell(cell_instance)
            self.parent.handle_touch(self, i, j)


class nBoardWidget(GridLayout): 
    n_board_dimension: int
    n_board_size: IntegerVector
    boards_widgets: list[BoardWidget]
    selected_position: IntegerVector

    def __init__(self, n_board: nBoard = None, n_board_dimension: int = None, n_board_size: int = None, **kwargs):
        super().__init__(**kwargs)

        self.spacing = [10, 10]
        self.padding = [10, 10]

        self.selected_position = None

        if n_board is None:
            assert n_board_dimension is not None and n_board_size is not None
            self.n_board = nBoard(n_board_dimension, n_board_size)
            self.n_board_dimension = n_board_dimension
            self.n_board_size = n_board_size
        else:
            self.n_board = n_board
            self.n_board_dimension = n_board.dimension
            self.n_board_size = n_board.size

        self.position_a = None

        self.boards_widgets = []
        if self.n_board_dimension == 2:
            self.rows = 1
            board = BoardWidget(*self.n_board_size, is_n_board=True)
            self.boards_widgets.append(board)
            self.add_widget(board)
            self.load_pieces_from_n_board()
        elif self.n_board_dimension == 3:
            self.rows = 1
            for i in range(n_board_size[2]):
                board = BoardWidget(*self.n_board_size[:2], is_n_board=True)
                self.boards_widgets.append(board)
                self.add_widget(board)
            self.load_pieces_from_n_board()
        elif self.n_board_dimension == 4:
            self.rows = self.n_board_size[2]
            for i in range(self.n_board_size[2]):
                self.boards_widgets.append([])
                for j in range(self.n_board_size[3]):
                    board = BoardWidget(*self.n_board_size[:2], is_n_board=True)
                    self.boards_widgets[i].append(board)
                    self.add_widget(board)
            self.load_pieces_from_n_board()
        else:
            raise Exception

    def load_pieces_from_n_board(self):
        for piece in self.n_board.pieces:
            self.set_piece(PieceWidget(source=to_PNG(piece)), piece.position)

    def has_piece(self, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            return self.boards_widgets[0].has_piece(*position)
        elif self.n_board_dimension == 3:
            return self.boards_widgets[position[2]].has_piece(*position[:2])
        elif self.n_board_dimension == 4:
            return self.boards_widgets[position[2]][position[3]].has_piece(*position[:2])
        else:
            raise Exception

    def set_piece(self, piece, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            self.boards_widgets[0].set_piece(piece, *position)
        elif self.n_board_dimension == 3:
            self.boards_widgets[position[2]].set_piece(piece, *position[:2])
        elif self.n_board_dimension == 4:
            self.boards_widgets[position[2]][position[3]].set_piece(piece, *position[:2])
        else:
            raise Exception

    def get_piece(self, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            return self.boards_widgets[0].get_piece(*position)
        elif self.n_board_dimension == 3:
            return self.boards_widgets[position[2]].get_piece(*position[:2])
        elif self.n_board_dimension == 4:
            return self.boards_widgets[position[2]][position[3]].get_piece(*position[:2])
        else:
            raise Exception

    def remove_piece(self, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            self.boards_widgets[0].remove_piece(*position)
        elif self.n_board_dimension == 3:
            self.boards_widgets[position[2]].remove_piece(*position[:2])
        elif self.n_board_dimension == 4:
            self.boards_widgets[position[2]][position[3]].remove_piece(*position[:2])
        else:
            raise Exception

    def move_piece(self, initial_position, final_position):
        source = self.get_piece(initial_position).source
        self.remove_piece(initial_position)
        self.set_piece(PieceWidget(source=source), final_position)

    def get_cell(self, position):
        if self.n_board_dimension == 2:
            return self.boards_widgets[0].get_cell(*position)
        elif self.n_board_dimension == 3:
            return self.boards_widgets[position[2]].get_cell(*position[:2])
        elif self.n_board_dimension == 4:
            return self.boards_widgets[position[2]][position[3]].get_cell(*position[:2])
        else:
            raise Exception

    def find_board(self, board):
        if self.n_board_dimension == 2:
            return 0
        elif self.n_board_dimension == 3:
            for i in range(self.n_board_size[2]):
                if self.boards_widgets[i] == board:
                    return i
        elif self.n_board_dimension == 4:
            for i in range(self.n_board_size[2]):
                for j in range(self.n_board_size[3]):
                    if self.boards_widgets[i][j] == board:
                        return i, j
        else:
            raise Exception

    def toggle_highlight(self, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            self.boards_widgets[0].toggle_highlight(*position)
        elif self.n_board_dimension == 3:
            self.boards_widgets[position[2]].toggle_highlight(*position[:2])
        elif self.n_board_dimension == 4:
            self.boards_widgets[position[2]][position[3]].toggle_highlight(*position[:2])
        else:
            raise Exception

    def reconstruct_position(self, board, i, j):
        if self.n_board_dimension == 2:
            return (i, j)            
        elif self.n_board_dimension == 3:
            k = self.find_board(board)
            return (i, j, k)
        elif self.n_board_dimension == 4:
            k, h = self.find_board(board)
            return (i, j, k, h)
        else:
            raise Exception

    def select_piece(self, position):
        assert self.has_piece(position)

        self.toggle_highlight(position)
        for move in self.n_board.get(position).moves():
            self.toggle_highlight(move.final_position)

    def unselect_piece(self, position):
        assert self.has_piece(position)

        self.toggle_highlight(position)
        for move in self.n_board.get(position).moves():
            self.toggle_highlight(move.final_position)

    def handle_touch(self, board, i, j):
        position = self.reconstruct_position(board, i, j)

        # raise NotImplementedError

        if self.selected_position is not None:
            if position == self.selected_position:
                self.unselect_piece(self.selected_position)
                self.selected_position = None
            elif (move := Move(self.selected_position, position)) in self.n_board.get(self.selected_position).moves():
                self.unselect_piece(self.selected_position)
                self.selected_position = None
                self.move_piece(move.initial_position, move.final_position)
                self.n_board.move(move, force=True)
            elif self.has_piece(position):
                self.unselect_piece(self.selected_position)
                self.select_piece(position)
                self.selected_position = position
            else:
                self.unselect_piece(self.selected_position)
                self.selected_position = None
        else:
            if self.has_piece(position):
                self.select_piece(position)
                self.selected_position = position


class nChessApp(App):
    n_board_dimension: int
    n_board_size: IntegerVector
    n_board: nBoard
    n_board_widget: nBoardWidget

    def __init__(self, n_board: nBoard = None, n_board_dimension: int = None, n_board_size: int = None, **kwargs):
        super().__init__(**kwargs)

        if n_board is None:
            assert n_board_dimension is not None and n_board_size is not None
            self.n_board = nBoard(n_board_dimension, n_board_size)
        else:
            self.n_board = n_board

        self.n_board_widget = nBoardWidget(n_board=n_board)
        self.n_board_dimension = n_board.dimension
        self.n_board_size = n_board.size

    def build(self):
        return self.n_board_widget


if __name__ == "__main__":
    n_board = nBoard(4, (4, 4, 4, 4))    
    n_board.add(Pawn, (0, 1, 0, 0), ClassicColor.white)
    n_board.add(Pawn, (1, 1, 0, 0), ClassicColor.white)
    n_board.add(Pawn, (2, 1, 0, 0), ClassicColor.white)
    n_board.add(Pawn, (3, 1, 0, 0), ClassicColor.white)
    n_board.add(Rook, (0, 0, 0, 0), ClassicColor.white)
    n_board.add(Queen, (1, 0, 0, 0), ClassicColor.white)
    n_board.add(King, (2, 0, 0, 0), ClassicColor.white)
    n_board.add(Rook, (3, 0, 0, 0), ClassicColor.white)
    n_board.add(Pawn, (0, 2, 0, 0), ClassicColor.black)
    n_board.add(Pawn, (1, 2, 0, 0), ClassicColor.black)
    n_board.add(Pawn, (2, 2, 0, 0), ClassicColor.black)
    n_board.add(Pawn, (3, 2, 0, 0), ClassicColor.black)
    n_board.add(Rook, (0, 3, 0, 0), ClassicColor.black)
    n_board.add(King, (1, 3, 0, 0), ClassicColor.black)
    n_board.add(Queen, (2, 3, 0, 0), ClassicColor.black)
    n_board.add(Rook, (3, 3, 0, 0), ClassicColor.black)

    n_chess_app = nChessApp(n_board=n_board)
    n_chess_app.run()

    import time
    time.sleep(5)

    n_chess_app.n_board_widget.export_as_image().save("out.png")
