import chess
import chess.engine
import pandas as pd
import logging
from stockfish import Stockfish
import csv
from multiprocessing import Pool, cpu_count, current_process

# Path to the Stockfish engine
engine_path = "/Users/ruvinjagoda/Desktop/Aka/AIP/Stockfish and move/stockfish/stockfish-macos-m1-apple-silicon"

# Number of moves to get from Stockfish
NUMOFMOVES = 5

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_engine_stockfish():
    stockfish = Stockfish(engine_path)
    stockfish.set_elo_rating(3000)
    return stockfish

def init_engine():
    # Initialize the Stockfish engine
    return chess.engine.SimpleEngine.popen_uci(engine_path)

def analyze_position(board_fen, stockfish, engine, num_moves=NUMOFMOVES):
    try:
        stockfish.set_fen_position(board_fen)
        move_infos = stockfish.get_top_moves(num_moves)
        top_moves = [move_info['Move'] for move_info in move_infos]
        centipawns = [move_info['Centipawn'] for move_info in move_infos]
        mates = [move_info['Mate'] for move_info in move_infos]
        best_move = stockfish.get_best_move()
        board = chess.Board(board_fen)

        result = engine.analyse(board, chess.engine.Limit(time=0.5))
        move_sequence = result["pv"][:num_moves] 
        move_sequence = [move.uci() for move in move_sequence]
        return top_moves, best_move, centipawns, mates,move_sequence
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return [], None, [], []

def process_fens(fens_chunk):
    stockfish = init_engine_stockfish()
    engine = init_engine()

    results = []
    count = 0
    for fen in fens_chunk:
        top_moves, best_move, centipawns, mates,move_sequence = analyze_position(fen, stockfish, engine)
        results.append((fen, top_moves, best_move, centipawns, mates,move_sequence))
        count+=1
        
        if count % 10 == 0:
            logging.info(f"Process {current_process().name} processed {count} FENs in current chunk")
    engine.quit()
    return results

def enhance_and_save_csv(input_filename, output_filename):
    # Read the original CSV file
    df = pd.read_csv(input_filename)
    
    df = df[100000:300000]
    
    fens = df["FEN"].tolist()
    
    # Split the FENs into chunks for multiprocessing
    num_cores = cpu_count()
    chunk_size = len(fens) // num_cores
    fens_chunks = [fens[i:i + chunk_size] for i in range(0, len(fens), chunk_size)]

    # Process the chunks in parallel
    with Pool(num_cores) as pool:
        results = pool.map(process_fens, fens_chunks)

    # Combine the results
    results_flat = [item for sublist in results for item in sublist]

    # Create new columns in the DataFrame
    df["TopMoves"] = [result[1] for result in results_flat]
    df["BestMove"] = [result[2] for result in results_flat]
    df["Centipawns"] = [result[3] for result in results_flat]
    df["Mates"] = [result[4] for result in results_flat]
    df["MoveSequence"] = [result[5] for result in results_flat]
    # Save the enhanced DataFrame to a new CSV file
    df.to_csv(output_filename, index=False)
    logging.info(f"Enhanced data saved to {output_filename}")

if __name__ == "__main__":
    input_filename = "./magnus_moves_dataset.csv"
    output_filename = "./enhanced_magnus_moves_dataset_v2.csv"
    enhance_and_save_csv(input_filename, output_filename)
    
   
    