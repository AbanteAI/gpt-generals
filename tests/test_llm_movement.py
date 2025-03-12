import unittest
from unittest.mock import patch

from game_engine import GameEngine
from map_generator import MapGenerator, TerrainType
from simulation import MoveDecision, get_game_state_description, get_unit_move_decision


class TestLLMMovement(unittest.TestCase):
    def setUp(self):
        """Set up a test game with a controlled environment."""
        # Create a simple 5x5 map with all land except one water tile
        self.test_map = MapGenerator.generate_empty_map(5, 5)
        self.test_map[2][2] = TerrainType.WATER  # Water in the center

        # Create a game with this map
        self.game = GameEngine(map_grid=self.test_map, num_coins=3)

        # Override positions for predictable testing
        # Place unit A at (0,0) - top left
        self.game.units["A"].position = (0, 0)
        # Place unit B at (4,4) - bottom right
        self.game.units["B"].position = (4, 4)

        # Place coins at specific positions
        self.game.coin_positions = [(1, 0), (4, 0), (0, 4)]

    def test_move_decision_model(self):
        """Test the MoveDecision Pydantic model."""
        # Create a valid move decision
        move = MoveDecision(direction="up", reasoning="Moving up to collect a coin")
        self.assertEqual(move.direction, "up")
        self.assertEqual(move.reasoning, "Moving up to collect a coin")

        # Test invalid direction
        with self.assertRaises(ValueError):
            MoveDecision(direction="diagonal", reasoning="Invalid direction")

    def test_game_state_description(self):
        """Test the game state description generation."""
        description = get_game_state_description(self.game)

        # Check that the description contains key elements
        self.assertIn("Current Game State:", description)
        self.assertIn("Unit Positions:", description)
        self.assertIn("A at (0, 0)", description)
        self.assertIn("B at (4, 4)", description)
        self.assertIn("Coins: 3 remaining", description)

        # Check that the map rendering is included
        # The map should show water at position (2,2)
        self.assertIn("~", description)

    @patch("simulation.call_openrouter")
    def test_unit_move_decision(self, mock_call_openrouter):
        """Test getting a move decision from the LLM (mocked)."""
        # Mock the LLM response
        mock_decision = MoveDecision(
            direction="right", reasoning="Moving right to collect the coin at (1,0)"
        )
        mock_call_openrouter.return_value = mock_decision

        # Get move decision for unit A
        decision = get_unit_move_decision(self.game, "A")

        # Verify the mock was called with expected arguments
        mock_call_openrouter.assert_called_once()
        args, kwargs = mock_call_openrouter.call_args

        # Check that we're using the right model and unit
        self.assertEqual(kwargs["response_model"], MoveDecision)
        self.assertIn("controlling unit A", kwargs["messages"].messages[-1]["content"])

        # Check the returned decision
        self.assertEqual(decision, mock_decision)
        self.assertEqual(decision.direction, "right")
        self.assertEqual(decision.reasoning, "Moving right to collect the coin at (1,0)")

    @patch("simulation.call_openrouter")
    def test_error_handling(self, mock_call_openrouter):
        """Test error handling when the LLM call fails."""
        # Mock an exception being raised by call_openrouter
        mock_call_openrouter.side_effect = Exception("API error")

        # Get move decision for unit A - should return None but not crash
        decision = get_unit_move_decision(self.game, "A")

        # Check that we handled the error
        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
