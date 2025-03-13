import random
from enum import Enum
from typing import List, Optional, Tuple


class TerrainType(Enum):
    LAND = "."
    WATER = "~"


class MapGenerator:
    """Class responsible for generating game maps with different terrains."""

    @staticmethod
    def generate_random_map(
        width: int = 10, height: int = 10, water_probability: float = 0.2
    ) -> List[List[TerrainType]]:
        """
        Generate a random map with land and water.

        Args:
            width: Width of the map grid (default 10)
            height: Height of the map grid (default 10)
            water_probability: Probability of a cell being water (default 0.2)

        Returns:
            A 2D grid of TerrainType representing the map
        """
        map_grid = []
        for _y in range(height):
            row = []
            for _x in range(width):
                terrain = (
                    TerrainType.WATER if random.random() < water_probability else TerrainType.LAND
                )
                row.append(terrain)
            map_grid.append(row)
        return map_grid

    @staticmethod
    def generate_empty_map(width: int = 10, height: int = 10) -> List[List[TerrainType]]:
        """
        Generate an empty map with all land tiles.

        Args:
            width: Width of the map grid (default 10)
            height: Height of the map grid (default 10)

        Returns:
            A 2D grid of TerrainType.LAND
        """
        return [[TerrainType.LAND for _ in range(width)] for _ in range(height)]

    @staticmethod
    def find_random_land_positions(
        map_grid: List[List[TerrainType]],
        count: int = 1,
        excluded_positions: Optional[List[Tuple[int, int]]] = None,
    ) -> List[Tuple[int, int]]:
        """
        Find random positions on land that are not in the excluded list.

        Args:
            map_grid: The map to search for land positions
            count: Number of positions to find (default 1)
            excluded_positions: List of positions to exclude (default None)

        Returns:
            List of (x, y) tuples representing land positions
        """
        if excluded_positions is None:
            excluded_positions = []

        width = len(map_grid[0])
        height = len(map_grid)

        # Get all available land positions
        all_land_positions = []
        for y in range(height):
            for x in range(width):
                if map_grid[y][x] == TerrainType.LAND and (x, y) not in excluded_positions:
                    all_land_positions.append((x, y))

        # Make sure we have enough land positions
        if len(all_land_positions) < count:
            return all_land_positions

        # Randomly select 'count' positions
        return random.sample(all_land_positions, count)

    @staticmethod
    def render_map(
        map_grid: List[List[TerrainType]],
        unit_positions: Optional[dict] = None,
        coin_positions: Optional[List[Tuple[int, int]]] = None,
        unit_colors: Optional[dict] = None,
    ) -> str:
        """
        Render a map as a string with optional units and coins.

        Args:
            map_grid: The map to render
            unit_positions: Dict mapping unit names to (x, y) positions (default None)
            coin_positions: List of (x, y) tuples for coin positions (default None)
            unit_colors: Dict mapping unit names to color codes (default None)

        Returns:
            A string representation of the map
        """
        if unit_positions is None:
            unit_positions = {}
        if coin_positions is None:
            coin_positions = []
        if unit_colors is None:
            unit_colors = {}

        width = len(map_grid[0])
        height = len(map_grid)
        result = []

        # Add a header with column numbers
        header = "  " + "".join(f"{i % 10}" for i in range(width))
        result.append(header)

        # Render map grid in reverse order (start from the highest row number)
        for y in range(height - 1, -1, -1):
            # Add row number at the beginning of each row
            row = f"{y % 10} "

            for x in range(width):
                # Check if there's a unit at this position
                unit_at_pos = None
                for name, pos in unit_positions.items():
                    if pos == (x, y):
                        unit_at_pos = name
                        break

                if unit_at_pos:
                    # This is just for terminal output, colors will be displayed in the frontend
                    row += unit_at_pos
                elif (x, y) in coin_positions:
                    row += "c"
                else:
                    row += map_grid[y][x].value

            result.append(row)

        return "\n".join(result)


if __name__ == "__main__":
    # Example usage
    map_grid = MapGenerator.generate_random_map(10, 10, 0.3)
    land_positions = MapGenerator.find_random_land_positions(map_grid, 2)

    # Create units at land positions
    units = {"A": land_positions[0], "B": land_positions[1]}

    # Create coins
    coin_positions = MapGenerator.find_random_land_positions(
        map_grid, 5, excluded_positions=list(units.values())
    )

    # Render the map
    rendered_map = MapGenerator.render_map(map_grid, units, coin_positions)
    print("Example map:")
    print(rendered_map)
