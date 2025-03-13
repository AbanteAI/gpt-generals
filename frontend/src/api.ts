import { GameState, TerrainType, Position, Unit, ChatMessage, ChatHistory } from './models';

// Constants
const API_URL = 'http://localhost:8000'; // API base URL (should be updated for production)

// Function to get game state
export async function getGameState(): Promise<GameState> {
  try {
    const response = await fetch(`${API_URL}/state`);
    if (!response.ok) {
      throw new Error('Failed to fetch game state');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching game state:', error);
    // Fallback to mock data if API is unavailable
    return getMockGameState();
  }
}

// Function to get chat history
export async function getChatHistory(): Promise<ChatHistory> {
  try {
    const response = await fetch(`${API_URL}/chat/history`);
    if (!response.ok) {
      throw new Error('Failed to fetch chat history');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching chat history:', error);
    // Fallback to empty chat history if API is unavailable
    return { messages: [] };
  }
}

// Function to send a chat message
export async function sendChatMessage(
  sender: string,
  content: string,
  senderType: 'player' | 'system' | 'unit' = 'player'
): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender,
        content,
        sender_type: senderType,
      }),
    });
    
    return response.ok;
  } catch (error) {
    console.error('Error sending chat message:', error);
    return false;
  }
}

// Function to move a unit
export async function moveUnit(unitName: string, direction: 'up' | 'down' | 'left' | 'right'): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/move`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        unit_name: unitName,
        direction,
      }),
    });
    
    return response.ok;
  } catch (error) {
    console.error('Error moving unit:', error);
    return false;
  }
}

// Mock function to get game state (fallback)
function getMockGameState(): GameState {
  // Generate a mock game state
  const width = 10;
  const height = 10;
  
  // Create a random map with land and water
  const mapGrid: TerrainType[][] = [];
  for (let y = 0; y < height; y++) {
    const row: TerrainType[] = [];
    for (let x = 0; x < width; x++) {
      // 20% chance of water
      row.push(Math.random() < 0.2 ? TerrainType.WATER : TerrainType.LAND);
    }
    mapGrid.push(row);
  }
  
  // Create mock units
  const units: Record<string, Unit> = {
    'A': { name: 'A', position: { x: 1, y: 1 } },
    'B': { name: 'B', position: { x: 8, y: 8 } }
  };
  
  // Create mock coins
  const coinPositions: Position[] = [
    { x: 3, y: 3 },
    { x: 5, y: 7 },
    { x: 7, y: 2 }
  ];
  
  // Create mock game state
  return {
    mapGrid,
    units,
    coinPositions,
    turn: Math.floor(Math.random() * 10) // Random turn number
  };
}

// Mock function to get chat history (for testing)
export function getMockChatHistory(): ChatHistory {
  return {
    messages: [
      {
        sender: 'System',
        content: 'Welcome to GPT Generals!',
        timestamp: Date.now() - 60000,
        senderType: 'system'
      },
      {
        sender: 'Player1',
        content: 'Hello everyone!',
        timestamp: Date.now() - 45000,
        senderType: 'player'
      },
      {
        sender: 'Unit A',
        content: 'I\'m heading to the coin at (3,3)',
        timestamp: Date.now() - 30000,
        senderType: 'unit'
      }
    ]
  };
}
