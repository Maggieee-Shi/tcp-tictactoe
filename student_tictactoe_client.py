import socket
import sys

class TicTacToeClient:
    def __init__(self, server_name='127.0.0.1', server_port=12000):
        self.server_name = server_name
        self.server_port = server_port
        self.client_socket = None
        self.board = [' ' for _ in range(9)]
        self.last_move = None  # remembered so an "Invalid move" can be undone

    def print_board(self):
        print("\nCurrent board:")
        print(" -------------")
        for i in range(0, 9, 3):
            print(f" | {self.board[i]} | {self.board[i+1]} | {self.board[i+2]} | ")
            if i < 6:
                print(" -------------")
        print(" -------------")

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(5)  # Set a 5 second timeout
        try:
            self.client_socket.connect((self.server_name, self.server_port))
        except socket.error as e:
            print(f"Failed to connect to server: {e}")
            sys.exit(1)
        # The 5 s timeout is only for connecting. The server is a human typing a
        # move, which can take longer than 5 s, so wait as long as needed after that.
        self.client_socket.settimeout(None)
        print(f"Connected to server at {self.server_name}:{self.server_port}. You are X.")

    def get_player_move(self):
        # Keep asking until the player gives a number 1-9 for an empty square
        while True:
            choice = input("Enter your move (1-9): ").strip()
            if not choice.isdigit():
                print("Invalid input. Please enter a number.")
                continue
            position = int(choice) - 1  # squares 1-9 -> board index 0-8
            if not 0 <= position <= 8:
                print("Invalid move. Please enter a number between 1 and 9.")
                continue
            if self.board[position] != ' ':
                print("That square is already taken. Choose an empty one.")
                continue
            return position

    def make_move(self):
        move = self.get_player_move()
        self.client_socket.send(str(move).encode())
        self.board[move] = 'X'
        self.last_move = move
        self.print_board()
        return move

    def apply_server_move(self, text):
        # Place the server's O from a message such as "4" or "Server wins 4"
        server_move = int(text.split()[-1])
        self.board[server_move] = 'O'
        print(f"Server played square {server_move + 1}")

    def handle_server_response(self):
        print("Waiting for server's move...")
        server_response = self.client_socket.recv(1024).decode()

        # Empty response means the server closed the connection
        if not server_response:
            print("The server closed the connection.")
            return True

        if server_response == "You win":
            print("\n*** You win! ***")
            return True

        if server_response.startswith("Tie"):
            if server_response != "Tie":  # "Tie <index>": server made the last move
                self.apply_server_move(server_response)
                self.print_board()
            print("\n*** It's a tie! ***")
            return True

        if server_response.startswith("Server wins"):
            if server_response != "Server wins":
                self.apply_server_move(server_response)
                self.print_board()
            print("\n*** Server wins! ***")
            return True

        if server_response == "Invalid move":
            # The server rejected our move: take the X back and let the player retry
            print("Server says that move was invalid. Try again.")
            if self.last_move is not None:
                self.board[self.last_move] = ' '
            return False

        # Anything else is the server's move (a board index 0-8)
        self.apply_server_move(server_response)
        return False

    def play_game(self):
        game_over = False
        while not game_over:
            self.print_board()
            self.make_move()
            game_over = self.handle_server_response()

    def run(self):
        while True:
            self.board = [' ' for _ in range(9)]  # fresh board for each game
            self.connect_to_server()
            self.play_game()

            # Tell the server whether we want another game
            again = input("Play again? (yes/no): ").strip().lower()
            try:
                self.client_socket.send((again or 'no').encode())
            except OSError:
                pass  # server already gone
            self.client_socket.close()
            if again != 'yes':
                break
            print("Starting a new game...\n")
        print("Game over. Connection closed.")

if __name__ == "__main__":
    client = TicTacToeClient()
    client.run()
