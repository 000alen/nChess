from kivy.app import App

from nChess.nBoard import nBoard
from nChess.GUI.nBoardWidget import nBoardWidget


class nChessApp(App):
    n_board: nBoard
    n_board_widget: nBoardWidget

    def __init__(self, n_board: nBoard, **kwargs):
        super().__init__(**kwargs)

        self.n_board = n_board
        self.n_board_widget = nBoardWidget(n_board)

    def build(self):
        return self.n_board_widget
