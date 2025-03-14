export enum TerrainType {
  LAND = "LAND",
  WATER = "WATER"
}

export interface Position {
  x: number;
  y: number;
}

export interface Player {
  id: string;
  name: string;
  color: string;
}

export interface Unit {
  name: string;
  position: Position;
  player_id: string;
}

export interface GameState {
  mapGrid: TerrainType[][];
  units: Record<string, Unit>;
  players: Record<string, Player>;
  coinPositions: Position[];
  turn: number;
}

export interface ChatMessage {
  sender: string;
  content: string;
  timestamp: number;
  senderType: 'player' | 'system' | 'unit';
}

export interface ChatHistory {
  messages: ChatMessage[];
}

// Lobby-related types
export interface GameConfig {
  width: number;
  height: number;
  waterProbability: number;
  numCoins: number;
  unitsPerPlayer: number;
}

export interface GameRoom {
  id: string;
  name: string;
  hostId: string;
  hostName: string;
  players: LobbyPlayer[];
  status: 'waiting' | 'playing' | 'finished';
  createdAt: number;
  gameConfig?: GameConfig;
  visible?: boolean;
}

export interface LobbyPlayer {
  id: string;
  name: string;
  color: string;
  isHost: boolean;
}

export interface LobbyState {
  rooms: GameRoom[];
  currentRoom: GameRoom | null;
}

// Available colors for players to choose from
export const PLAYER_COLORS = [
  '#F44336', // Red
  '#2196F3', // Blue
  '#4CAF50', // Green
  '#FF9800', // Orange
  '#9C27B0', // Purple
  '#00BCD4', // Cyan
  '#FFEB3B', // Yellow
  '#795548', // Brown
  '#607D8B'  // Blue Grey
];
