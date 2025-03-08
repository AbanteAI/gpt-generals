import unittest

from game_engine import GameEngine, Unit
from map_generator import MapGenerator, TerrainType


class TestGameEngine(unittest.TestCase):
    def test_game_initialization(self):
        """Test that the game initializes with correct dimensions and components."""
        # Create a game with default settings
        game = GameEngine()

        # Check map dimensions
        self.assertEqual(len(game.map_grid), 10)  # height
        self.assertEqual(len(game.map_grid[0]), 10)  # width

        # Check units
        self.assertEqual(len(game.units), 2)
        self.assertIn("A", game.units)
        self.assertIn("B", game.units)

        # Check unit positions are on land
        for unit in game.units.values():
            x, y = unit.position
            self.assertEqual(game.map_grid[y][x], TerrainType.LAND)

        # Check coins
        self.assertEqual(len(game.coin_positions), 5)

        # Check coin positions are on land
        for x, y in game.coin_positions:
            self.assertEqual(game.map_grid[y][x], TerrainType.LAND)

        # Check turn counter and history
        self.assertEqual(game.current_turn, 0)
        self.assertEqual(len(game.history), 1)  # Initial state should be saved

    def test_game_initialization_with_custom_map(self):
        """Test that the game can initialize with a custom map."""
        # Create a custom map (all land)
        custom_map = MapGenerator.generate_empty_map(5, 5)
        
        # Create a game with the custom map
        game = GameEngine(map_grid=custom_map)
        
        # Check map dimensions match the custom map
        self.assertEqual(len(game.map_grid), 5)  # height
        self.assertEqual(len(game.map_grid[0]), 5)  # width
        
        # Check all terrain is land
        for row in game.map_grid:
            for cell in row:
                self.assertEqual(cell, TerrainType.LAND)

    def test_unit_movement(self):
        """Test that units can move correctly on the map."""
        # Create a game with a controlled map for predictable testing
        custom_map = MapGenerator.generate_empty_map(5, 5)
        game = GameEngine(map_grid=custom_map)

        # Force unit positions for testing
        game.units["A"].position = (2, 2)  # Center

        # Move in each direction
        directions = ["up", "right", "down", "left"]
        expected_positions = [(2, 1), (3, 1), (3, 2), (2, 2)]

        for direction, expected_pos in zip(directions, expected_positions, strict=False):
            success = game.move_unit("A", direction)
            self.assertTrue(success)
            self.assertEqual(game.units["A"].position, expected_pos)

    def test_invalid_movement(self):
        """Test that units cannot move into invalid positions."""
        # Create a custom map with water at specific positions
        custom_map = MapGenerator.generate_empty_map(5, 5)
        custom_map[0][1] = TerrainType.WATER  # Water at (1,0)
        
        game = GameEngine(map_grid=custom_map)

        # Clear existing units and place unit at edge of map
        game.units = {"A": Unit(name="A", position=(0, 0))}

        # Try to move left and up (out of bounds)
        self.assertFalse(game.move_unit("A", "left"))
        self.assertFalse(game.move_unit("A", "up"))

        # Position should remain unchanged
        self.assertEqual(game.units["A"].position, (0, 0))

        # Try to move right into water
        self.assertFalse(game.move_unit("A", "right"))
        self.assertEqual(game.units["A"].position, (0, 0))

    def test_coin_collection(self):
        """Test that units can collect coins."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        game = GameEngine(map_grid=custom_map)

        # Clear existing coins and place one at a known location
        game.coin_positions = [(3, 3)]

        # Position unit adjacent to coin
        game.units["A"].position = (2, 3)

        # Move to coin position
        self.assertTrue(game.move_unit("A", "right"))

        # Verify coin was collected
        self.assertEqual(len(game.coin_positions), 0)

    def test_game_history(self):
        """Test that game history is correctly maintained."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        game = GameEngine(map_grid=custom_map)

        # Make a move and advance turn
        game.move_unit("A", "right")
        game.next_turn()

        # Check that history has two states
        self.assertEqual(len(game.history), 2)

        # Check that turn counter is updated in history
        self.assertEqual(game.history[1].turn, 1)

        # Check that unit positions are different in history
        self.assertNotEqual(
            game.history[0].units["A"].position, game.history[1].units["A"].position
        )

    def test_map_rendering(self):
        """Test that the map renders correctly."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        custom_map[0][0] = TerrainType.WATER  # Water at (0,0)
        
        game = GameEngine(map_grid=custom_map)

        # Position units and coins at known locations
        game.units = {
            "A": Unit(name="A", position=(1, 1)),
            "B": Unit(name="B", position=(3, 3))
        }
        game.coin_positions = [(2, 2), (4, 4)]

        # Render map
        rendered_map = game.render_map().split("\n")

        # Check header row
        self.assertTrue(rendered_map[0].startswith("  01234"))

        # Check water tile at (0,0)
        self.assertEqual(rendered_map[1][2], "~")

        # Check units
        self.assertEqual(rendered_map[2][3], "A")  # Unit A at (1,1)
        self.assertEqual(rendered_map[4][5], "B")  # Unit B at (3,3)

        # Check coins
        self.assertEqual(rendered_map[3][4], "c")  # Coin at (2,2)
        self.assertEqual(rendered_map[5][6], "c")  # Coin at (4,4)


if __name__ == "__main__":
    unittest.main()
