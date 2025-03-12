import unittest
from typing import cast
from unittest.mock import MagicMock, patch

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

    @patch("simulation.OpenAI")
    def test_unit_move_decision(self, mock_openai):
        """Test getting a move decision from the LLM (mocked)."""
        # Mock the chat completions create method
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Create a mock response object
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        # Create a mock message with JSON content
        mock_message = MagicMock()
        mock_message.content = (
            '{"direction": "right", "reasoning": "Moving right to collect the coin at (1,0)"}'
        )
        mock_completion.choices = [MagicMock(message=mock_message)]

        # Get move decision for unit A
        decision = get_unit_move_decision(self.game, "A")

        # Verify the mock was called
        mock_client.chat.completions.create.assert_called_once()

        # Check arguments to the create method
        _, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], "openai/gpt-4o-mini")
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})

        # Check that the message contains the expected content
        sent_messages = kwargs["messages"]
        user_message = [m for m in sent_messages if m["role"] == "user"][0]
        self.assertIn(f"controlling unit A", user_message["content"])

        # Check the returned decision
        self.assertIsNotNone(decision)
        move_decision = cast(MoveDecision, decision)
        self.assertEqual(move_decision.direction, "right")
        self.assertEqual(move_decision.reasoning, "Moving right to collect the coin at (1,0)")

    @patch("simulation.OpenAI")
    def test_error_handling(self, mock_openai):
        """Test error handling when the LLM call fails."""
        # Mock the OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        # Get move decision for unit A - should return None but not crash
        decision = get_unit_move_decision(self.game, "A")

        # Check that we handled the error
        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
