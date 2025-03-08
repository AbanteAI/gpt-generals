from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from map_generator import MapGenerator, TerrainType


@dataclass
class Unit:
    name: str
    position: Tuple[int, int]


@dataclass
class GameState:
    map_grid: List[List[TerrainType]]
    units: Dict[str, Unit]
    coin_positions: List[Tuple[int, int]]
    turn: int


class GameEngine:
    def __init__(
        self, 
        map_grid: Optional[List[List[TerrainType]]] = None,
        width: int = 10, 
        height: int = 10, 
        water_probability: float = 0.2,
        num_coins: int = 5
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

        # Initialize empty collections for units and coins
        self.units: Dict[str, Unit] = {}
        self.coin_positions: List[Tuple[int, int]] = []

        # Place units at random land positions
        self._place_units()

        # Place coins at random land positions
        self._place_coins(num_coins)

        # Save initial state
        self._save_state()

    def _place_units(self):
        """Place units A and B on random land positions."""
        excluded_positions = []
        
        # Find positions for units
        unit_positions = MapGenerator.find_random_land_positions(
            self.map_grid, 2, excluded_positions
        )
        
        if len(unit_positions) < 2:
            raise ValueError("Not enough land positions for units")
            
        # Create units at these positions
        unit_names = ["A", "B"]
        for i, name in enumerate(unit_names):
            self.units[name] = Unit(name=name, position=unit_positions[i])
            excluded_positions.append(unit_positions[i])

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
            coin_positions=self.coin_positions.copy(),
            turn=self.current_turn,
        )
        self.history.append(state)

    def move_unit(self, unit_name: str, direction: str) -> bool:
        """
        Move a unit in the specified direction.

        Args:
            unit_name: Name of the unit to move
            direction: Direction to move ('up', 'down', 'left', 'right')

        Returns:
            True if the move was successful, False otherwise
        """
        if unit_name not in self.units:
            return False

        unit = self.units[unit_name]
        x, y = unit.position

        # Calculate new position based on direction
        new_x, new_y = x, y
        if direction == "up" and y > 0:
            new_y = y - 1
        elif direction == "down" and y < self.height - 1:
            new_y = y + 1
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
        
        return MapGenerator.render_map(self.map_grid, unit_positions, self.coin_positions)


if __name__ == "__main__":
    # Example usage
    game = GameEngine()
    print(f"Initial map (Turn {game.current_turn}):")
    print(game.render_map())
