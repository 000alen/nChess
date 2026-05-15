from nChess.GUI.CellWidget import CellWidget
from kivy.uix.gridlayout import GridLayout

from nChess.nBoard import nBoard, IntegerVector
from nChess.Piece import Move
from nChess.GUI.BoardWidget import BoardWidget
from nChess.GUI.PieceWidget import PieceWidget
from nChess.GUI.geometry import (
    board_coordinates_for_indices,
    board_grid_size,
    board_indices_for_position,
    layer_dimensions,
    position_padding as pad_position,
)
from nChess.utils import to_PNG


class nBoardWidget(GridLayout):
    n_board: nBoard
    boards_widgets: list[BoardWidget]
    selected_position: IntegerVector | None

    def __init__(self, n_board: nBoard, **kwargs):
        super().__init__(**kwargs)
        self.spacing = [10, 10]
        self.padding = [10, 10]

        assert 2 <= n_board.dimension <= 4

        self.n_board = n_board

        boards_widgets_size = board_grid_size(self.n_board.dimension, self.n_board.size)
        board_rows, board_columns = layer_dimensions(self.n_board.size)

        self.rows = boards_widgets_size[0]

        self.boards_widgets = []
        self.board_widget_positions = {}
        for i in range(boards_widgets_size[0]):
            self.boards_widgets.append([])
            for j in range(boards_widgets_size[1]):
                board_widget = BoardWidget(board_rows=board_rows, board_columns=board_columns, is_n_board=True)
                self.boards_widgets[i].append(board_widget)
                self.board_widget_positions[board_widget] = board_coordinates_for_indices(
                    i,
                    j,
                    self.n_board.dimension,
                    boards_widgets_size[0],
                )
                self.add_widget(board_widget)

        self.selected_position = None
        self.selected_moves = set()
        self.highlighted_positions = set()

        self.sync_pieces_from_model()

    def position_padding(self, position: IntegerVector) -> IntegerVector:
        return pad_position(position)

    def get_board_widget(self, position: IntegerVector) -> BoardWidget:
        row, column = board_indices_for_position(
            position,
            self.n_board.dimension,
            len(self.boards_widgets),
        )
        return self.boards_widgets[row][column]

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
        return self.get_board_widget(position).remove_piece_widget(position[:2])

    def apply_model_move(self, move: Move):
        piece_widget = self.remove_piece_widget(move.initial_position)

        if self.has_piece_widget(move.final_position):
            self.remove_piece_widget(move.final_position)

        if piece_widget is None:
            piece_widget = PieceWidget()
        piece_widget.source = to_PNG(self.n_board.get(move.final_position))
        self.set_piece_widget(piece_widget, move.final_position)

    def sync_pieces_from_model(self):
        for board_widget in self.iter_board_widgets():
            for row in board_widget.cells_widgets:
                for cell in row:
                    cell.remove_piece_widget()
        for piece in self.n_board.pieces:
            self.set_piece_widget(PieceWidget(source=to_PNG(piece)), piece.position)

    def iter_board_widgets(self):
        for row in self.boards_widgets:
            for board_widget in row:
                yield board_widget

    def get_cell(self, position: IntegerVector) -> CellWidget:
        position = self.position_padding(position)
        return self.get_board_widget(position).get_cell_widget(position[:2])

    def find_board_widget(self, board_widget: BoardWidget) -> IntegerVector:
        try:
            return self.board_widget_positions[board_widget]
        except KeyError as exc:
            raise ValueError("board widget does not belong to this n-board") from exc

    def set_cell_widget_highlight(self, position: tuple[int, ...], highlighted: bool):
        position = self.position_padding(position)
        self.get_board_widget(position).set_cell_widget_highlight(position[:2], highlighted)

    def reconstruct_position(self, board_widget: BoardWidget, in_board_widget_position: IntegerVector) -> IntegerVector:
        if self.n_board.dimension == 2:
            return in_board_widget_position
        elif self.n_board.dimension == 3:
            k, _ = self.find_board_widget(board_widget)
            return (*in_board_widget_position, k)
        elif self.n_board.dimension == 4:
            k, h = self.find_board_widget(board_widget)
            return (*in_board_widget_position, k, h)

    def select_piece(self, position: IntegerVector):
        assert self.has_piece_widget(position)

        self.clear_selection()
        self.selected_position = position
        self.selected_moves = set(self.n_board.get(position).moves())
        self.highlighted_positions = {position, *(move.final_position for move in self.selected_moves)}
        for highlighted_position in self.highlighted_positions:
            self.set_cell_widget_highlight(highlighted_position, True)

    def clear_selection(self):
        for position in self.highlighted_positions:
            self.set_cell_widget_highlight(position, False)
        self.highlighted_positions = set()
        self.selected_moves = set()
        self.selected_position = None

    def handle_touch(self, board_widget: BoardWidget, in_board_widget_position):
        position = self.reconstruct_position(board_widget, in_board_widget_position)

        if self.selected_position is not None:
            if position == self.selected_position:
                self.clear_selection()
            elif (move := Move(self.selected_position, position)) in self.selected_moves:
                self.clear_selection()
                self.n_board.move(move, force=self.n_board.current_turn() is None)
                self.apply_model_move(move)
            elif self.has_piece_widget(position) and self.can_select_piece(position):
                self.select_piece(position)
            else:
                self.clear_selection()
        else:
            if self.has_piece_widget(position) and self.can_select_piece(position):
                self.select_piece(position)

    def can_select_piece(self, position: IntegerVector) -> bool:
        current_turn = self.n_board.current_turn()
        return current_turn is None or self.n_board.get(position).color == current_turn
