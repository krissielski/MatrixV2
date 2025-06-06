def GameBoard2AI(game_board):

    # Character mapping for players and empty spaces
    player_chars = {
        0: 'X',      # Player 0 -> X
        1: 'O',      # Player 1 -> O  
        None: '.'    # Empty position -> dot
    }
    
    result = []
    
    # Header section
    result.append("CONNECT-4 BOARD STATE")
    result.append("DIMENSIONS: 6 rows x 7 columns")
    result.append("COORDINATE SYSTEM: Column 1-7 (left to right), Row 1-6 (bottom to top)")
    result.append("PIECES: X=Player1, O=Player2, .=Empty")
    result.append("")
    
    # Visual board section
    result.append("VISUAL BOARD:")
    result.append("   Col: 1 2 3 4 5 6 7")
    result.append("   ==================")
    
    # Process rows from top to bottom (row 5 to 0 for visual correctness)
    for row in range(NUMROWS-1, -1, -1):
        row_str = f"Row {row+1}: "  # Row number (1-6 for human readability)
        
        for col in range(NUMCOLS):
            player = game_board[col][row]
            char = player_chars[player]
            row_str += char + " "
        
        result.append(row_str)
    
    result.append("   ==================")
    result.append("   Col: 1 2 3 4 5 6 7")
    result.append("")
    
    # Position data section
    result.append("POSITION DATA (Row,Col):")
    
    # Process rows from bottom to top for position data
    for row in range(NUMROWS):
        row_str = f"Row {row+1}: "
        row_chars = []
        
        for col in range(NUMCOLS):
            player = game_board[col][row]
            char = player_chars[player]
            row_chars.append(char)
        
        row_str += ",".join(row_chars)
        result.append(row_str)
    
    result.append("")
    
    # Occupied positions section
    result.append("OCCUPIED POSITIONS:")
    
    # Collect X and O positions
    x_positions = []
    o_positions = []
    
    for col in range(NUMCOLS):
        for row in range(NUMROWS):
            player = game_board[col][row]
            if player == 0:  # X
                x_positions.append(f"({row+1},{col+1})")
            elif player == 1:  # O
                o_positions.append(f"({row+1},{col+1})")
    
    # Format position lists
    x_pos_str = ", ".join(x_positions) if x_positions else "None"
    o_pos_str = ", ".join(o_positions) if o_positions else "None"
    
    result.append(f"X pieces: {x_pos_str}")
    result.append(f"O pieces: {o_pos_str}")
    result.append("")
    
    # Column heights and next available rows
    column_heights = []
    next_available_rows = []
    
    for col in range(NUMCOLS):
        height = 0
        # Count pieces from bottom up
        for row in range(NUMROWS):
            if game_board[col][row] is not None:
                height = row + 1
        
        column_heights.append(str(height))
        
        # Next available row (height + 1, or "FULL" if column is full)
        if height >= NUMROWS:
            next_available_rows.append("FULL")
        else:
            next_available_rows.append(str(height + 1))
    
    result.append(f"COLUMN HEIGHTS: [{','.join(column_heights)}]")
    result.append(f"NEXT AVAILABLE ROWS: [{','.join(next_available_rows)}]")
    
    return "\n".join(result)


# Test function to demonstrate the AI format
def TestGameBoard2AI():
    
    # Create a test game board with some moves
    test_board = [[None for _ in range(NUMROWS)] for _ in range(NUMCOLS)]
    
    # Add some test moves (matching the example from the original specification)
    test_board[0][0] = 1  # X in column 1, row 1 (bottom)
    test_board[1][0] = 1  # O in column 2, row 1 (bottom)  
    test_board[3][0] = 0  # X in column 4, row 1 (bottom)
    test_board[6][0] = 1  # O in column 7, row 1 (bottom)
    test_board[0][1] = 1  # O in column 1, row 2
    test_board[3][1] = 0  # X in column 4, row 2
    test_board[3][2] = 0  # O in column 4, row 3
    
    print("=== AI-FRIENDLY FORMAT ===")
    print(GameBoard2AI(test_board))


if __name__ == "__main__":
    # Include the constants from the original file
    NUMROWS = 6
    NUMCOLS = 7
    
    TestGameBoard2AI()