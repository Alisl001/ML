import tkinter as tk
from tkinter import messagebox

class Piece:
    def __init__(self, piece_type, position):
        self.piece_type = piece_type  # 'Gray', 'Red', or 'Purple'
        self.position = position  # (row, column) tuple

    def __repr__(self):
        return f"{self.piece_type[0]}({self.position})"

    def copy(self):
        return Piece(self.piece_type, self.position)

class GameState:
    def __init__(self, board):
        self.board = board

    def display(self):
        self.board.display()

    def is_final_state(self):
        return self.board.is_final_state()

    def make_move(self, piece, new_position):
        new_board = self.board.copy()
        new_board.make_move(piece, new_position)
        return GameState(new_board)

class Board:
    def __init__(self, n, m, pieces, targets):
        self.n = n  # Number of rows
        self.m = m  # Number of columns
        self.grid = [[' ' for _ in range(m)] for _ in range(n)]
        self.pieces = {piece.position: piece for piece in pieces}  # Dict of pieces by their positions
        self.targets = targets  # List of target positions as (row, col) tuples
        self.initial_pieces = pieces  # Save initial pieces for reset
        self.initialize_board()

    def initialize_board(self):
        self.grid = [[' ' for _ in range(self.m)] for _ in range(self.n)]
        self.pieces = {piece.position: piece for piece in self.initial_pieces}  # Reset pieces
        for piece in self.pieces.values():
            row, col = piece.position
            self.grid[row][col] = piece.piece_type[0]
        for row, col in self.targets:
            if self.grid[row][col] == ' ':
                self.grid[row][col] = 'T'

    def display(self):
        for row in self.grid:
            print(" | ".join(row))
            print("-" * (self.m * 4 - 1))

    def can_move_to(self, row, col):
        return 0 <= row < self.n and 0 <= col < self.m and self.grid[row][col] in [' ', 'T']

    def move_red_magnet(self, piece, new_position):
        old_row, old_col = piece.position
        new_row, new_col = new_position
        if not self.can_move_to(new_row, new_col):
            print("Invalid move for Red magnet.")
            return

        self.grid[old_row][old_col] = ' '
        piece.position = new_position
        self.grid[new_row][new_col] = 'R'
        self.pieces[new_position] = piece
        del self.pieces[(old_row, old_col)]
        self._pull_magnets(new_row, new_col)

    def move_purple_magnet(self, piece, new_position):
        old_row, old_col = piece.position
        new_row, new_col = new_position
        if not self.can_move_to(new_row, new_col):
            print("Invalid move for Purple magnet.")
            return

        self.grid[old_row][old_col] = ' '
        piece.position = new_position
        self.grid[new_row][new_col] = 'P'
        self.pieces[new_position] = piece
        del self.pieces[(old_row, old_col)]
        self._push_magnets(new_row, new_col)

    def _shift_piece(self, row, col, row_offset, col_offset):
        new_row, new_col = row + row_offset, col + col_offset
        if self.can_move_to(new_row, new_col):
            self.grid[new_row][new_col] = self.grid[row][col]
            self.pieces[(new_row, new_col)] = self.pieces[(row, col)]
            self.pieces[(new_row, new_col)].position = (new_row, new_col)
            self.grid[row][col] = ' '
            del self.pieces[(row, col)]

    def _pull_magnets(self, row, col):
        for i in range(1, self.m):
            left = (row, col - i)
            if left in self.pieces and col - i + 1 < self.m:
                self._shift_piece(row, col - i, 0, 1)
            right = (row, col + i)
            if right in self.pieces and col + i - 1 >= 0:
                self._shift_piece(row, col + i, 0, -1)
        for i in range(1, self.n):
            up = (row - i, col)
            if up in self.pieces and row - i + 1 < self.n:
                self._shift_piece(row - i, col, 1, 0)
            down = (row + i, col)
            if down in self.pieces and row + i - 1 >= 0:
                self._shift_piece(row + i, col, -1, 0)

    def _push_magnets(self, row, col):
        for i in range(self.m - 1, 0, -1):
            left = (row, col - i)
            if left in self.pieces and col - i - 1 >= 0:
                self._shift_piece(row, col - i, 0, -1)
            right = (row, col + i)
            if right in self.pieces and col + i + 1 < self.m:
                self._shift_piece(row, col + i, 0, 1)
        for i in range(self.n - 1, 0, -1):
            up = (row - i, col)
            if up in self.pieces and row - i - 1 >= 0:
                self._shift_piece(row - i, col, -1, 0)
            down = (row + i, col)
            if down in self.pieces and row + i + 1 < self.n:
                self._shift_piece(row + i, col, 1, 0)

    def is_final_state(self):
        for piece in self.pieces.values():
            if piece.piece_type in ['Red', 'Purple', 'Gray'] and piece.position not in self.targets:
                return False
        return True

    def make_move(self, piece, new_position):
        if piece.piece_type == 'Red':
            self.move_red_magnet(piece, new_position)
        elif piece.piece_type == 'Purple':
            self.move_purple_magnet(piece, new_position)

    def copy(self):
        return Board(self.n, self.m, [piece.copy() for piece in self.pieces.values()], self.targets)

class GameGUI:
    def __init__(self, master, game_state):
        self.master = master
        self.master.title("Logic Magnets")
        self.game_state = game_state
        self.initial_state = GameState(game_state.board.copy())
        self.cell_size = 75
        self.canvas = tk.Canvas(master, width=self.cell_size * self.game_state.board.m, height=self.cell_size * self.game_state.board.n)
        self.canvas.pack()
        self.selected_piece = None
        self.draw_board()
        self.canvas.bind("<Button-1>", self.on_click)

        # Add Reset Button
        self.reset_button = tk.Button(master, text="Reset", command=self.reset_board)
        self.reset_button.pack()

    def draw_board(self):
        self.canvas.delete("all")
        for row in range(self.game_state.board.n):
            for col in range(self.game_state.board.m):
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = "white"
                if (row, col) in self.game_state.board.targets:
                    color = "lightGreen"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
                if (row, col) in self.game_state.board.pieces:
                    piece = self.game_state.board.pieces[(row, col)]
                    piece_color = "gray" if piece.piece_type == 'Gray' else "red" if piece.piece_type == 'Red' else "purple"
                    self.canvas.create_oval(x1 + 5, y1 + 5, x2 - 5, y2 - 5, fill=piece_color)

    def on_click(self, event):
        row, col = event.y // self.cell_size, event.x // self.cell_size
        if self.selected_piece:
            piece = self.game_state.board.pieces.get(self.selected_piece)
            if piece:
                self.game_state = self.game_state.make_move(piece, (row, col))
                self.selected_piece = None
                if self.game_state.is_final_state():
                    self.draw_board()
                    self.show_win_message()
            self.draw_board()
        elif (row, col) in self.game_state.board.pieces:
            self.selected_piece = (row, col)

    def show_win_message(self):
        messagebox.showinfo("Congratulations!", "You've won the game!")

    def reset_board(self):
        self.game_state = GameState(self.initial_state.board.copy())
        self.draw_board()


root = tk.Tk() 
initial_pieces = [
    Piece('Gray', (0, 1)), 
    Piece('Gray', (1, 1)), 
    Piece('Gray', (1, 2)), 
    Piece('Red', (2, 3)), 
    Piece('Purple', (2, 0))
    ] 
targets = [(0, 2), (1, 0), (1, 1), (2, 0), (2, 1)] 
board = Board(3, 4, initial_pieces, targets) 
game_state = GameState(board) 
game_gui = GameGUI(root, game_state) 
root.mainloop()
