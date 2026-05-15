from nChess.nBoard import IntegerVector
from nChess.GUI.PieceWidget import PieceWidget
from kivy.uix.gridlayout import GridLayout

from nChess.GUI.CellWidget import CellWidget, BLACK, WHITE
from nChess.GUI.geometry import cell_indices_for_position, layer_dimensions, position_for_cell_indices


class BoardWidget(GridLayout):
    board_rows: int
    board_columns: int
    is_n_board: bool
    cells_widgets: list[CellWidget]

    def __init__(self, board=None, board_rows: int = None, board_columns: int = None, is_n_board=False, **kwargs):
        super().__init__(**kwargs)

        assert board is not None or (board_rows is not None and board_columns is not None)

        if board is None:
            self.board_rows = board_rows
            self.board_columns = board_columns
        else:
            self.board_rows, self.board_columns = layer_dimensions(board.size)

        self.rows = self.board_rows

        self.is_n_board = is_n_board

        self.cells_widgets = []
        self.cell_positions = {}
        for i in range(self.board_rows):
            self.cells_widgets.append([])
            for j in range(self.board_columns):
                cell = CellWidget(BLACK if (i + j) % 2 == 0 else WHITE)
                self.cells_widgets[i].append(cell)
                self.cell_positions[cell] = position_for_cell_indices(i, j)
                self.add_widget(cell)

    def has_piece_widget(self, position: IntegerVector) -> bool:
        return self.get_cell_widget(position).has_piece_widget()

    def set_piece_widget(self, piece_widget: PieceWidget, position: IntegerVector):
        self.get_cell_widget(position).set_piece_widget(piece_widget)

    def get_piece_widget(self, position: IntegerVector) -> PieceWidget:
        return self.get_cell_widget(position).get_piece_widget()

    def remove_piece_widget(self, position: IntegerVector):
        return self.get_cell_widget(position).remove_piece_widget()

    def move_piece_widget(self, initial_position: IntegerVector, final_position: IntegerVector):
        piece = self.get_piece_widget(initial_position)
        self.remove_piece_widget(initial_position)
        if self.has_piece_widget(final_position):
            self.remove_piece_widget(final_position)
        self.set_piece_widget(piece, final_position)

    def get_cell_widget(self, position: IntegerVector) -> CellWidget:
        row, column = cell_indices_for_position(position)
        return self.cells_widgets[row][column]

    def find_cell_widget(self, cell_widget) -> IntegerVector:
        try:
            return self.cell_positions[cell_widget]
        except KeyError as exc:
            raise ValueError("cell widget does not belong to this board") from exc

    def toggle_cell_widget_highlight(self, position: IntegerVector):
        self.get_cell_widget(position).toggle_highlight()

    def set_cell_widget_highlight(self, position: IntegerVector, highlighted: bool):
        self.get_cell_widget(position).set_highlighted(highlighted)

    def handle_touch(self, cell_widget):
        if self.is_n_board:
            position = self.find_cell_widget(cell_widget)
            self.parent.handle_touch(self, position)
