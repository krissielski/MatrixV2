# Shared components of the Connect4 game


#Define Game board Size Parameters
NUMROWS     = 6
NUMCOLS     = 7


#return row or None if FULL
def GetFirstOpenRow( board, col ):
    if 0 <= col < NUMCOLS:
        for row in range(NUMROWS):
            if board[col][row] is None:
                return row
        return None
    else:
        raise IndexError("Column out of range")

#Check to see if all slots are filled
def CheckForDraw(board):
    for col in range(NUMCOLS):
        if GetFirstOpenRow(board,col) is not None:
            return False
    return True

#returns TRUE if valid move, else false
def CheckForValidMove(board, col, row ):
    if board[col][row] == None:
        return True
    return False



#returns a list of winning positions, or None if no winner found
def CheckForWinner(board, col, row, player):
    
    # Validate input parameters
    if not (0 <= col < NUMCOLS and 0 <= row < NUMROWS):
        raise IndexError("Invalid board position")
    
    # Check if the position actually contains the player's chip
    if board[col][row] != player:
        return None
    
    # Check all four directions for 4-in-a-row
    directions = [
        (0, 1),   # Horizontal
        (1, 0),   # Vertical  
        (1, 1),   # Diagonal (bottom-left to top-right)
        (1, -1)   # Diagonal (top-left to bottom-right)
    ]
    
    for dx, dy in directions:

        count = 1                   # Count the chip at the starting position
        positions = [(col,row)]     # Include the starting position
        
        # Check in positive direction
        c, r = col + dx, row + dy
        while (0 <= c < NUMCOLS and 0 <= r < NUMROWS and board[c][r] == player):
            positions.append( (c,r) )
            count += 1
            c += dx
            r += dy
        
        # Check in negative direction  
        c, r = col - dx, row - dy
        while (0 <= c < NUMCOLS and 0 <= r < NUMROWS and board[c][r] == player):
            positions.append( (c,r) )
            count += 1
            c -= dx
            r -= dy
        
        #Check for at least 4 in a row
        if len(positions) >= 4:
            return positions
    
    #Nope, none found
    return None

