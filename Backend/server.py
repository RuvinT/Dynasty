#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 29 08:58:03 2024

@author: ruvinjagoda
"""

import chess
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# Load the pre-trained model
model = models.Sequential([
    layers.Conv2D(64, (3, 3), activation='relu', input_shape=(8, 8, 12), padding='same'),
    layers.BatchNormalization(),
    layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.1),

    layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.2),

    layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
    layers.BatchNormalization(),
    layers.MaxPooling2D((2, 2)),
    layers.Dropout(0.05),

    layers.Flatten(),
    layers.Dense(1024, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.1),

    layers.Dense(4096, activation='softmax')
])
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.load_weights("model_weights_v91.h5")

# Function to convert a board state to one-hot encoding
def board_to_one_hot(board):
    one_hot = np.zeros((8, 8, 12), dtype=np.int8)
    piece_map = {
        chess.PAWN: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 4,
        chess.KING: 5
    }
    for square in chess.scan_reversed(chess.BB_ALL):
        piece = board.piece_at(square)
        if piece is not None:
            piece_index = piece_map[piece.piece_type] + (6 if piece.color else 0)
            one_hot[chess.square_rank(square), chess.square_file(square), piece_index] = 1
    return one_hot

# Function to get the AI's move
def get_ai_move(board):
    print("turn",board.turn)
    if board.turn :
        print("black turn")
        board = board.mirror()
    one_hot = board_to_one_hot(board)
    one_hot = np.expand_dims(one_hot, axis=0)
    predictions = model.predict(one_hot)
    legal_moves = filter_legal_moves(board, predictions)
    best_move, _ = max(legal_moves, key=lambda x: x[1])
    return best_move

# Function to filter out illegal moves from predictions
def filter_legal_moves(board, predictions):
    legal_moves = []
    for move in board.legal_moves:
        from_square = move.from_square
        to_square = move.to_square
        move_index = from_square * 64 + to_square
        prob = predictions[0][move_index]
        legal_moves.append((move, prob))
    return legal_moves

@app.route('/get_move', methods=['POST'])
def get_move():
    board_state = request.json['board']
    board = chess.Board(board_state)
    move = get_ai_move(board)
    return jsonify({'move': move.uci()})

if __name__ == '__main__':
    app.run(debug=True)
