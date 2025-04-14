import chess
import chess.engine
import argparse
import sys

# File paths
FEN_FILE = "game/fen.txt"
MOVES_FILE = "game/moves.txt"
STATUS_FILE = "game/status.txt"

def new_game():
    """Start a new chess game with Stockfish making the first move."""
    # Initialize a new chess board (starting position)
    board = chess.Board()
    
    try:
        engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        
        # Get Stockfish's move
        result = engine.play(board, chess.engine.Limit(time=2.0))
        move = result.move
        
        # Make the move
        board.push(move)
        
        # Print the board after Stockfish's move
        print(f"Board after Stockfish's move ({move.uci()}):")
        print(board)
        
        # Create directories if they don't exist
        import os
        os.makedirs(os.path.dirname(FEN_FILE), exist_ok=True)
        
        # Write the current FEN to fen.txt
        with open(FEN_FILE, "w") as fen_file:
            fen_file.write(board.fen() + "\n")
        
        # Write the move in UCI format to moves.txt
        with open(MOVES_FILE, "w") as moves_file:
            moves_file.write(move.uci())
        
        # Write board representation to status.txt
        with open(STATUS_FILE, "w") as status_file:
            status_file.write(str(board))
               
        # Close the engine
        engine.quit()
        
        return board
        
    except FileNotFoundError:
        print("Error: Stockfish engine not found")
        print("Make sure the Stockfish executable is in your PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def player_move(move_str):
    """Player makes a move in UCI format."""
    # Load current board state
    try:
        with open(FEN_FILE) as f:
            board = chess.Board(f.readlines()[-1])
    except FileNotFoundError:
        print("No game in progress. Start a new game first.")
        return None
    
    # Check if game is already over
    if board.is_game_over():
        print(game_over_message(board))
        return board
    
    # Parse and validate player's move
    try:
        move = chess.Move.from_uci(move_str)
        if move not in board.legal_moves:
            print(f"Illegal move: {move_str}")
            print(f"Valid moves: {' '.join(m.uci() for m in board.legal_moves)}")
            return board
    except ValueError:
        print("Invalid move format! Please use UCI notation (e.g., e2e4)")
        return board
    
    # Make player's move
    board.push(move)
    
    # Update files
    with open(FEN_FILE, "a") as f:
        f.write(board.fen() + "\n")
    with open(MOVES_FILE, "a") as f:
        f.write(" " + move.uci())
    with open(STATUS_FILE, "w") as f:
        f.write(str(board))
    
    # Check if game is over after player's move
    if board.is_game_over():
        print(board)
        print(game_over_message(board))
        return board
    
    return board

def stockfish_move():
    """Stockfish makes a move in response to player's move."""
    # Load current board state
    try:
        with open(FEN_FILE) as f:
            board = chess.Board(f.readlines()[-1])
    except FileNotFoundError:
        print("No game in progress. Start a new game first.")
        return None
    
    # Check if game is already over
    if board.is_game_over():
        print(game_over_message(board))
        return board
    
    try:
        with chess.engine.SimpleEngine.popen_uci("stockfish") as engine:
            # Get engine's move
            result = engine.play(board, chess.engine.Limit(time=2.0))
            move = result.move
            
            # Make the move
            board.push(move)
            
            # Update files
            with open(FEN_FILE, "a") as f:
                f.write(board.fen() + "\n")
            with open(MOVES_FILE, "a") as f:
                f.write("\n" + move.uci())
            with open(STATUS_FILE, "w") as f:
                f.write(str(board))
            
            print(f"Stockfish played: {move.uci()}")
            
            # Check if game is over after engine's move
            if board.is_game_over():
                print(board)
                print(game_over_message(board))
            
            return board
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return board

def show_board():
    """Display the current board state in the terminal."""
    try:
        with open(FEN_FILE) as f:
            board = chess.Board(f.readlines()[-1])
        
        print(board)
        
        # Show additional information
        side_to_move = "White" if board.turn else "Black"
        print(f"Current turn: {side_to_move}")
        
        if board.is_check():
            print("CHECK!")
        
        if board.is_game_over():
            print(game_over_message(board))
        else:
            print(f"Valid moves: {' '.join(m.uci() for m in board.legal_moves)}")
        
        return board
    
    except FileNotFoundError:
        print("No game in progress. Start a new game first.")
        return None

def game_over_message(board):
    """Return appropriate game over message."""
    if board.is_checkmate():
        return "Checkmate!"
    if board.is_stalemate():
        return "Stalemate!"
    if board.is_insufficient_material():
        return "Draw due to insufficient material!"
    if board.is_fifty_moves():
        return "Draw by fifty-move rule!"
    if board.is_repetition():
        return "Draw by repetition!"
    return "Game Over!"

def main():
    parser = argparse.ArgumentParser(description="Chess game against Stockfish")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # New game command
    subparsers.add_parser("new", help="Start a new game")
    
    # Player move command
    move_parser = subparsers.add_parser("move", help="Make a move as a player")
    move_parser.add_argument("uci", help="Move in UCI notation (e.g., e2e4)")
    
    # Show board command
    subparsers.add_parser("show", help="Show the current board state")
    
    args = parser.parse_args()
    
    if args.command == "new":
        new_game()
    elif args.command == "move":
        board = player_move(args.uci)
        # Only make stockfish move if player's move was legal
        # Check if the board was updated with the player's move
        try:
            with open(FEN_FILE) as f:
                lines = f.readlines()
                current_fen = lines[-1].strip()
                # If there's only one line or the last move wasn't the player's
                if len(lines) <= 1 or chess.Board(current_fen).turn == chess.BLACK:
                    # This means player's move wasn't applied (was illegal)
                    return
        except FileNotFoundError:
            return
        
        stockfish_move()
    elif args.command == "show":
        show_board()

if __name__ == "__main__":
    main()
