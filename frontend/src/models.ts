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
