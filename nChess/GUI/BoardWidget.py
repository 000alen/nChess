from nChess.nBoard.Board import Board
from nChess.nBoard import IntegerVector
from nChess.GUI.PieceWidget import PieceWidget
from kivy.uix.gridlayout import GridLayout

from nChess.GUI.CellWidget import CellWidget, BLACK, WHITE


class BoardWidget(GridLayout):
    board: Board
    board_rows: int
    board_columns: int
    is_n_board: bool
    cells_widgets: list[CellWidget]

    def __init__(self, board: Board = None, board_rows: int = None, board_columns: int = None, is_n_board=False, **kwargs):
        super().__init__(**kwargs)

        assert board is not None or (board_rows is not None and board_columns is not None)

        if board is None:
            self.board_rows = board_rows
            self.board_columns = board_columns
        else:
            self.board = board
            self.board_rows = self.board.size[0]
            self.board_columns = self.board_size[1]

        self.rows = self.board_rows

        self.is_n_board = is_n_board

        self.cells_widgets = []
        for i in range(self.board_rows):
            self.cells_widgets.append([])
            for j in range(self.board_columns):
                cell = CellWidget(BLACK if (i + j) % 2 == 0 else WHITE)
                self.cells_widgets[i].append(cell)
                self.add_widget(cell, index=100)

    def has_piece_widget(self, position: IntegerVector) -> bool:
        return self.get_cell_widget(position).has_piece_widget()

    def set_piece_widget(self, piece_widget: PieceWidget, position: IntegerVector):
        self.get_cell_widget(position).set_piece_widget(piece_widget)

    def get_piece_widget(self, position: IntegerVector) -> PieceWidget:
        return self.get_cell_widget(position).get_piece_widget()

    def remove_piece_widget(self, position: IntegerVector):
        self.get_cell_widget(position).remove_piece_widget()

    def move_piece_widget(self, initial_position: IntegerVector, final_position: IntegerVector):
        piece = self.get_piece_widget(initial_position)
        if self.has_piece_widget(final_position):
            self.remove_piece_widget(final_position)
        self.set_piece_widget(piece, final_position)

    def select_piece(self, position: IntegerVector):
        assert self.board is not None
        assert self.has_piece_widget(position)

        self.toggle_cell_widget_highlight(position)
        for move in self.board.get(position).moves():
            self.toggle_cell_widget_highlight(move.final_position)

    def unselect_piece(self, position: IntegerVector):
        assert self.board is not None
        assert self.has_piece_widget(position)

        self.toggle_cell_widget_highlight(position)
        for move in self.board.get(position).moves():
            self.toggle_cell_widget_highlight(move.final_position)

    def get_cell_widget(self, position: IntegerVector) -> CellWidget:
        # return self.cells_widgets[position[0]][position[1]]
        # return self.cells_widgets[len(self.cells_widgets) - position[0] - 1][len(self.cells_widgets[0]) - position[1] - 1]
        # return self.cells_widgets[len(self.cells_widgets[0]) - position[1] - 1][len(self.cells_widgets) - position[0] - 1]
        return self.cells_widgets[position[1]][position[0]]

    def find_cell_widget(self, cell_widget) -> IntegerVector:
        for i in range(self.board_rows):
            for j in range(self.board_columns):
                if self.cells_widgets[i][j] == cell_widget:
                    return (j, i)

    def toggle_cell_widget_highlight(self, position: IntegerVector):
        self.get_cell_widget(position).toggle_highlight()

    def handle_touch(self, cell_widget):
        if self.is_n_board:
            position = self.find_cell_widget(cell_widget)
            self.parent.handle_touch(self, position)
