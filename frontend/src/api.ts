import { GameState, TerrainType, Position, Unit, ChatMessage, ChatHistory } from './models';

// Default WebSocket server URL
const DEFAULT_WS_URL = 'ws://localhost:8765';

// Class to manage WebSocket connection and game state
export class GameClient {
  private ws: WebSocket | null = null;
  private gameState: GameState = {
    mapGrid: [],
    units: {},
    players: {},
    coinPositions: [],
    turn: 0
  };
  private chatHistory: ChatHistory = { messages: [] };
  private gameStateListeners: ((gameState: GameState) => void)[] = [];
  private chatHistoryListeners: ((chatHistory: ChatHistory) => void)[] = [];
  private connectionListeners: ((connected: boolean) => void)[] = [];
  private isConnected: boolean = false;
  private reconnectTimer: number | null = null;

  // Get the current game state
  public getCurrentGameState(): GameState {
    // Return a default empty state if no state is available
    if (!this.gameState) {
      return {
        mapGrid: [],
        units: {},
        players: {},
        coinPositions: [],
        turn: 0
      };
    }
    return this.gameState;
  }

  // Get the current chat history
  public getCurrentChatHistory(): ChatHistory {
    return this.chatHistory;
  }

  // Subscribe to game state changes
  public subscribeToGameState(callback: (gameState: GameState) => void): () => void {
    this.gameStateListeners.push(callback);
    
    // If we already have game state, call the callback immediately
    if (this.gameState) {
      callback(this.gameState);
    }
    
    // Return unsubscribe function
    return () => {
      this.gameStateListeners = this.gameStateListeners.filter(cb => cb !== callback);
    };
  }

  // Subscribe to chat history changes
  public subscribeToChatHistory(callback: (chatHistory: ChatHistory) => void): () => void {
    this.chatHistoryListeners.push(callback);
    
    // Call with current chat history immediately
    callback(this.chatHistory);
    
    // Return unsubscribe function
    return () => {
      this.chatHistoryListeners = this.chatHistoryListeners.filter(cb => cb !== callback);
    };
  }

  // Subscribe to connection state changes
  public subscribeToConnectionState(callback: (connected: boolean) => void): () => void {
    this.connectionListeners.push(callback);
    
    // Call with current state immediately
    callback(this.isConnected);
    
    // Return unsubscribe function
    return () => {
      this.connectionListeners = this.connectionListeners.filter(cb => cb !== callback);
    };
  }
  
  // Public method to check if connection is active
  public isConnectionActive(): boolean {
    return this.isConnected;
  }

  // Connect to WebSocket server
  public connect(url: string = DEFAULT_WS_URL): void {
    // Don't try to connect if already connected
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    
    // Clear any pending reconnect timer
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Create new WebSocket connection
    this.ws = new WebSocket(url);
    
    // Set up event handlers
    this.ws.onopen = this.handleOpen.bind(this);
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onclose = this.handleClose.bind(this);
    this.ws.onerror = this.handleError.bind(this);
  }

  // Request the current game state from the server
  public requestGameState(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('Cannot request game state: WebSocket is not connected');
      return;
    }
    
    const message = {
      command: 'get_state'
    };
    
    this.ws.send(JSON.stringify(message));
  }

  // Send a chat message
  public sendChatMessage(
    sender: string,
    content: string,
    senderType: 'player' | 'system' | 'unit' = 'player'
  ): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        console.error('Cannot send chat message: WebSocket is not connected');
        resolve(false);
        return;
      }
      
      const message = {
        command: 'chat',
        sender,
        content,
        sender_type: senderType
      };
      
      try {
        this.ws.send(JSON.stringify(message));
        
        // Add message to local chat history immediately for responsiveness
        // The server will broadcast this message back to all clients including us
        const newMessage: ChatMessage = {
          sender,
          content,
          timestamp: Date.now(),
          senderType
        };
        
        this.chatHistory = {
          messages: [...this.chatHistory.messages, newMessage]
        };
        
        // Notify listeners
        this.chatHistoryListeners.forEach(listener => listener(this.chatHistory));
        
        resolve(true);
      } catch (error) {
        console.error('Error sending chat message:', error);
        resolve(false);
      }
    });
  }

  // Move a unit
  public moveUnit(unitName: string, direction: 'up' | 'down' | 'left' | 'right'): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        console.error('Cannot move unit: WebSocket is not connected');
        resolve(false);
        return;
      }
      
      const message = {
        command: 'move',
        unit_name: unitName,
        direction
      };
      
      try {
        this.ws.send(JSON.stringify(message));
        resolve(true);
      } catch (error) {
        console.error('Error moving unit:', error);
        resolve(false);
      }
    });
  }

  // Handle WebSocket open event
  private handleOpen(): void {
    console.log('WebSocket connection established');
    this.isConnected = true;
    
    // Notify connection listeners
    this.connectionListeners.forEach(listener => listener(true));
    
    // Request initial game state
    this.requestGameState();
  }

  // Handle WebSocket messages
  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      if (data.type === 'game_state') {
        this.handleGameStateMessage(data);
      } else if (data.type === 'chat_message') {
        this.handleChatMessage(data);
      } else if (data.type === 'error') {
        console.error('Server error:', data.message);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  // Handle game state messages
  private handleGameStateMessage(data: any): void {
    // Convert terrain types from strings to enum values
    const mapGrid = data.map_grid.map((row: string[]) => 
      row.map((cell: string) => cell === 'WATER' ? TerrainType.WATER : TerrainType.LAND)
    );
    
    // Convert unit positions to the expected format
    const units: Record<string, Unit> = {};
    Object.entries(data.units).forEach(([key, value]: [string, any]) => {
      units[key] = {
        name: value.name,
        position: { x: value.position[0], y: value.position[1] },
        player_id: value.player_id || 'p0' // Default to player 0 if not provided
      };
    });
    
    // Convert coin positions to the expected format
    const coinPositions: Position[] = data.coin_positions.map(
      (pos: [number, number]) => ({ x: pos[0], y: pos[1] })
    );
    
    // Convert players or create default players if not provided
    const players = data.players || {
      'p0': { id: 'p0', name: 'Player 1', color: '#F44336' },
      'p1': { id: 'p1', name: 'Player 2', color: '#2196F3' }
    };
    
    // Create new game state
    this.gameState = {
      mapGrid,
      units,
      players,
      coinPositions,
      turn: data.current_turn
    };
    
    // Notify all listeners with the game state
    // Store it in a local variable to avoid null checks in the callback
    const gameState = this.gameState;
    if (gameState) {
      this.gameStateListeners.forEach(listener => listener(gameState));
    }
  }

  // Handle chat messages
  private handleChatMessage(data: any): void {
    const message: ChatMessage = {
      sender: data.sender,
      content: data.content,
      timestamp: data.timestamp ? parseInt(data.timestamp) * 1000 : Date.now(),
      senderType: data.sender_type || 'player'
    };
    
    // Check for duplicates - avoid adding the same message twice
    // This can happen when we send a message and then receive it back from the server
    const isDuplicate = this.chatHistory.messages.some(existingMsg => 
      existingMsg.sender === message.sender && 
      existingMsg.content === message.content &&
      // Allow for a small time difference (5 seconds) for messages that might have been added locally
      Math.abs(existingMsg.timestamp - message.timestamp) < 5000
    );
    
    if (!isDuplicate) {
      // Add to chat history
      this.chatHistory = {
        messages: [...this.chatHistory.messages, message]
      };
      
      // Notify listeners
      this.chatHistoryListeners.forEach(listener => listener(this.chatHistory));
    }
  }

  // Handle WebSocket close event
  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
    this.isConnected = false;
    this.ws = null;
    
    // Notify connection listeners
    this.connectionListeners.forEach(listener => listener(false));
    
    // Schedule reconnect
    this.scheduleReconnect();
  }

  // Handle WebSocket error event
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    // The WebSocket will also trigger onclose after an error, so we handle reconnection there
  }

  // Schedule a reconnection attempt
  private scheduleReconnect(): void {
    if (this.reconnectTimer === null) {
      console.log('Scheduling reconnect in 3 seconds...');
      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 3000);
    }
  }
}

// Create a singleton instance
export const gameClient = new GameClient();

// Connect immediately
gameClient.connect();

// Helper function for components that just want the current game state
export async function getGameState(): Promise<GameState> {
  return new Promise<GameState>((resolve) => {
    // Get current state - this will never be null thanks to our default state implementation
    const currentState = gameClient.getCurrentGameState();
    
    // Check if it's a non-empty state (has at least some content)
    const hasRealContent = currentState.mapGrid.length > 0 || Object.keys(currentState.units).length > 0;
    
    if (hasRealContent) {
      // If we have a meaningful state, resolve immediately
      resolve(currentState);
    } else {
      // Otherwise subscribe and wait for a meaningful update
      const unsubscribe = gameClient.subscribeToGameState((state: GameState) => {
        // Only resolve when we get a non-empty update
        if (state.mapGrid.length > 0) {
          unsubscribe();
          resolve(state);
        }
      });
      
      // Ensure we're connected and request state
      if (!gameClient.isConnectionActive()) {
        gameClient.connect();
      } else {
        gameClient.requestGameState();
      }
      
      // If we're having trouble getting a real state, provide the default state after 5 seconds
      setTimeout(() => {
        unsubscribe();
        resolve(currentState);
      }, 5000);
    }
  });
}

// Helper function to get chat history
export async function getChatHistory(): Promise<ChatHistory> {
  return gameClient.getCurrentChatHistory();
}

// Helper function to send a chat message
export async function sendChatMessage(
  sender: string,
  content: string,
  senderType: 'player' | 'system' | 'unit' = 'player'
): Promise<boolean> {
  return gameClient.sendChatMessage(sender, content, senderType);
}

// Helper function to move a unit
export async function moveUnit(
  unitName: string,
  direction: 'up' | 'down' | 'left' | 'right'
): Promise<boolean> {
  return gameClient.moveUnit(unitName, direction);
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
    'A': { name: 'A', position: { x: 1, y: 1 }, player_id: 'p0' },
    'B': { name: 'B', position: { x: 8, y: 8 }, player_id: 'p1' }
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
    players: {
      'p0': { id: 'p0', name: 'Player 1', color: '#F44336' },
      'p1': { id: 'p1', name: 'Player 2', color: '#2196F3' }
    },
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
