from kivy.uix.gridlayout import GridLayout

from nChess.GUI.CellWidget import CellWidget, BLACK, WHITE


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

    def has_piece_widget(self, i, j):
        return self.cells_widgets[i][j].has_piece_widget()

    def set_piece_widget(self, piece, i, j):
        self.cells_widgets[i][j].set_piece_widget(piece)

    def get_piece_widget(self, i, j):
        return self.cells_widgets[i][j].get_piece_widget()

    def remove_piece_widget(self, i, j):
        self.cells_widgets[i][j].remove_piece_widget()

    def move_piece(self, i_1, j_1, i_2, j_2):
        piece = self.get_piece_widget(i_1, j_1)
        self.remove_piece_widget(i_1, j_1)
        self.set_piece_widget(piece, i_2, j_2)

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
