from nChess.GUI.CellWidget import CellWidget
from kivy.uix.gridlayout import GridLayout

from nChess.nBoard import nBoard, IntegerVector
from nChess.Piece import Move
from nChess.GUI.BoardWidget import BoardWidget
from nChess.GUI.PieceWidget import PieceWidget
from nChess.utils import to_PNG


class nBoardWidget(GridLayout): 
    n_board: nBoard
    boards_widgets: list[BoardWidget]
    selected_position: IntegerVector

    def __init__(self, n_board: nBoard, **kwargs):
        super().__init__(**kwargs)
        self.spacing = [10, 10]
        self.padding = [10, 10]

        assert 2 <= n_board.dimension <= 4
        
        self.n_board = n_board

        if self.n_board.dimension == 2:
            boards_widgets_size = (1, 1)
        elif self.n_board.dimension == 3:
            boards_widgets_size = (1, self.n_board.size[2])
        else:
            boards_widgets_size = (self.n_board.size[2], self.n_board.size[3])

        self.rows = boards_widgets_size[0]

        self.boards_widgets = []
        for i in range(boards_widgets_size[0]):
            self.boards_widgets.append([])
            for j in range(boards_widgets_size[1]):
                board_widget = BoardWidget(board_rows=self.n_board.size[0], board_columns=self.n_board.size[0], is_n_board=True)
                self.boards_widgets[i].append(board_widget)
                self.add_widget(board_widget)

        self.selected_position = None

        for piece in self.n_board.pieces:
            self.set_piece_widget(PieceWidget(source=to_PNG(piece)), piece.position)

    def position_padding(self, position: IntegerVector) -> IntegerVector:
        if len(position) < 4:
            return (*position, *((0,) * (4 - len(position))))
        return position

    def get_board_widget(self, position: IntegerVector) -> BoardWidget:
        return self.boards_widgets[len(self.boards_widgets) - position[2] - 1][position[3]]

    def has_piece_widget(self, position: tuple[int, ...]) -> bool:
        position = self.position_padding(position)
        return self.get_board_widget(position).has_piece_widget(position[:2])

    def set_piece_widget(self, piece_widget: PieceWidget, position: tuple[int, ...]):
        position = self.position_padding(position)
        self.get_board_widget(position).set_piece_widget(piece_widget, position[:2])

    def get_piece_widget(self, position: tuple[int, ...]) -> PieceWidget:
        position = self.position_padding(position)
        return self.get_board_widget(position).get_piece_widget(position[:2])

    def remove_piece_widget(self, position: tuple[int, ...]):
        position = self.position_padding(position)
        self.get_board_widget(position).remove_piece_widget(position[:2])

    def move_piece_widget(self, move: Move):
        source = self.get_piece_widget(move.initial_position).source
        self.remove_piece_widget(move.initial_position)
        
        if self.has_piece_widget(move.final_position):
            self.remove_piece_widget(move.final_position)

        self.set_piece_widget(PieceWidget(source=source), move.final_position)

    def get_cell(self, position: IntegerVector) -> CellWidget:
        position = self.position_padding(position)
        return self.get_board_widget(position).get_cell_widget(position[:2])

    def find_board_widget(self, board_widget: BoardWidget) -> IntegerVector:
        n_board_size = self.position_padding(self.n_board.size)
        for i in range(n_board_size[2]):
            for j in range(n_board_size[3]):
                if self.boards_widgets[i][j] == board_widget:
                    return len(self.boards_widgets) - i - 1, j

    def toggle_cell_widget_highlight(self, position: tuple[int, ...]):
        position = self.position_padding(position)
        self.get_board_widget(position).toggle_cell_widget_highlight(position[:2])

    def reconstruct_position(self, board_widget: BoardWidget, in_board_widget_position: IntegerVector) -> IntegerVector:
        if self.n_board.dimension == 2:
            return in_board_widget_position
        elif self.n_board.dimension == 3:
            k = self.find_board_widget(board_widget)
            return (*in_board_widget_position, k)
        elif self.n_board.dimension == 4:
            k, h = self.find_board_widget(board_widget)
            return (*in_board_widget_position, k, h)

    def select_piece(self, position: IntegerVector):
        assert self.has_piece_widget(position)

        self.toggle_cell_widget_highlight(position)
        for move in self.n_board.get(position).moves():
            self.toggle_cell_widget_highlight(move.final_position)

    def unselect_piece(self, position: IntegerVector):
        assert self.has_piece_widget(position)

        self.toggle_cell_widget_highlight(position)
        for move in self.n_board.get(position).moves():
            self.toggle_cell_widget_highlight(move.final_position)

    def handle_touch(self, board_widget: BoardWidget, in_board_widget_position):
        position = self.reconstruct_position(board_widget, in_board_widget_position)

        if self.selected_position is not None:
            if position == self.selected_position:
                self.unselect_piece(self.selected_position)
                self.selected_position = None
            elif (move := Move(self.selected_position, position)) in self.n_board.get(self.selected_position).moves():
                self.unselect_piece(self.selected_position)
                self.selected_position = None
                self.move_piece_widget(move)
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
