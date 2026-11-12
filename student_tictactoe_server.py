import socket

# Protocol summary (one message per turn, strictly alternating):
#   client -> server : a board index "0".."8" (the player typed 1-9, client subtracts 1)
#   server -> client : "Invalid move"          -> client must choose again
#                      "You win" / "Tie"       -> game over after the client's move
#                      "<index>"               -> the server's move, game continues
#                      "Server wins <index>"   -> server's winning move, game over
#                      "Tie <index>"           -> server's move filled the board, game over
#   client -> server : "yes" / "no" after the game (play again?)


class TicTacToeServer:
    def __init__(self, port=12000):
        self.port = port
        self.board = [' ' for _ in range(9)]
        self.server_socket = None

    def print_board(self):
        print("\nCurrent board:")
        print(" -------------")
        for i in range(0, 9, 3):
            print(f" | {self.board[i]} | {self.board[i+1]} | {self.board[i+2]} | ")
            if i < 6:
                print(" -------------")
        print(" -------------")

    def check_winner(self):
        # Define win combinations
        win_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]

        for combo in win_combinations:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != ' ':
                return self.board[combo[0]]

        if ' ' not in self.board:
            return 'Tie'

        return None

    def setup_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Let the server be restarted right away without "Address already in use"
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(1)
        print('Tic-Tac-Toe Server is ready to play!')

    def handle_client_move(self, connection_socket):
        while True:
            client_move = connection_socket.recv(1024).decode().strip()

            # recv() returns an empty string when the client has closed the connection
            if not client_move:
                raise ConnectionError("Client disconnected")

            # 1. The move must be a digit
            if client_move.isdigit():
                move = int(client_move)
                # 2. It must be a valid board index (0-8, i.e. squares 1-9)
                # 3. The chosen square must be empty
                if 0 <= move <= 8 and self.board[move] == ' ':
                    self.board[move] = 'X'
                    print(f"Client played square {move + 1}")
                    break

            # Any check failed: tell the client and wait for another move
            print(f"Client sent an invalid move: {client_move!r}")
            connection_socket.send("Invalid move".encode())
        self.print_board()

    def make_server_move(self):
        while True:
            try:
                server_move = int(input("Enter your move (1-9): ")) - 1
                if 0 <= server_move <= 8 and self.board[server_move] == ' ':
                    self.board[server_move] = 'O'
                    break
                else:
                    print("Invalid move. Please enter a number between 1 and 9 for an empty space.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        self.print_board() # Display the board after a server's move
        return server_move

    def play_game(self, connection_socket):
        self.board = [' ' for _ in range(9)]
        game_over = False

        while not game_over:
            print("Waiting for client's move...")
            self.handle_client_move(connection_socket)

            # Game-over check after the client's (X) move
            winner = self.check_winner()
            if winner == 'X':
                connection_socket.send("You win".encode())
                print("Client (X) wins!")
                game_over = True
            elif winner == 'Tie':
                connection_socket.send("Tie".encode())
                print("It's a tie!")
                game_over = True

            if not game_over:
                server_move = self.make_server_move()

                # Game-over check after the server's (O) move.
                # The move index is included so the client can draw the final board.
                winner = self.check_winner()
                if winner == 'O':
                    connection_socket.send(f"Server wins {server_move}".encode())
                    print("Server (O) wins!")
                    game_over = True
                elif winner == 'Tie':
                    connection_socket.send(f"Tie {server_move}".encode())
                    print("It's a tie!")
                    game_over = True
                else:
                    # Game continues: just send the server's move to the client
                    connection_socket.send(str(server_move).encode())

    def run(self):
        self.setup_server()
        while True:
            connection_socket, addr = self.server_socket.accept()
            print(f"Game started with {addr}")
            try:
                self.play_game(connection_socket)
                # After the game the client answers "yes" or "no" to playing again
                play_again = connection_socket.recv(1024).decode().strip()
            except OSError as e:  # includes ConnectionError (client quit mid-game)
                print(f"Connection lost: {e}")
                play_again = ''
            connection_socket.close()
            if play_again.lower() != 'yes':
                break
            print("Client wants to play again. Waiting for it to reconnect...")
        self.server_socket.close()
        print("Server shut down.")

if __name__ == "__main__":
    server = TicTacToeServer()
    server.run()
