import requests
import json
from c4_common import NUMROWS, NUMCOLS

# Configuration constants
OLLAMA_MODEL       = 'llama3.2'
OLLAMA_MODEL       = 'llama3'

OLLAMA_HOST        = 'http://192.168.3.50:11434'
OLLAMA_PROMPT_FILE = 'c4_ollama_prompt.txt'

OLLAMA_TIMEOUT     = (5*60)      #Request Timeout (seconds)      

def GetOllamaMove(game_board, current_player):

    # Generate the dynamic prompt
    prompt = generate_prompt(game_board, current_player)
    
    # Call Ollama API
    try:
        response = call_ollama_api(prompt)
        
        # Parse the response to extract column number
        column = parse_ai_response(response)
        
        return column
        
    except Exception as e:
        print(f"Error getting AI move: {e}")
        # Fallback to random move if AI fails
        import random
        return random.randint(0, 6)


def generate_prompt(game_board, current_player):

    try:
        # Read the base prompt from file
        with open(OLLAMA_PROMPT_FILE, 'r') as f:
            base_prompt = f.read()
            
    except FileNotFoundError:
        print(f"Error: Could not find prompt file '{OLLAMA_PROMPT_FILE}'")
        raise
    
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        raise
    
    # Replace the board state section with current game state
    prompt_lines = base_prompt.split('\n')
    
    # Find where to insert the board state (after "BOARD STATE BY COLUMN")
    board_start_index = -1
    for i, line in enumerate(prompt_lines):
        if "BOARD STATE BY COLUMN" in line:
            board_start_index = i + 1
            break
    
    if board_start_index == -1:
        # If we can't find the marker, just append to the end
        prompt = base_prompt + "\n\nBOARD STATE BY COLUMN (bottom to top):\n"
    else:
        # Keep everything up to the board state marker
        prompt = '\n'.join(prompt_lines[:board_start_index]) + '\n'
    
    # Generate current board state for each column
    for col in range(NUMCOLS):
        column_state = f"Column {col + 1}: "
        
        row_states = []
        for row in range(NUMROWS):
            if game_board[col][row] is None:
                row_states.append(f"Row{row + 1}=empty")
            elif game_board[col][row] == 0:  # Player 1 (X)
                row_states.append(f"Row{row + 1}=X")
            else:  # Player 2 (O)
                row_states.append(f"Row{row + 1}=O")
        
        column_state += ", ".join(row_states)
        prompt += column_state + "\n"
    
    # Update current player in the prompt if it contains the placeholder
    current_player_symbol = "X" if current_player == 0 else "O"
    prompt = prompt.replace("CURRENT PLAYER: X to make a next move", 
                           f"CURRENT PLAYER: {current_player_symbol} to make a next move")
    
    return prompt


def call_ollama_api(prompt):

    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Lower temperature for more deterministic responses
            "top_p": 0.9,
            "top_k": 10
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to call Ollama API: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Ollama response: {e}")


def parse_ai_response(response):
 
    # Clean up the response
    response = response.strip()
    
    # Try to extract number from response
    import re
    
    # Look for single digit 1-7
    numbers = re.findall(r'\b[1-7]\b', response)
    
    if numbers:
        # Take the first valid number found
        column_1_based = int(numbers[0])
        # Convert to 0-based index
        column = column_1_based - 1
        
        if 0 <= column <= 6:
            return column
    
    # If no valid number found, try to parse the entire response as a number
    try:
        column_1_based = int(response)
        if 1 <= column_1_based <= 7:
            return column_1_based - 1
    except ValueError:
        pass
    
    # If we can't parse a valid column, raise an exception
    raise ValueError(f"Could not parse valid column from AI response: '{response}'")


def test_connection():

    try:
        url = f"{OLLAMA_HOST}/api/tags"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        print("Successfully connected to Ollama server")
        return True
    except Exception as e:
        print(f"Failed to connect to Ollama server: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test connection
    test_connection()
    
    # Test with a sample board state
    test_board = [[None for _ in range(NUMROWS)] for _ in range(NUMCOLS)]
    
    # Add some test pieces
    test_board[0][0] = 1  # O in column 1, row 1
    test_board[0][1] = 1  # O in column 1, row 2
    test_board[1][0] = 1  # O in column 2, row 1
    test_board[3][0] = 0  # X in column 4, row 1
    test_board[3][1] = 0  # X in column 4, row 2
    test_board[3][2] = 0  # X in column 4, row 3
    test_board[6][0] = 1  # O in column 7, row 1
    
    print("\nTesting AI move generation...")
    try:
        prompt = generate_prompt(test_board, 0)  # Player X's turn
        print("Generated prompt:")
        print(prompt)
        print("\n" + "="*50 + "\n")
        
        column = GetOllamaMove(test_board, 0)
        print(f"AI suggested column: {column + 1} (0-based: {column})")
        
    except Exception as e:
        print(f"Error during testing: {e}")