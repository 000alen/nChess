from kivy.uix.gridlayout import GridLayout

from nChess.nBoard import nBoard, IntegerVector
from nChess.Piece import Move
from nChess.GUI.BoardWidget import BoardWidget
from nChess.GUI.PieceWidget import PieceWidget
from nChess.utils import to_PNG


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
            self.set_piece_widget(PieceWidget(source=to_PNG(piece)), piece.position)

    def has_piece_widget(self, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            return self.boards_widgets[0].has_piece_widget(*position)
        elif self.n_board_dimension == 3:
            return self.boards_widgets[position[2]].has_piece_widget(*position[:2])
        elif self.n_board_dimension == 4:
            return self.boards_widgets[position[2]][position[3]].has_piece_widget(*position[:2])
        else:
            raise Exception

    def set_piece_widget(self, piece, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            self.boards_widgets[0].set_piece_widget(piece, *position)
        elif self.n_board_dimension == 3:
            self.boards_widgets[position[2]].set_piece_widget(piece, *position[:2])
        elif self.n_board_dimension == 4:
            self.boards_widgets[position[2]][position[3]].set_piece_widget(piece, *position[:2])
        else:
            raise Exception

    def get_piece_widget(self, position: tuple[int, ...]):
        if self.n_board_dimension == 2:
            return self.boards_widgets[0].get_piece_widget(*position)
        elif self.n_board_dimension == 3:
            return self.boards_widgets[position[2]].get_piece_widget(*position[:2])
        elif self.n_board_dimension == 4:
            return self.boards_widgets[position[2]][position[3]].get_piece_widget(*position[:2])
        else:
            raise Exception

    def remove_piece_widget(self, position: tuple[int, ...], visually=False):
        if not visually:
            self.n_board.remove(position)

        if self.n_board_dimension == 2:
            self.boards_widgets[0].remove_piece_widget(*position)
        elif self.n_board_dimension == 3:
            self.boards_widgets[position[2]].remove_piece_widget(*position[:2])
        elif self.n_board_dimension == 4:
            self.boards_widgets[position[2]][position[3]].remove_piece_widget(*position[:2])
        else:
            raise Exception

    def move_piece(self, move):
        self.n_board.move(move)
        source = self.get_piece_widget(move.initial_position).source
        self.remove_piece_widget(move.initial_position)
        
        if self.has_piece_widget(move.final_position):
            self.remove_piece_widget(move.initial_position, visually=True)

        self.set_piece_widget(PieceWidget(source=source), move.final_position)

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
        assert self.has_piece_widget(position)

        self.toggle_highlight(position)
        for move in self.n_board.get(position).moves():
            self.toggle_highlight(move.final_position)

    def unselect_piece(self, position):
        assert self.has_piece_widget(position)

        self.toggle_highlight(position)
        for move in self.n_board.get(position).moves():
            self.toggle_highlight(move.final_position)

    def handle_touch(self, board, i, j):
        position = self.reconstruct_position(board, i, j)

        if self.selected_position is not None:
            if position == self.selected_position:
                self.unselect_piece(self.selected_position)
                self.selected_position = None
            elif (move := Move(self.selected_position, position)) in self.n_board.get(self.selected_position).moves():
                self.unselect_piece(self.selected_position)
                self.selected_position = None
                self.move_piece(move)
                self.n_board.move(move, force=True)
            elif self.has_piece_widget(position):
                self.unselect_piece(self.selected_position)
                self.select_piece(position)
                self.selected_position = position
            else:
                self.unselect_piece(self.selected_position)
                self.selected_position = None
        else:
            if self.has_piece_widget(position):
                self.select_piece(position)
                self.selected_position = position
