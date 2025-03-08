import random
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy


class TerrainType(Enum):
    LAND = "."
    WATER = "~"


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
    def __init__(self, width: int = 20, height: int = 20, water_probability: float = 0.2):
        """
        Initialize the game engine with a map of specified dimensions.
        
        Args:
            width: Width of the map grid (default 20)
            height: Height of the map grid (default 20)
            water_probability: Probability of a cell being water (default 0.2)
        """
        self.width = width
        self.height = height
        self.current_turn = 0
        self.history: List[GameState] = []
        
        # Initialize the map with terrain
        self.map_grid = self._generate_map(water_probability)
        
        # Initialize empty collections for units and coins
        self.units: Dict[str, Unit] = {}
        self.coin_positions: List[Tuple[int, int]] = []
        
        # Place units at random land positions
        self._place_units()
        
        # Place coins at random land positions
        self._place_coins(5)  # Place 5 coins
        
        # Save initial state
        self._save_state()
    
    def _generate_map(self, water_probability: float) -> List[List[TerrainType]]:
        """Generate a random map with land and water."""
        map_grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                terrain = TerrainType.WATER if random.random() < water_probability else TerrainType.LAND
                row.append(terrain)
            map_grid.append(row)
        return map_grid
    
    def _get_random_land_position(self) -> Tuple[int, int]:
        """Get a random position on land that's not occupied by units or coins."""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            # Check if position is land and not occupied
            if (self.map_grid[y][x] == TerrainType.LAND and
                    (x, y) not in [unit.position for unit in self.units.values()] and
                    (x, y) not in self.coin_positions):
                return (x, y)
    
    def _place_units(self):
        """Place units A and B on random land positions."""
        for name in ["A", "B"]:
            position = self._get_random_land_position()
            self.units[name] = Unit(name=name, position=position)
    
    def _place_coins(self, num_coins: int):
        """Place a specified number of coins on random land positions."""
        for _ in range(num_coins):
            position = self._get_random_land_position()
            self.coin_positions.append(position)
    
    def _save_state(self):
        """Save the current game state to history."""
        state = GameState(
            map_grid=deepcopy(self.map_grid),
            units={name: deepcopy(unit) for name, unit in self.units.items()},
            coin_positions=self.coin_positions.copy(),
            turn=self.current_turn
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
        result = []
        
        # Add a header with column numbers
        header = "  " + "".join(f"{i % 10}" for i in range(self.width))
        result.append(header)
        
        for y in range(self.height):
            # Add row number at the beginning of each row
            row = f"{y % 10} "
            
            for x in range(self.width):
                # Check if there's a unit at this position
                unit_at_pos = None
                for unit in self.units.values():
                    if unit.position == (x, y):
                        unit_at_pos = unit
                        break
                
                if unit_at_pos:
                    row += unit_at_pos.name
                elif (x, y) in self.coin_positions:
                    row += "C"
                else:
                    row += self.map_grid[y][x].value
            
            result.append(row)
        
        return "\n".join(result)


if __name__ == "__main__":
    # Example usage
    game = GameEngine()
    print(f"Initial map (Turn {game.current_turn}):")
    print(game.render_map())
