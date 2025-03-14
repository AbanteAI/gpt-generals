import React, { useState } from 'react';
import { Box, IconButton, Paper, Grid } from '@mui/material';
import { GameState, TerrainType, Position } from '../models';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { moveUnit, gameClient } from '../api';
import { MapEditorPanel } from './MapEditorPanel';
import { useAdmin } from '../context/AdminContext';

interface GameBoardProps {
  gameState: GameState;
}

interface UnitAtPosition {
  name: string;
  color: string;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  const { mapGrid, units, players, coinPositions } = gameState;
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<'unit' | 'coin' | 'terrain' | null>(null);
  const [selectedPlayerId, setSelectedPlayerId] = useState<string>('');
  const [selectedTerrain, setSelectedTerrain] = useState<TerrainType>(TerrainType.LAND);
  const { isAdmin } = useAdmin();
  
  // Calculate grid dimensions
  const gridHeight = mapGrid.length;
  const gridWidth = gridHeight > 0 ? mapGrid[0].length : 0;
  
  const isUnitAtPosition = (x: number, y: number): UnitAtPosition | null => {
    for (const unitKey in units) {
      const unit = units[unitKey];
      if (unit.position.x === x && unit.position.y === y) {
        const playerColor = players?.[unit.player_id]?.color || '#F44336'; // Default to red
        return {
          name: unit.name,
          color: playerColor
        };
      }
    }
    return null;
  };
  
  const isCoinAtPosition = (x: number, y: number): boolean => {
    return coinPositions.some(pos => pos.x === x && pos.y === y);
  };

  const handleCellClick = (x: number, y: number) => {
    // If we're in editor mode, handle edits
    if (isAdmin && editorMode) {
      handleEditorAction(x, y);
      return;
    }
    
    // Otherwise, handle normal unit selection
    const clickedUnit = isUnitAtPosition(x, y);
    if (clickedUnit) {
      setSelectedUnit(clickedUnit.name);
    }
  };

  const handleEditorAction = (x: number, y: number) => {
    // Don't process clicks if the position is invalid (used for signaling)
    if (x < 0 || y < 0) return;
    
    // Create a position object
    const position: Position = { x, y };
    
    // Handle different editor modes
    if (editorMode === 'unit' && selectedPlayerId) {
      // Send command to place unit
      placeUnit(position, selectedPlayerId);
    } else if (editorMode === 'coin') {
      // Send command to place coin
      placeCoin(position);
    } else if (editorMode === 'terrain') {
      // Send command to change terrain
      changeTerrain(position, selectedTerrain);
    }
  };

  const placeUnit = async (position: Position, playerId: string) => {
    try {
      // In a real implementation, we would send this to the server
      console.log(`Placing unit at (${position.x}, ${position.y}) for player ${playerId}`);
      // For now, we'll just send a chat message to indicate the action
      await gameClient.sendChatMessage('Admin', `Placed unit at (${position.x}, ${position.y}) for player ${playerId}`, 'system');
      // In a full implementation, we would also request a game state update after placing the unit
    } catch (error) {
      console.error('Error placing unit:', error);
    }
  };

  const placeCoin = async (position: Position) => {
    try {
      // In a real implementation, we would send this to the server
      console.log(`Placing coin at (${position.x}, ${position.y})`);
      // For now, we'll just send a chat message to indicate the action
      await gameClient.sendChatMessage('Admin', `Placed coin at (${position.x}, ${position.y})`, 'system');
      // In a full implementation, we would also request a game state update after placing the coin
    } catch (error) {
      console.error('Error placing coin:', error);
    }
  };

  const changeTerrain = async (position: Position, terrain: TerrainType) => {
    try {
      // In a real implementation, we would send this to the server
      console.log(`Changing terrain at (${position.x}, ${position.y}) to ${terrain}`);
      // For now, we'll just send a chat message to indicate the action
      await gameClient.sendChatMessage('Admin', `Changed terrain at (${position.x}, ${position.y}) to ${terrain}`, 'system');
      // In a full implementation, we would also request a game state update after changing the terrain
    } catch (error) {
      console.error('Error changing terrain:', error);
    }
  };

  const handleMoveUnit = async (direction: 'up' | 'down' | 'left' | 'right') => {
    if (selectedUnit) {
      await moveUnit(selectedUnit, direction);
    }
  };

  // Get color for terrain
  const getTerrainColor = (cell: TerrainType) => {
    return cell === TerrainType.WATER ? '#0077BE' : '#8BC34A';
  };
  
  // Create a reversed copy of the map grid to display rows from bottom to top
  const reversedMapGrid = [...mapGrid].reverse();
  
  // The MapEditorPanel and GameBoard communicate through callback props
  // No need for a separate handler function as the callbacks directly update the state
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, position: 'relative' }}>
      <Box
        data-testid="game-grid"
        sx={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridWidth}, 30px)`,
          gridTemplateRows: `repeat(${gridHeight}, 30px)`,
          gap: '2px',
          backgroundColor: '#ccc',
          padding: '2px',
          border: '1px solid #999',
          cursor: editorMode ? 'crosshair' : 'default', // Change cursor based on editor mode
        }}
      >
        {reversedMapGrid.map((row, reversedY) => {
          // Calculate the actual y position in the original grid
          const y = gridHeight - reversedY - 1;
          
          return (
            // Use React Fragment as a container for each row to maintain grid structure
            <React.Fragment key={`row-${y}`}>
              {row.map((cell, x) => {
                const unitAtPos = isUnitAtPosition(x, y);
                const hasCoin = isCoinAtPosition(x, y);
                const isSelected = unitAtPos && unitAtPos.name === selectedUnit;
                const isWater = cell === TerrainType.WATER;
                
                // Determine the background color with priority: unit > coin > terrain
                let backgroundColor;
                if (unitAtPos) {
                  backgroundColor = unitAtPos.color; // Use player's color for unit
                } else if (hasCoin) {
                  backgroundColor = '#FFC107'; // Yellow for coins
                } else {
                  backgroundColor = getTerrainColor(cell);
                }
                
                return (
                  <Box
                    key={`${x}-${y}`}
                    data-testid={`grid-cell-${x}-${y}`}
                    data-cell-type={unitAtPos ? 'unit' : (hasCoin ? 'coin' : (isWater ? 'water' : 'land'))}
                    onClick={() => handleCellClick(x, y)}
                    sx={{
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor,
                      ...(isSelected && { 
                        border: '2px solid yellow',
                        boxSizing: 'border-box'
                      }),
                      fontWeight: 'bold',
                      color: unitAtPos ? '#fff' : (hasCoin ? '#000' : undefined),
                      cursor: editorMode ? 'crosshair' : (unitAtPos ? 'pointer' : 'default'),
                      // For water, add wave pattern
                      ...(isWater && !unitAtPos && !hasCoin && {
                        backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%, transparent)',
                        backgroundSize: '10px 10px'
                      }),
                      // Highlight cells when in editor mode to indicate they are clickable
                      ...(editorMode && {
                        '&:hover': {
                          outline: '2px solid white',
                          zIndex: 1
                        }
                      })
                    }}
                  >
                    {unitAtPos ? unitAtPos.name : (hasCoin ? 'c' : '')}
                  </Box>
                );
              })}
            </React.Fragment>
          );
        })}
      </Box>

      {/* D-pad control - show only if not in editor mode */}
      {!editorMode && (
        <Paper elevation={3} sx={{ p: 2, width: 'fit-content' }}>
          <Grid container direction="column" alignItems="center" spacing={1}>
            <Grid item>
              <IconButton 
                color="primary" 
                onClick={() => handleMoveUnit('up')}
                disabled={!selectedUnit}
              >
                <ArrowUpwardIcon />
              </IconButton>
            </Grid>
            <Grid item container justifyContent="center" spacing={1}>
              <Grid item>
                <IconButton 
                  color="primary" 
                  onClick={() => handleMoveUnit('left')}
                  disabled={!selectedUnit}
                >
                  <ArrowBackIcon />
                </IconButton>
              </Grid>
              <Grid item>
                <IconButton 
                  color="primary" 
                  onClick={() => handleMoveUnit('down')}
                  disabled={!selectedUnit}
                >
                  <ArrowDownwardIcon />
                </IconButton>
              </Grid>
              <Grid item>
                <IconButton 
                  color="primary" 
                  onClick={() => handleMoveUnit('right')}
                  disabled={!selectedUnit}
                >
                  <ArrowForwardIcon />
                </IconButton>
              </Grid>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Map Editor Panel */}
      <MapEditorPanel 
        onPlaceUnit={(position, playerId) => {
          // Special position values are used for signaling
          if (position.x === -2 && position.y === -2) {
            // Reset editing mode
            setEditorMode(null);
            return;
          }
          
          if (position.x === -1 && position.y === -1) {
            // Just set the mode and player, don't perform the action yet
            setEditorMode('unit');
            setSelectedPlayerId(playerId);
            return;
          }
          
          // Real position - perform the action
          placeUnit(position, playerId);
        }}
        onPlaceCoin={(position) => {
          // Special position values are used for signaling
          if (position.x === -2 && position.y === -2) {
            // Reset editing mode
            setEditorMode(null);
            return;
          }
          
          if (position.x === -1 && position.y === -1) {
            // Just set the mode, don't perform the action yet
            setEditorMode('coin');
            return;
          }
          
          // Real position - perform the action
          placeCoin(position);
        }}
        onChangeTerrain={(position, terrain) => {
          // Special position values are used for signaling
          if (position.x === -2 && position.y === -2) {
            // Reset editing mode
            setEditorMode(null);
            return;
          }
          
          if (position.x === -1 && position.y === -1) {
            // Just set the mode and terrain, don't perform the action yet
            setEditorMode('terrain');
            setSelectedTerrain(terrain);
            return;
          }
          
          // Real position - perform the action
          changeTerrain(position, terrain);
        }}
        playerIds={Object.keys(players)}
      />
    </Box>
  );
};
