$(document).ready(function() {
    var board = Chessboard('board', {
        pieceTheme: './chessboardjs-1.0.0/img/chesspieces/wikipedia/{piece}.png',
        position: 'start',
        draggable: true,
        onDrop: onDrop
    });
    var game = new Chess();
    var playerColor = 'white'; // Player plays white by default
    var playerTurn = true; // Flag to track player's turn

    function onDrop(source, target, piece, newPos, oldPos, orientation) {
        // Validate move
        var move = game.move({
            from: source,
            to: target,
            promotion: 'q' // promote to queen for simplicity
        });
        console.log(" move is legal",move);
        // Illegal move
        if (move === null) {
            // It's AI's turn after player's move
            console.log("wromg move")
            playerTurn = true;
            return 'snapback'
        }
        else {

            // Check if the game is over after player's move
            if (game.game_over()) {
                alert('Game over checkmate !');
                return;
                
            }
            playerTurn = false;
        }    

         // If it's not player's turn or player's color, ignore the move
        if (!playerTurn || playerColor !== board.orientation()) {
            // Make the AI move after a short delay
            window.setTimeout(makeAIMove, 250);

        }   
        
    }

    function makeAIMove() {
        console.log("Making AI move...");
        console.log("Current board FEN:", board.fen());

        $.ajax({
            url: 'http://127.0.0.1:5000/get_move',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ board: game.fen() }),
            success: function(response) {
                console.log("Received response from API:", response);

                var move = response.move;
                console.log("Move received from API:", move);

                // Convert move to algebraic notation if needed
                //var algebraicMove = convertToAlgebraic(move);
                //console.log("Algebraic notation move:", algebraicMove);

                // Make the move on the board
                var aiMove = game.move({
                    from: move.slice(0, 2),
                    to: move.slice(2, 4),
                    promotion: 'q'
                });

                // Illegal move or game over
                if (aiMove === null) {
                    alert('Game over checkmate !');
                    return;
                }
                board.position(game.fen())
                // It's player's turn after AI's move
                playerTurn = true;
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Error getting AI move:", textStatus, errorThrown);
                alert('Error getting AI move');
            }
        });
    }

    // Function to convert move to algebraic notation if needed
    function convertToAlgebraic(move) {
        // If move format is like 'd7d5', insert '-' in the middle
        if (move.length === 4) {
            return move.slice(0, 2) + '-' + move.slice(2);
        }
        return move;
    }
});
