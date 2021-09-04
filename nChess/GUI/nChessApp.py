from kivy.app import App

from nChess.nBoard import nBoard, IntegerVector
from nChess.GUI.nBoardWidget import nBoardWidget


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
