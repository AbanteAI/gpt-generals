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

        # Check players
        self.assertEqual(len(game.players), 2)
        self.assertIn("p0", game.players)
        self.assertIn("p1", game.players)

        # Check units
        self.assertEqual(len(game.units), 2)
        self.assertIn("A", game.units)
        self.assertIn("B", game.units)

        # Check unit positions are on land
        for unit in game.units.values():
            x, y = unit.position
            self.assertEqual(game.map_grid[y][x], TerrainType.LAND)
            # Check units have a player_id
            self.assertTrue(hasattr(unit, "player_id"))
            self.assertIn(unit.player_id, game.players)

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

        # Get the first unit and its player
        unit_name = "A"
        unit = game.units[unit_name]
        player_id = unit.player_id

        # Force unit positions for testing
        unit.position = (2, 2)  # Center

        # Move in each direction
        directions = ["up", "right", "down", "left"]
        expected_positions = [(2, 3), (3, 3), (3, 2), (2, 2)]

        for direction, expected_pos in zip(directions, expected_positions, strict=False):
            success = game.move_unit(unit_name, direction, player_id)
            self.assertTrue(success)
            self.assertEqual(game.units[unit_name].position, expected_pos)

    def test_invalid_movement(self):
        """Test that units cannot move into invalid positions."""
        # Create a custom map with water at specific positions
        custom_map = MapGenerator.generate_empty_map(5, 5)
        custom_map[0][1] = TerrainType.WATER  # Water at (1,0)

        game = GameEngine(map_grid=custom_map)

        # Add a player
        player_id = game.add_player("Test Player")

        # Clear existing units and place unit at edge of map
        game.units = {"A": Unit(name="A", position=(0, 0), player_id=player_id)}

        # Try to move left and down (out of bounds)
        self.assertFalse(game.move_unit("A", "left", player_id))
        self.assertFalse(game.move_unit("A", "down", player_id))

        # Position should remain unchanged
        self.assertEqual(game.units["A"].position, (0, 0))

        # Try to move right into water
        self.assertFalse(game.move_unit("A", "right", player_id))
        self.assertEqual(game.units["A"].position, (0, 0))

    def test_coin_collection(self):
        """Test that units can collect coins."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        game = GameEngine(map_grid=custom_map)

        # Get the first unit and its player
        unit_name = "A"
        unit = game.units[unit_name]
        player_id = unit.player_id

        # Clear existing coins and place one at a known location
        game.coin_positions = [(3, 3)]

        # Position unit adjacent to coin
        unit.position = (2, 3)

        # Move to coin position
        self.assertTrue(game.move_unit(unit_name, "right", player_id))

        # Verify coin was collected
        self.assertEqual(len(game.coin_positions), 0)

    def test_game_history(self):
        """Test that game history is correctly maintained."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        game = GameEngine(map_grid=custom_map)

        # Get the first unit and its player
        unit_name = "A"
        unit = game.units[unit_name]
        player_id = unit.player_id

        # Position unit A at a location where it can move right
        unit.position = (1, 1)

        # Clear any existing history and save the current state as initial
        game.history.clear()
        game._save_state()

        # Make a move and advance turn
        move_success = game.move_unit(unit_name, "right", player_id)
        self.assertTrue(move_success, "Unit A move right should succeed")
        game.next_turn()

        # Check that history has two states (initial + after move)
        self.assertEqual(len(game.history), 2)

        # Check that turn counter is updated in history
        self.assertEqual(game.history[1].turn, 1)

        # Check that unit positions are different in history
        self.assertNotEqual(
            game.history[0].units[unit_name].position, game.history[1].units[unit_name].position
        )

    def test_map_rendering(self):
        """Test that the map renders correctly."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        custom_map[0][0] = TerrainType.WATER  # Water at (0,0)

        game = GameEngine(map_grid=custom_map)

        # Add two players
        player1_id = game.add_player("Player 1")
        player2_id = game.add_player("Player 2")

        # Position units and coins at known locations
        game.units = {
            "A": Unit(name="A", position=(1, 1), player_id=player1_id),
            "B": Unit(name="B", position=(3, 3), player_id=player2_id),
        }
        game.coin_positions = [(2, 2), (4, 4)]

        # Render map
        rendered_map = game.render_map().split("\n")

        # Check header row
        self.assertTrue(rendered_map[0].startswith("  01234"))

        # With reversed row ordering:
        # Water tile at (0,0) is in the last row now
        self.assertEqual(rendered_map[5][2], "~")

        # Check units - positions are reversed in the rendered map
        self.assertEqual(rendered_map[4][3], "A")  # Unit A at (1,1)
        self.assertEqual(rendered_map[2][5], "B")  # Unit B at (3,3)

        # Check coins - positions are reversed in the rendered map
        self.assertEqual(rendered_map[3][4], "c")  # Coin at (2,2)
        self.assertEqual(rendered_map[1][6], "c")  # Coin at (4,4)

    def test_player_unit_ownership(self):
        """Test that players can only move their own units."""
        custom_map = MapGenerator.generate_empty_map(5, 5)
        game = GameEngine(map_grid=custom_map)

        # Get players
        player1_id = "p0"  # First default player
        player2_id = "p1"  # Second default player

        # Ensure units belong to different players
        unit_a = game.units["A"]
        unit_b = game.units["B"]
        unit_a.player_id = player1_id
        unit_b.player_id = player2_id

        # Position units for testing
        unit_a.position = (1, 1)
        unit_b.position = (3, 3)

        # Player 1 should be able to move their own unit but not player 2's unit
        self.assertTrue(game.move_unit("A", "right", player1_id))
        self.assertFalse(game.move_unit("B", "right", player1_id))

        # Player 2 should be able to move their own unit but not player 1's unit
        self.assertTrue(game.move_unit("B", "left", player2_id))
        self.assertFalse(game.move_unit("A", "up", player2_id))

        # Check final positions
        self.assertEqual(unit_a.position, (2, 1))  # Moved right by player 1
        self.assertEqual(unit_b.position, (2, 3))  # Moved left by player 2


if __name__ == "__main__":
    unittest.main()
