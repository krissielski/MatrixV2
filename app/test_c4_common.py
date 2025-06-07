import unittest
from c4_common import GetFirstOpenRow, CheckForDraw, CheckForWinner, CheckForValidMove, NUMROWS, NUMCOLS

class TestC4Common(unittest.TestCase):

    def setUp(self):
        # Create an empty board for each test
        self.board = [[None for _ in range(NUMROWS)] for _ in range(NUMCOLS)]

    def test_get_first_open_row_empty(self):
        row = GetFirstOpenRow(self.board, 3)
        self.assertEqual(row, 0)

    def test_get_first_open_row_partial_column(self):
        self.board[2][0] = 0
        self.board[2][1] = 1
        row = GetFirstOpenRow(self.board, 2)
        self.assertEqual(row, 2)

    def test_get_first_open_row_full_column(self):
        for r in range(NUMROWS):
            self.board[1][r] = 0
        row = GetFirstOpenRow(self.board, 1)
        self.assertIsNone(row)

    def test_check_for_draw_false(self):
        self.assertFalse(CheckForDraw(self.board))

    def test_check_for_draw_true(self):
        for c in range(NUMCOLS):
            for r in range(NUMROWS):
                self.board[c][r] = 0
        self.assertTrue(CheckForDraw(self.board))

    def test_check_for_valid_move_true(self):
        self.assertTrue(CheckForValidMove(self.board, 3, 2))

    def test_check_for_valid_move_false(self):
        self.board[3][2] = 1
        self.assertFalse(CheckForValidMove(self.board, 3, 2))

    def test_check_for_winner_horizontal(self):
        for c in range(4):
            self.board[c][0] = 1
        winner = CheckForWinner(self.board, 2, 0, 1)
        self.assertIsNotNone(winner)
        self.assertEqual(len(winner), 4)

    def test_check_for_winner_vertical(self):
        for r in range(4):
            self.board[3][r] = 0
        winner = CheckForWinner(self.board, 3, 2, 0)
        self.assertIsNotNone(winner)
        self.assertEqual(len(winner), 4)

    def test_check_for_winner_diagonal(self):
        self.board[0][0] = 1
        self.board[1][1] = 1
        self.board[2][2] = 1
        self.board[3][3] = 1
        winner = CheckForWinner(self.board, 3, 3, 1)
        self.assertIsNotNone(winner)
        self.assertEqual(len(winner), 4)

    def test_check_for_winner_antidiagonal(self):
        self.board[3][0] = 0
        self.board[2][1] = 0
        self.board[1][2] = 0
        self.board[0][3] = 0
        winner = CheckForWinner(self.board, 1, 2, 0)
        self.assertIsNotNone(winner)
        self.assertEqual(len(winner), 4)

    def test_check_for_winner_none(self):
        self.board[0][0] = 1
        self.board[1][0] = 0
        self.board[2][0] = 1
        self.board[3][0] = 0
        winner = CheckForWinner(self.board, 0, 0, 1)
        self.assertIsNone(winner)

if __name__ == '__main__':
    unittest.main()
