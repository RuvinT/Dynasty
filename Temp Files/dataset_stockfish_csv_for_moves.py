import chess
import chess.engine
import random
import h5py
from multiprocessing import Pool, cpu_count
from datetime import datetime
import numpy as np
import time

# Path to the Stockfish engine
engine_path = "/Users/ruvinjagoda/Desktop/Aka/AIP/Stockfish and move/stockfish/stockfish-macos-m1-apple-silicon"
#engine_path ="/Users/ruvinjagoda/Desktop/Aka/AIP/stockfish/stockfish-macos-x86-64"

# Path to the output HDF5 file
OUTPUT_FILE = "./filtered_top_10_moves_depth_20_1m_v0.h5"

# Analysis depth for Stockfish
ANALYSIS_DEPTH = 20
NUMOFMOVES = 10
def init_engine():
    # Initialize the Stockfish engine
    return chess.engine.SimpleEngine.popen_uci(engine_path)



def analyze_position(board_fen, engine, num_moves=NUMOFMOVES):
    
    try:
        # Initialize the engine
        with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
            # Set up a chess board
            board = chess.Board(board_fen)

            # Get the top 10 moves from Stockfish
            result = engine.analyse(board, chess.engine.Limit(depth=ANALYSIS_DEPTH), info=chess.engine.INFO_ALL)
            top_moves = result["pv"][:num_moves]  # Extract top 10 moves
            random.shuffle(top_moves)
            best_move = result["pv"][0]

            return top_moves,best_move
    except Exception as e:
        print(f"An error occurred: {e}")
        return [],None


def process_boards(board_fens):
    engine = None
    print("len of boards",len(board_fens))
    try:
        engine = init_engine()  # Initialize engine within each process
        if engine is None:
            print("Engine failed to initialize.")
            return [(board_fen, [], None) for board_fen in board_fens]  # Return empty results if engine failed to initialize
        
        print("Engine initialized successfully.")
        start_time = time.time()
        data = []
        
        for board_fen in board_fens:
            try:
                top_moves, best_move = analyze_position(board_fen, engine)
                data.append((board_fen, top_moves, best_move))
            except Exception as e:
                print("Exception occurd place 1mmmmmmmmmmmmmm{e}")
                data.append((board_fen, [], None))
        
        engine.quit()  # Ensure the engine is properly closed after processing
        print("Engine closed successfully.")
        end_time = time.time()
        print(f"Processe time:  {end_time - start_time:.2f} seconds.")
        # Count valid data entries
        valid_countx = sum(1 for best_move in data if best_move is not None)
        
        print(f"Number of valid entries: {valid_countx}")
        
        return data
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        if engine:
            engine.quit()  # Ensure the engine is closed in case of an unexpected error
            print("Engine closed due to unexpected error.")
        return [(board_fen, [], None) for board_fen in board_fens]



def process_unique_boards_to_h5(unique_boards, output_file, batch_size=1000,num_moves = NUMOFMOVES):
    total_boards = len(unique_boards)
    count = 0
    filtered_feature_board =[]
    filtered_best_move =[]
    filtered_top_10_moves =[]
    with h5py.File(output_file, "w") as hf:
        hf.create_dataset("fen", (total_boards,), dtype=h5py.string_dtype(encoding='utf-8'))
        hf.create_dataset("best_move", (total_boards,), dtype=h5py.string_dtype(encoding='utf-8'))
        hf.create_dataset("top_moves", (total_boards, num_moves), dtype=h5py.string_dtype(encoding='utf-8'))

        while count < total_boards:
            batch_boards = unique_boards[count:count+batch_size]
            
            print(f"Processing {min(count + batch_size, total_boards)} boards...")
            
            with Pool(cpu_count()) as pool:
                results = pool.map(process_boards, [batch_boards[i::cpu_count()] for i in range(cpu_count())])
            
            results_flat = [item for sublist in results for item in sublist]
            valid_count = 0
            for i, (fen, top_moves, best_move) in enumerate(results_flat):
                if best_move is not None:
                    move_uci = best_move.uci()
                    board = chess.Board(fen)
                    if ((move_uci in [move.uci() for move in board.legal_moves]) and (move_uci in [move.uci() for move in top_moves])):
                       
                        if len(top_moves) == num_moves:
                            hf["top_moves"][count + valid_count] =[move.uci() for move in top_moves]
                            filtered_top_10_moves = [move.uci() for move in top_moves]
                            hf["best_move"][count + valid_count] = move_uci
                            filtered_best_move.append(move_uci)
                            hf["fen"][count + valid_count] = fen
                            filtered_feature_board.append(fen)
                            valid_count += 1
                    else:
                        print(f"Invalid move {move_uci}")
                else:
                    print("No valid best move")

            count += batch_size
            print(f"valid count {valid_count} boards...")
            
            
            
        # Save the filtered data to a new .h5 file
        new_file_path = "./filtered_top_10_moves_depth_20_1m_v1.h5"
        with h5py.File(new_file_path, "w") as hf:
            hf.create_dataset("fen", data=np.array(filtered_feature_board, dtype='S'))
            hf.create_dataset("best_move", data=np.array(filtered_best_move, dtype='S'))
            hf.create_dataset("top_moves", data=np.array(filtered_top_10_moves, dtype='S'))

        print(f"Filtered data saved to {new_file_path}")   

        print("Total unique boards processed:", count)

def is_draw(board):
    """
    Check if the current board position results in a draw.
    """
    return (
        board.is_stalemate() or
        board.is_insufficient_material() or
        board.is_seventyfive_moves() or  # Seventy-five-move rule
        board.is_fivefold_repetition()   # Fivefold repetition
    )


def generate_unique_board_states(num_states):
    """
    Generate a specified number of unique board states by making random moves.

    Args:
    - num_states: Number of unique board states to generate.

    Returns:
    - List of unique board states represented as FEN strings where it's Black's turn.
    """
    unique_states = set()
    board = chess.Board()
    
    while len(unique_states) < num_states:
        legal_moves = list(board.legal_moves)
        
        if not legal_moves or is_draw(board):
            board = chess.Board()  # Reset the board if no legal moves left
            continue
            
        random_move = random.choice(legal_moves)
        board.push(random_move)
        
        # Check if it's Black's turn and add the FEN string to unique_states
        if board.turn == chess.BLACK:
            unique_states.add(board.fen())
            
            if len(unique_states) % 100000 == 0:
                print(f"Unique boards: {len(unique_states)}")


    return list(unique_states)

def load_from_h5(filename):
    """
    Load a list of FEN strings from an HDF5 file.

    Args:
    - filename: Name of the HDF5 file to load the data from.

    Returns:
    - List of FEN strings.
    """
    with h5py.File(filename, 'r') as h5file:
        dataset = h5file['fen_strings']
        data_as_bytes = dataset[:]
        data = [s.decode('utf-8') for s in data_as_bytes]
    return data

if __name__ == "__main__":
    
    unique_board_states = load_from_h5('./5m_boards.h5')
  
    print("Total unique board states generated where it's Black's turn:", len(unique_board_states))
    
    process_unique_boards_to_h5(unique_board_states[:100000], OUTPUT_FILE)
   
    