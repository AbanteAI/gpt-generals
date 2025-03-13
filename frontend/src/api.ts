import { GameState, TerrainType, Position, Unit } from './models';

// Default WebSocket server URL
const DEFAULT_WS_URL = 'ws://localhost:8765';

// Class to manage WebSocket connection and game state
export class GameClient {
  private ws: WebSocket | null = null;
  private gameState: GameState | null = null;
  private listeners: ((gameState: GameState) => void)[] = [];
  private connectionListeners: ((connected: boolean) => void)[] = [];
  private isConnected: boolean = false;
  private reconnectTimer: number | null = null;

  // Get the current game state
  public getCurrentGameState(): GameState | null {
    return this.gameState;
  }

  // Subscribe to game state changes
  public subscribeToGameState(callback: (gameState: GameState) => void): () => void {
    this.listeners.push(callback);
    
    // If we already have game state, call the callback immediately
    if (this.gameState) {
      callback(this.gameState);
    }
    
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(cb => cb !== callback);
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
      
      // Check if it's a game state message
      if (data.type === 'game_state') {
        // Convert terrain types from strings to enum values
        const mapGrid = data.map_grid.map((row: string[]) => 
          row.map((cell: string) => cell === 'WATER' ? TerrainType.WATER : TerrainType.LAND)
        );
        
        // Convert unit positions to the expected format
        const units: Record<string, Unit> = {};
        Object.entries(data.units).forEach(([key, value]: [string, any]) => {
          units[key] = {
            name: value.name,
            position: { x: value.position[0], y: value.position[1] }
          };
        });
        
        // Convert coin positions to the expected format
        const coinPositions: Position[] = data.coin_positions.map(
          (pos: [number, number]) => ({ x: pos[0], y: pos[1] })
        );
        
        // Create new game state
        this.gameState = {
          mapGrid,
          units,
          coinPositions,
          turn: data.current_turn
        };
        
        // Notify all listeners
        this.listeners.forEach(listener => listener(this.gameState));
      } else if (data.type === 'error') {
        console.error('Server error:', data.message);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
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
  return new Promise((resolve) => {
    const currentState = gameClient.getCurrentGameState();
    if (currentState) {
      // If we already have state, resolve immediately
      resolve(currentState);
    } else {
      // Otherwise subscribe and wait for the first update
      const unsubscribe = gameClient.subscribeToGameState((state) => {
        unsubscribe();
        resolve(state);
      });
      
      // Ensure we're connected and request state
      if (!gameClient.isConnected) {
        gameClient.connect();
      } else {
        gameClient.requestGameState();
      }
    }
  });
}
