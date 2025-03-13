import unittest
from unittest.mock import patch

from game_engine import GameEngine
from llm_utils import ParsedResponse
from map_generator import MapGenerator, TerrainType
from simulation import (
    Direction,
    MoveDecision,
    MoveDecisionResponse,
    get_game_state_description,
    get_unit_move_decision,
)


class TestLLMMovement(unittest.TestCase):
    def setUp(self):
        """Set up a test game with a controlled environment."""
        # Create a simple 5x5 map with all land except one water tile
        self.test_map = MapGenerator.generate_empty_map(5, 5)
        self.test_map[2][2] = TerrainType.WATER  # Water in the center

        # Create a game with this map
        self.game = GameEngine(map_grid=self.test_map, num_coins=3)

        # Get player IDs from the game
        self.player1_id = "p0"
        self.player2_id = "p1"

        # Override positions for predictable testing
        # Place unit A at (0,0) - top left
        self.game.units["A"].position = (0, 0)
        self.game.units["A"].player_id = self.player1_id
        # Place unit B at (4,4) - bottom right
        self.game.units["B"].position = (4, 4)
        self.game.units["B"].player_id = self.player2_id

        # Place coins at specific positions
        self.game.coin_positions = [(1, 0), (4, 0), (0, 4)]

    def test_move_decision_model(self):
        """Test the MoveDecision Pydantic model."""
        # Create a valid move decision
        move = MoveDecision(direction=Direction.UP, reasoning="Moving up to collect a coin")
        self.assertEqual(move.direction, Direction.UP)
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

    @patch("simulation.call_openrouter_structured")
    def test_unit_move_decision(self, mock_call_openrouter_structured):
        """Test getting a move decision from the LLM (mocked)."""
        # Create a MoveDecision instance for the mock to return
        move_decision = MoveDecision(
            direction=Direction.RIGHT, reasoning="Moving right to collect the coin at (1,0)"
        )

        # Create a raw response string that would typically be returned
        raw_response = (
            '{"direction": "right", "reasoning": "Moving right to collect the coin at (1,0)"}'
        )

        # Create a ParsedResponse object to return from the mock
        parsed_response = ParsedResponse(parsed=move_decision, raw=raw_response)

        # Set up the mock to return our ParsedResponse
        mock_call_openrouter_structured.return_value = parsed_response

        # Get move decision for unit A
        response = get_unit_move_decision(self.game, "A")

        # Verify the mock was called
        mock_call_openrouter_structured.assert_called_once()

        # Check arguments to the call_openrouter_structured method
        args, kwargs = mock_call_openrouter_structured.call_args
        self.assertEqual(kwargs["model"], "openai/gpt-4o-mini")
        self.assertEqual(kwargs["response_model"], MoveDecision)

        # Check that a message object was passed
        self.assertIn("messages", kwargs)

        # Check the returned decision response
        self.assertIsNotNone(response)
        self.assertIsInstance(response, MoveDecisionResponse)

        # Now that we've confirmed response is not None and is the right type, we can safely use it
        if response is not None:  # This is for the type checker
            self.assertEqual(response.decision.direction, "right")
            self.assertEqual(
                response.decision.reasoning, "Moving right to collect the coin at (1,0)"
            )
            self.assertEqual(response.raw_response, raw_response)

    @patch("simulation.call_openrouter_structured")
    def test_error_handling(self, mock_call_openrouter_structured):
        """Test error handling when the LLM call fails."""
        # Set the mock to raise an exception
        mock_call_openrouter_structured.side_effect = Exception("API error")

        # Get move decision for unit A - should return None but not crash
        response = get_unit_move_decision(self.game, "A")

        # Check that we handled the error
        self.assertIsNone(response)


if __name__ == "__main__":
    unittest.main()
