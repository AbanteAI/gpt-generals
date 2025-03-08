import random
from typing import Dict, List, Literal, Optional, TypedDict, cast


class UnitInfo(TypedDict):
    x: int
    y: int
    resources: int


GameGrid = List[List[str]]


class GameState(TypedDict):
    grid: GameGrid
    units: Dict[str, UnitInfo]
    resources_collected: int
    game_over: bool
    winner: Optional[str]


Direction = Literal["up", "down", "left", "right"]


class GameEngine:
    """
    Core game engine for GPT Generals that manages the game grid, unit positions,
    and game state updates.

    The game is a single-player game where the goal is to collect resources (r)
    by moving units (A-E) to their grid cells. Units collect resources when they
    move to a cell containing a resource.

    The game ends when the total resources collected equals or exceeds the target.
    """

    def __init__(
        self,
        grid_size: int = 20,
        num_units: int = 5,
        num_resources: int = 15,
        num_water_cells: int = 10,
        target_resources: int = 10,
    ):
        """
        Initialize the game engine with a grid, units, and resources.

        Args:
            grid_size: Size of the square grid (default: 20)
            num_units: Number of units to place on the grid (default: 5)
            num_resources: Number of resources to place on the grid (default: 15)
            num_water_cells: Number of water cells to place on the grid (default: 10)
            target_resources: Number of resources needed to win the game (default: 10)
        """
        self.grid_size = grid_size
        self.num_units = min(num_units, 26)  # Limit to 26 units (A-Z)
        self.num_resources = num_resources
        self.num_water_cells = num_water_cells
        self.target_resources = target_resources
        self.unit_labels = [chr(65 + i) for i in range(self.num_units)]  # A, B, C, D, E, ...
        self.total_resources_collected = 0
        self.winner: Optional[str] = None

        # Initialize empty grid
        self.grid: GameGrid = [[" " for _ in range(grid_size)] for _ in range(grid_size)]

        # Initialize unit positions
        self.units: Dict[str, UnitInfo] = {}

        # Place water cells randomly on the grid
        self._place_water()

        # Place units randomly on the grid
        self._place_units()

        # Place resources randomly on the grid
        self._place_resources()

    def _place_water(self) -> None:
        """Place water cells randomly on the grid."""
        available_positions = [(x, y) for x in range(self.grid_size) for y in range(self.grid_size)]

        for _ in range(min(self.num_water_cells, len(available_positions))):
            if not available_positions:
                break

            pos_idx = random.randrange(len(available_positions))
            x, y = available_positions.pop(pos_idx)

            self.grid[y][x] = "~"

    def _place_units(self) -> None:
        """Place units randomly on the grid."""
        available_positions = [
            (x, y)
            for x in range(self.grid_size)
            for y in range(self.grid_size)
            if self.grid[y][x] == " "
        ]

        for unit in self.unit_labels:
            if not available_positions:
                break

            pos_idx = random.randrange(len(available_positions))
            x, y = available_positions.pop(pos_idx)

            self.units[unit] = {"x": x, "y": y, "resources": 0}
            self.grid[y][x] = unit

    def _place_resources(self) -> None:
        """Place resources randomly on the grid."""
        available_positions = [
            (x, y)
            for x in range(self.grid_size)
            for y in range(self.grid_size)
            if self.grid[y][x] == " "
        ]

        for _ in range(min(self.num_resources, len(available_positions))):
            if not available_positions:
                break

            pos_idx = random.randrange(len(available_positions))
            x, y = available_positions.pop(pos_idx)

            self.grid[y][x] = "r"

    def is_valid_move(self, unit: str, direction: Direction) -> bool:
        """
        Check if a move is valid.

        Args:
            unit: The unit to move (A-E)
            direction: The direction to move (up, down, left, right)

        Returns:
            True if the move is valid, False otherwise
        """
        if unit not in self.units:
            return False

        x, y = self.units[unit]["x"], self.units[unit]["y"]

        if direction == "up":
            new_y = y - 1
            new_x = x
        elif direction == "down":
            new_y = y + 1
            new_x = x
        elif direction == "left":
            new_y = y
            new_x = x - 1
        else:  # right
            new_y = y
            new_x = x + 1

        # Check if the new position is within bounds
        if not (0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size):
            return False

        # Check if the new position has a terrain obstacle (water)
        if self.grid[new_y][new_x] == "~":
            return False

        # Check if the new position has another unit
        if self.grid[new_y][new_x] in self.unit_labels:
            return False

        return True

    def move_unit(self, unit: str, direction: Direction) -> bool:
        """
        Move a unit in the specified direction if the move is valid.

        Args:
            unit: The unit to move (A-E)
            direction: The direction to move (up, down, left, right)

        Returns:
            True if the move was successful, False otherwise
        """
        if not self.is_valid_move(unit, direction):
            return False

        x, y = self.units[unit]["x"], self.units[unit]["y"]

        # Calculate new position
        if direction == "up":
            new_y = y - 1
            new_x = x
        elif direction == "down":
            new_y = y + 1
            new_x = x
        elif direction == "left":
            new_y = y
            new_x = x - 1
        else:  # right
            new_y = y
            new_x = x + 1

        # Check if there's a resource at the new position
        has_resource = self.grid[new_y][new_x] == "r"

        # Update grid
        self.grid[y][x] = " "
        self.grid[new_y][new_x] = unit

        # Update unit position
        self.units[unit]["x"] = new_x
        self.units[unit]["y"] = new_y

        # If there was a resource, collect it
        if has_resource:
            self.units[unit]["resources"] += 1
            self.total_resources_collected += 1

            # Check if the game is over
            if self.total_resources_collected >= self.target_resources:
                self.winner = self._determine_winner()

        return True

    def _determine_winner(self) -> str:
        """
        Determine the winner of the game.

        Returns:
            The unit with the most resources
        """
        max_resources = 0
        winner = ""

        for unit, info in self.units.items():
            if info["resources"] > max_resources:
                max_resources = info["resources"]
                winner = unit

        return winner

    def collect_resource(self, unit: str) -> bool:
        """
        Check if the unit is on a resource and collect it if so.
        This is automatically called after moving a unit, but can be called
        explicitly if needed.

        Args:
            unit: The unit to check (A-E)

        Returns:
            True if a resource was collected, False otherwise
        """
        if unit not in self.units:
            return False

        x, y = self.units[unit]["x"], self.units[unit]["y"]

        if self.grid[y][x] == "r":
            # Update grid (the unit is already there after moving)
            self.grid[y][x] = unit

            # Update unit resources
            self.units[unit]["resources"] += 1

            # Update total resources collected
            self.total_resources_collected += 1

            # Check if the game is over
            if self.total_resources_collected >= self.target_resources:
                self.winner = self._determine_winner()

            return True

        return False

    def process_command(self, command: str) -> bool:
        """
        Process a command to update the game state.

        Args:
            command: A command string (e.g., "A left", "B up", "C right", "D down")

        Returns:
            True if the command was processed successfully, False otherwise
        """
        # Normalize command
        command = command.strip().lower()

        # Split command into parts
        parts = command.split()

        # Handle simple movement commands like "A left"
        if len(parts) >= 2:
            unit = parts[0].upper()
            direction = parts[1].lower()

            # Check if the unit is valid
            if unit not in self.units:
                return False

            # Check if the direction is valid
            if direction not in ["up", "down", "left", "right"]:
                return False

            # Move the unit
            return self.move_unit(unit, cast(Direction, direction))

        return False

    def is_game_over(self) -> bool:
        """
        Check if the game is over.

        Returns:
            True if the total resources collected equals or exceeds the target, False otherwise
        """
        return self.total_resources_collected >= self.target_resources

    def get_state(self) -> GameState:
        """
        Get the current game state.

        Returns:
            A dictionary containing the grid, unit positions, resources collected,
            and game over status
        """
        return {
            "grid": [row[:] for row in self.grid],  # Create a deep copy of the grid
            # Create a deep copy of the units
            "units": {unit: info.copy() for unit, info in self.units.items()},
            "resources_collected": self.total_resources_collected,
            "game_over": self.is_game_over(),
            "winner": self.winner,
        }

    def print_grid(self) -> None:
        """Print the current grid state to the console."""
        print("  " + " ".join(str(i % 10) for i in range(self.grid_size)))
        for y, row in enumerate(self.grid):
            print(f"{y % 10} " + " ".join(cell if cell != " " else "." for cell in row))
        print()


if __name__ == "__main__":
    # Initialize the game
    engine = GameEngine()

    # Print the initial state
    print("Initial state:")
    engine.print_grid()
    print(f"Units: {engine.units}")

    # Make some moves and collect resources
    print("\nMoving unit A left:")
    engine.move_unit("A", "left")
    engine.print_grid()

    # Process a command
    print("\nProcessing command 'B down':")
    engine.process_command("B down")
    engine.print_grid()

    # Print the game state
    print("\nGame state:")
    state = engine.get_state()
    print(f"Units: {state['units']}")
    print(f"Resources collected: {state['resources_collected']}")
    print(f"Game over: {state['game_over']}")
    print(f"Winner: {state['winner']}")
