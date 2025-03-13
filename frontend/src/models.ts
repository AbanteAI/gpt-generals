export enum TerrainType {
  LAND = "LAND",
  WATER = "WATER"
}

export interface Position {
  x: number;
  y: number;
}

export interface Unit {
  name: string;
  position: Position;
}

export interface GameState {
  mapGrid: TerrainType[][];
  units: Record<string, Unit>;
  coinPositions: Position[];
  turn: number;
}
