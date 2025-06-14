import requests
import json
import re
from c4_common import NUMROWS, NUMCOLS

# Configuration constants
OLLAMA_MODEL       = 'llama3.2:3b'
#OLLAMA_MODEL       = 'llama3:8b'
#OLLAMA_MODEL       = 'phi4:14b'
#OLLAMA_MODEL        = 'mistral:7b'
#OLLAMA_MODEL        = 'hermes3:8b'



OLLAMA_HOST        = 'http://192.168.3.50:11434'
OLLAMA_PROMPT_FILE = 'c4_ollama_prompt.txt'

OLLAMA_TIMEOUT     = (15*60)      #Request Timeout (seconds)      


# AI generation parameters
OLLAMA_TEMPERATURE = 0.1    # Controls randomness (0.0 = very deterministic, 1.0 = very random)
OLLAMA_TOP_P = 0.9          # Nucleus sampling parameter (controls diversity)
OLLAMA_TOP_K = 10           # Limits the number of highest probability tokens to consider


#Output Prompt to a file
OLLAMA_OUTPUT_FILE   = 'logs/outputprompt.txt'
OLLAMA_OUTPUT_ENABLE = 1    # 1=Enable, 0=Disable

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
    
    # Generate current board state text separately
    board_state = ""
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
        board_state += column_state + "\n"
    
    # Update current player in base prompt
    current_player_symbol = "X" if current_player == 0 else "O"
    base_prompt = base_prompt.replace("?", f"{current_player_symbol} (Player{current_player + 1})" )
    
    # Combine base prompt with board state
    final_prompt = base_prompt + "\n" + board_state

    # Output final prompt to file
    if OLLAMA_OUTPUT_ENABLE == 1:
        with open(OLLAMA_OUTPUT_FILE, 'w') as f:
            f.write(final_prompt)

    
    return final_prompt



def call_ollama_api(prompt):

    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
            "top_p": OLLAMA_TOP_P,
            "top_k": OLLAMA_TOP_K
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()

        # print("-------------------")
        # print("Ollama Full Response:", result)
        # print()
        print("Ollama Model:    ",OLLAMA_MODEL)
        print("Ollama Duration: ",int(result.get("total_duration", "")/1000000000))
        print("Ollama Response: ",result.get("response", "").strip())
        # print("-------------------")

        return result.get("response", "").strip()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to call Ollama API: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse Ollama response: {e}")


def parse_ai_response(response):

    # Response should be in the format:  
    #      { "col":#, "reason":"'your reason'"}

    # Use regex to find "col": followed by a number 1-7
    match = re.search(r'"col"\s*:\s*([1-7])', response)
    
    if match:
        column_1_based = int(match.group(1))
        return column_1_based - 1  # Convert to 0-based index
    
    # Legacy fallback????
    # # Find all numbers 1-7 in the response
    # numbers = re.findall(r'[1-7]', response)
    
    # if numbers:
    #     # Take the last valid number found and convert to 0-based index
    #     column_1_based = int(numbers[-1])
    #     return column_1_based - 1
    
    # If no valid column found, raise an exception
    raise ValueError(f"Could not find valid column [1-7] in AI response: '{response}'")



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