from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from map_generator import MapGenerator, TerrainType


@dataclass
class Player:
    """Represents a player in the game."""

    id: str
    name: str
    color: str


@dataclass
class Unit:
    """Represents a unit in the game owned by a player."""

    name: str
    position: Tuple[int, int]
    player_id: str


@dataclass
class GameState:
    map_grid: List[List[TerrainType]]
    units: Dict[str, Unit]
    players: Dict[str, Player]
    coin_positions: List[Tuple[int, int]]
    turn: int


class GameEngine:
    # Default player colors
    DEFAULT_COLORS = [
        "#F44336",  # Red
        "#2196F3",  # Blue
        "#4CAF50",  # Green
        "#FF9800",  # Orange
        "#9C27B0",  # Purple
        "#00BCD4",  # Cyan
        "#FFEB3B",  # Yellow
        "#795548",  # Brown
    ]

    def __init__(
        self,
        map_grid: Optional[List[List[TerrainType]]] = None,
        width: int = 10,
        height: int = 10,
        water_probability: float = 0.2,
        num_coins: int = 5,
    ):
        """
        Initialize the game engine with a map.

        Args:
            map_grid: Pre-generated map grid (default None, will generate random map)
            width: Width of the map grid if generating (default 10)
            height: Height of the map grid if generating (default 10)
            water_probability: Probability of water tiles if generating (default 0.2)
            num_coins: Number of coins to place (default 5)
        """
        self.current_turn = 0
        self.history: List[GameState] = []

        # Initialize the map - either use provided map or generate one
        if map_grid is None:
            self.map_grid = MapGenerator.generate_random_map(width, height, water_probability)
        else:
            self.map_grid = map_grid

        # Get map dimensions
        self.height = len(self.map_grid)
        self.width = len(self.map_grid[0]) if self.height > 0 else 0

        # Initialize empty collections for players, units and coins
        self.players: Dict[str, Player] = {}
        self.units: Dict[str, Unit] = {}
        self.coin_positions: List[Tuple[int, int]] = []
        self.next_unit_id = 0

        # Add two default players
        self.add_player("Player 1")
        self.add_player("Player 2")

        # Place units at random land positions
        self._place_units()

        # Place coins at random land positions
        self._place_coins(num_coins)

        # Save initial state
        self._save_state()

    def add_player(self, player_name: str) -> str:
        """
        Add a new player to the game.

        Args:
            player_name: Name of the player

        Returns:
            The ID of the newly created player
        """
        player_id = f"p{len(self.players)}"
        color_index = len(self.players) % len(self.DEFAULT_COLORS)

        # Create the player with a unique color
        self.players[player_id] = Player(
            id=player_id, name=player_name, color=self.DEFAULT_COLORS[color_index]
        )

        return player_id

    def add_unit(self, player_id: str) -> str:
        """
        Add a new unit for a player at a random position.

        Args:
            player_id: ID of the player who owns this unit

        Returns:
            The name of the newly created unit
        """
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found")

        # Exclude existing unit positions
        excluded_positions = [unit.position for unit in self.units.values()]

        # Find a position for the new unit
        positions = MapGenerator.find_random_land_positions(self.map_grid, 1, excluded_positions)

        if not positions:
            raise ValueError("No available land positions for new unit")

        # Create a new unit with an incrementing ID
        unit_name = f"{chr(65 + self.next_unit_id)}"
        self.next_unit_id += 1

        self.units[unit_name] = Unit(name=unit_name, position=positions[0], player_id=player_id)

        return unit_name

    def _place_units(self):
        """Place initial units for each player on random land positions."""
        # Place one unit for each player in sorted order to ensure consistent unit assignment
        # This ensures player "p0" gets unit A, player "p1" gets unit B, etc.
        for player_id in sorted(self.players.keys()):
            self.add_unit(player_id)

    def _place_coins(self, num_coins: int):
        """Place a specified number of coins on random land positions."""
        # Exclude unit positions
        excluded_positions = [unit.position for unit in self.units.values()]

        # Find positions for coins
        coin_positions = MapGenerator.find_random_land_positions(
            self.map_grid, num_coins, excluded_positions
        )

        self.coin_positions = coin_positions

    def _save_state(self):
        """Save the current game state to history."""
        state = GameState(
            map_grid=deepcopy(self.map_grid),
            units={name: deepcopy(unit) for name, unit in self.units.items()},
            players={id: deepcopy(player) for id, player in self.players.items()},
            coin_positions=self.coin_positions.copy(),
            turn=self.current_turn,
        )
        self.history.append(state)

    def move_unit(self, unit_name: str, direction: str, player_id: Optional[str] = None) -> bool:
        """
        Move a unit in the specified direction.

        Args:
            unit_name: Name of the unit to move
            direction: Direction to move ('up', 'down', 'left', 'right')
            player_id: ID of the player attempting to move the unit (if None, any player can move)

        Returns:
            True if the move was successful, False otherwise
        """
        if unit_name not in self.units:
            return False

        unit = self.units[unit_name]

        # Check if the player owns this unit
        if player_id is not None and unit.player_id != player_id:
            return False

        x, y = unit.position

        # Calculate new position based on direction
        new_x, new_y = x, y
        if direction == "up" and y < self.height - 1:
            new_y = y + 1
        elif direction == "down" and y > 0:
            new_y = y - 1
        elif direction == "left" and x > 0:
            new_x = x - 1
        elif direction == "right" and x < self.width - 1:
            new_x = x + 1
        else:
            return False

        # Check if new position is land
        if self.map_grid[new_y][new_x] != TerrainType.LAND:
            return False

        # Move the unit
        unit.position = (new_x, new_y)

        # Check if unit landed on a coin
        if (new_x, new_y) in self.coin_positions:
            self.coin_positions.remove((new_x, new_y))

        return True

    def next_turn(self):
        """Advance to the next turn and save the game state."""
        self.current_turn += 1
        self._save_state()

    def render_map(self) -> str:
        """
        Render the current state of the map as a string.

        Returns:
            A string representation of the map
        """
        # Convert units to position dictionary for MapGenerator.render_map
        unit_positions = {unit.name: unit.position for unit in self.units.values()}

        # Get unit colors based on player
        unit_colors = {
            unit.name: self.players[unit.player_id].color for unit in self.units.values()
        }

        return MapGenerator.render_map(
            self.map_grid, unit_positions, self.coin_positions, unit_colors
        )


if __name__ == "__main__":
    # Example usage
    game = GameEngine()
    print(f"Initial map (Turn {game.current_turn}):")
    print(game.render_map())
