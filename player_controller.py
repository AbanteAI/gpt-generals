"""
Player controller module for the GPT Generals game.
"""

class PlayerController:
    """
    Controller class for human player input in the GPT Generals game.
    """
    
    def __init__(self, game_engine):
        """
        Initialize the player controller.
        
        Args:
            game_engine: GameEngine instance to control
        """
        self.game_engine = game_engine
        self.direction_map = {
            'w': 'up',
            'a': 'left',
            's': 'down',
            'd': 'right'
        }
        
    def process_input(self, player_input: str) -> bool:
        """
        Process player input and apply it to the game.
        
        Args:
            player_input: Input string in the format "<unit_letter><direction>"
                          e.g., "Aw" to move unit A up
        
        Returns:
            True if the input was valid and the move was successful, False otherwise
        """
        # Validate input format
        if len(player_input) != 2:
            print("Invalid input. Please use format: <unit_letter><direction>")
            return False
            
        unit_name = player_input[0].upper()
        direction_key = player_input[1].lower()
        
        # Check if unit exists
        if unit_name not in self.game_engine.units:
            print(f"Unit '{unit_name}' not found. Available units: {list(self.game_engine.units.keys())}")
            return False
            
        # Check if direction is valid
        if direction_key not in self.direction_map:
            print("Invalid direction. Please use w (up), a (left), s (down), d (right)")
            return False
        
        # Translate wasd to game directions
        direction = self.direction_map[direction_key]
        
        # Try to move the unit
        success = self.game_engine.move_unit(unit_name, direction)
        
        if not success:
            print(f"Move failed. Unit {unit_name} cannot move {direction}.")
        
        return success
