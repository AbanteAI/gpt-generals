import unittest

from game_engine import GameEngine, TerrainType


class TestGameEngine(unittest.TestCase):
    def test_game_initialization(self):
        """Test that the game initializes with correct dimensions and components."""
        # Create a game with default settings
        game = GameEngine()

        # Check map dimensions
        self.assertEqual(len(game.map_grid), 20)  # height
        self.assertEqual(len(game.map_grid[0]), 20)  # width

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

    def test_unit_movement(self):
        """Test that units can move correctly on the map."""
        # Create a game with a controlled map for predictable testing
        game = GameEngine(width=5, height=5, water_probability=0)  # All land

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
        game = GameEngine(width=5, height=5)

        # Place unit at edge of map
        game.units["A"].position = (0, 0)

        # Try to move left and up (out of bounds)
        self.assertFalse(game.move_unit("A", "left"))
        self.assertFalse(game.move_unit("A", "up"))

        # Position should remain unchanged
        self.assertEqual(game.units["A"].position, (0, 0))

        # Create water at (1, 0) and try to move right into water
        game.map_grid[0][1] = TerrainType.WATER
        self.assertFalse(game.move_unit("A", "right"))
        self.assertEqual(game.units["A"].position, (0, 0))

    def test_coin_collection(self):
        """Test that units can collect coins."""
        game = GameEngine(width=5, height=5, water_probability=0)

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
        game = GameEngine(width=5, height=5)

        # Make a move and advance turn
        game.move_unit("A", "right")
        game.next_turn()

        # Check that history has two states
        self.assertEqual(len(game.history), 2)

        # Check that turn counter is updated in history
        self.assertEqual(game.history[1].turn, 1)

        # Check that unit positions are different in history
        self.assertNotEqual(
            game.history[0].units["A"].position,
            game.history[1].units["A"].position
        )

    def test_map_rendering(self):
        """Test that the map renders correctly."""
        game = GameEngine(width=5, height=5)

        # Set controlled terrain for predictable testing
        for y in range(5):
            for x in range(5):
                game.map_grid[y][x] = TerrainType.LAND

        # Position units and coins at known locations
        game.units["A"].position = (1, 1)
        game.units["B"].position = (3, 3)
        game.coin_positions = [(2, 2), (4, 4)]

        # Create a water tile
        game.map_grid[0][0] = TerrainType.WATER

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
        self.assertEqual(rendered_map[3][4], "C")  # Coin at (2,2)
        self.assertEqual(rendered_map[5][6], "C")  # Coin at (4,4)


if __name__ == "__main__":
    unittest.main()
