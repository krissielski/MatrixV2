


NUMROWS     = 6
NUMCOLS     = 7


def GameBoard2String(game_board):
    
    # Character mapping for players and empty spaces
    player_chars = {
        0: 'X',      # Player 0 (Red) -> X
        1: 'O',      # Player 1 (Yellow) -> O  
        None: '.'    # Empty position -> dot
    }
    
    # Build the string representation
    result = []
    
    # Add column numbers header
    result.append("  1 2 3 4 5 6 7")
    result.append("  -------------")
    
    # Process rows from top to bottom (row 5 to 0 for visual correctness)
    for row in range(NUMROWS-1, -1, -1):
        row_str = f"{row+1}|"  # Row number (1-6 for human readability)
        
        for col in range(NUMCOLS):
            player = game_board[col][row]
            char = player_chars[player]
            row_str += char + " "
        
        result.append(row_str)
    
    # Add bottom border
    result.append("  -------------")
    result.append("  1 2 3 4 5 6 7")
    
    return "\n".join(result)


def GameBoard2StringSimple(game_board):


    player_chars = {0: 'X', 1: 'O', None: '.'}
    
    result = []
    
    # Process rows from top to bottom
    for row in range(NUMROWS-1, -1, -1):
        row_str = ""
        for col in range(NUMCOLS):
            player = game_board[col][row]
            row_str += player_chars[player]
        result.append(row_str)

    result.append("1234567")
    
    return "\n".join(result)


def GameBoard2StringDetailed(game_board):

    player_chars = {0: 'X', 1: 'O', None: '·'}  # Using middle dot for empty
    
    result = []
    
    # Title and legend
    result.append("    CONNECT 4 BOARD")
    result.append("  X = Red Player (0)")
    result.append("  O = Yellow Player (1)")
    result.append("  · = Empty Position")
    result.append("")
    
    # Column headers
    result.append("    1   2   3   4   5   6   7")
    result.append("  ┌───┬───┬───┬───┬───┬───┬───┐")
    
    # Board rows
    for row in range(NUMROWS-1, -1, -1):
        row_str = f"{row+1} │"
        
        for col in range(NUMCOLS):
            player = game_board[col][row]
            char = player_chars[player]
            row_str += f" {char} │"
        
        result.append(row_str)
        
        # Add separator line (except after last row)
        if row > 0:
            result.append("  ├───┼───┼───┼───┼───┼───┼───┤")
    
    # Bottom border
    result.append("  └───┴───┴───┴───┴───┴───┴───┘")
    result.append("    1   2   3   4   5   6   7")
    
    return "\n".join(result)


# Test function to demonstrate the output
def TestGameBoardString():

    
    # Create a test game board with some moves
    test_board = [[None for _ in range(NUMROWS)] for _ in range(NUMCOLS)]
    
    # Add some test moves
    test_board[0][0] = 1  # O in column 1, bottom
    test_board[0][1] = 1  # O in column 1, second from bottom
    test_board[1][0] = 1  # O in column 2, bottom
    test_board[3][0] = 0  # X in column 4, bottom
    test_board[3][1] = 0  # X in column 4, second from bottom
    test_board[3][2] = 0  # O in column 4, third from bottom
    test_board[6][0] = 1  # O in column 7, bottom
    
    print("=== STANDARD VERSION ===")
    print(GameBoard2String(test_board))
    print()
    
    print("=== SIMPLE VERSION ===")
    print(GameBoard2StringSimple(test_board))
    print()
    
    print("=== DETAILED VERSION ===")
    print(GameBoard2StringDetailed(test_board))



if __name__ == "__main__":
    TestGameBoardString()


