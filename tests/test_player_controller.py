import unittest
from unittest.mock import patch

from game_engine import GameEngine
from map_generator import MapGenerator, TerrainType
from player_controller import PlayerController


class TestPlayerController(unittest.TestCase):
    def setUp(self):
        """Set up a test game with a controlled environment."""
        # Create a simple 5x5 map with all land except one water tile
        self.test_map = MapGenerator.generate_empty_map(5, 5)
        self.test_map[2][2] = TerrainType.WATER  # Water in the center

        # Create a game with this map
        self.game = GameEngine(map_grid=self.test_map, num_coins=2)

        # Override positions for predictable testing
        self.game.units["A"].position = (1, 1)
        self.game.units["B"].position = (3, 3)

        # Place coins at specific positions
        self.game.coin_positions = [(0, 0), (4, 4)]

        # Create the controller with manual mode enabled for testing
        self.controller = PlayerController(self.game, manual_mode=True)

    @patch("builtins.print")
    def test_valid_move(self, mock_print):
        """Test a valid move input."""
        # Move unit A up
        result = self.controller.process_input("Aw")

        # Should return True and update unit position
        self.assertTrue(result)
        self.assertEqual(self.game.units["A"].position, (1, 2))

    @patch("builtins.print")
    def test_invalid_move_water(self, mock_print):
        """Test an invalid move into water."""
        # Position unit A adjacent to water
        self.game.units["A"].position = (2, 1)

        # Try to move up into water
        result = self.controller.process_input("Aw")

        # Should return False and not change position
        self.assertFalse(result)
        self.assertEqual(self.game.units["A"].position, (2, 1))

    @patch("builtins.print")
    def test_invalid_move_out_of_bounds(self, mock_print):
        """Test an invalid move out of bounds."""
        # Position unit A at the edge
        self.game.units["A"].position = (0, 1)

        # Try to move left (out of bounds)
        result = self.controller.process_input("Aa")

        # Should return False and not change position
        self.assertFalse(result)
        self.assertEqual(self.game.units["A"].position, (0, 1))

    @patch("builtins.print")
    def test_invalid_unit(self, mock_print):
        """Test input with invalid unit name."""
        # Try to move a non-existent unit
        result = self.controller.process_input("Cw")

        # Should return False
        self.assertFalse(result)

    @patch("builtins.print")
    def test_invalid_direction(self, mock_print):
        """Test input with invalid direction."""
        # Try to move with invalid direction
        result = self.controller.process_input("Ax")

        # Should return False
        self.assertFalse(result)

    @patch("builtins.print")
    def test_invalid_format(self, mock_print):
        """Test input with invalid format."""
        # Try with too long input
        result = self.controller.process_input("Awx")

        # Should return False
        self.assertFalse(result)

        # Try with too short input
        result = self.controller.process_input("A")

        # Should return False
        self.assertFalse(result)

    @patch("builtins.print")
    def test_collect_coin(self, mock_print):
        """Test collecting a coin."""
        # Position unit adjacent to a coin
        self.game.units["A"].position = (0, 1)
        self.game.coin_positions = [(0, 2)]

        # Move to collect coin
        result = self.controller.process_input("Aw")

        # Should return True, update position, and remove coin
        self.assertTrue(result)
        self.assertEqual(self.game.units["A"].position, (0, 2))
        self.assertEqual(len(self.game.coin_positions), 0)


if __name__ == "__main__":
    unittest.main()
