from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Sample game state for testing
game_state = {
    "grid": [[" " for _ in range(20)] for _ in range(20)],
    "units": {"A": {"x": 3, "y": 5}, "B": {"x": 8, "y": 12}},
    "resources": [{"type": "r", "x": 2, "y": 1}]
}

# Initialize grid with units and resources
def update_grid():
    # Clear grid
    grid = [[" " for _ in range(20)] for _ in range(20)]

    # Place units
    for unit_id, unit_data in game_state["units"].items():
        x, y = unit_data["x"], unit_data["y"]
        if 0 <= x < 20 and 0 <= y < 20:
            grid[y][x] = unit_id

    # Place resources
    for resource in game_state.get("resources", []):
        x, y = resource["x"], resource["y"]
        if 0 <= x < 20 and 0 <= y < 20:
            grid[y][x] = resource["type"]

    game_state["grid"] = grid
    return grid

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    # Send initial game state to client
    update_grid()
    emit('update_game_state', game_state)

@socketio.on('command')
def handle_command(command):
    # Process command (in the future this will interact with the game engine)
    # For now, just echo it back to the chat
    emit('chat_message', {'message': f'You: {command}'})

    # Example of moving unit A left (for testing)
    if command.lower() == "alpha, move left" or command.lower() == "a, move left":
        game_state["units"]["A"]["x"] = max(0, game_state["units"]["A"]["x"] - 1)
        update_grid()
        emit('update_game_state', game_state)
        emit('chat_message', {'message': 'System: Unit A moved left.'})

if __name__ == '__main__':
    # Initialize the grid before starting
    update_grid()
    socketio.run(app, debug=True)
