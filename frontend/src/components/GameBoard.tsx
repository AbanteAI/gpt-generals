import React, { useState } from 'react';
import { Box, IconButton, Paper, Grid, Tooltip } from '@mui/material';
import { GameState, TerrainType } from '../models';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ViewInArIcon from '@mui/icons-material/ViewInAr';
import LanguageIcon from '@mui/icons-material/Language';
import { moveUnit } from '../api';
import { keyframes } from '@emotion/react';

// Define animations
const coinRotate = keyframes`
  0% { transform: rotateY(0deg); }
  100% { transform: rotateY(360deg); }
`;

const waterWave = keyframes`
  0% { background-position: 0 0; }
  25% { background-position: 5px 2px; }
  50% { background-position: 10px 0; }
  75% { background-position: 5px -2px; }
  100% { background-position: 0 0; }
`;

const waterWave2 = keyframes`
  0% { background-position: 0 0; }
  25% { background-position: -3px 1px; }
  50% { background-position: -6px 0; }
  75% { background-position: -3px -1px; }
  100% { background-position: 0 0; }
`;

const waterRipple = keyframes`
  0% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 0.5; }
  100% { transform: scale(1); opacity: 0.3; }
`;

const waterShimmer = keyframes`
  0% { opacity: 0.4; }
  50% { opacity: 0.7; }
  100% { opacity: 0.4; }
`;

const waterBubble = keyframes`
  0% { transform: translateY(0) scale(0.1); opacity: 0; }
  20% { opacity: 0.5; }
  80% { opacity: 0.5; }
  100% { transform: translateY(-8px) scale(0.3); opacity: 0; }
`;

const robotHover = keyframes`
  0% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
  100% { transform: translateY(0); }
`;

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
  const [viewMode, setViewMode] = useState<'flat' | 'isometric'>('flat');
  
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
    const clickedUnit = isUnitAtPosition(x, y);
    if (clickedUnit) {
      setSelectedUnit(clickedUnit.name);
    }
  };

  const handleMoveUnit = async (direction: 'up' | 'down' | 'left' | 'right') => {
    if (selectedUnit) {
      await moveUnit(selectedUnit, direction);
    }
  };

  const toggleViewMode = () => {
    setViewMode(viewMode === 'flat' ? 'isometric' : 'flat');
  };

  // Get color for terrain
  const getTerrainColor = (cell: TerrainType) => {
    return cell === TerrainType.WATER ? '#0077BE' : '#8BC34A';
  };
  
  // Create a reversed copy of the map grid to display rows from bottom to top
  const reversedMapGrid = [...mapGrid].reverse();
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, position: 'relative' }}>
      <Box
        data-testid="game-grid"
        sx={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridWidth}, 30px)`,
          gridTemplateRows: `repeat(${gridHeight}, 30px)`,
          gap: viewMode === 'isometric' ? '1px' : '2px',
          backgroundColor: '#ccc',
          padding: '2px',
          border: '1px solid #999',
          transformStyle: 'preserve-3d',
          transform: viewMode === 'isometric' ? 'rotateX(60deg) rotateZ(45deg)' : 'none',
          transformOrigin: 'center center',
          transition: 'transform 0.5s ease',
          perspective: '1000px',
          marginTop: viewMode === 'isometric' ? '50px' : '0',
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
                      ...(viewMode === 'isometric' && {
                        position: 'relative',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        transition: 'all 0.3s ease',
                        '::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: 'rgba(0,0,0,0.1)',
                          transform: 'translateZ(-5px) translateY(5px)',
                          zIndex: -1,
                        }
                      }),
                      ...(isSelected && { 
                        border: '2px solid yellow',
                        boxSizing: 'border-box'
                      }),
                      fontWeight: 'bold',
                      color: unitAtPos ? '#fff' : (hasCoin ? '#000' : undefined),
                      cursor: unitAtPos ? 'pointer' : 'default',
                      
                      // Isometric view water enhancements
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'isometric' && {
                        position: 'relative',
                        overflow: 'hidden',
                        backgroundColor: '#0088cc',
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '-5px',
                          left: '-5px',
                          right: '-5px',
                          bottom: '-5px',
                          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 60%), radial-gradient(circle at 70% 60%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 30%), radial-gradient(circle at 30% 30%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 40%)',
                          backgroundSize: '12px 12px, 15px 15px, 10px 10px',
                          opacity: 0.6,
                          animation: `${waterWave} 6s infinite ease-in-out`,
                          zIndex: 1,
                        },
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'linear-gradient(45deg, transparent 65%, rgba(255,255,255,0.3) 70%, transparent 75%), linear-gradient(135deg, transparent 75%, rgba(255,255,255,0.2) 80%, transparent 85%)',
                          backgroundSize: '15px 15px, 20px 20px',
                          animation: `${waterWave2} 4s infinite ease-in-out`,
                          zIndex: 2,
                        },
                        // Main water body animation with subtle depth gradient
                        animation: `${waterShimmer} 4s infinite ease-in-out`,
                        background: 'linear-gradient(135deg, #0066aa 0%, #0088cc 25%, #00aadd 50%, #0088cc 75%, #0066aa 100%), linear-gradient(to bottom, #00aadd 0%, #0077aa 100%)',
                        backgroundSize: '30px 30px, 100% 100%',
                        backgroundBlendMode: 'overlay',
                        // Pseudo elements for additional visual effects - tiny bubbles
                        '&': {
                          '&:before, &:after': {
                            content: '""',
                            display: 'block',
                            position: 'absolute',
                            width: '4px',
                            height: '4px',
                            borderRadius: '50%',
                            backgroundColor: 'rgba(255, 255, 255, 0.5)',
                            boxShadow: 'rgba(255, 255, 255, 0.3) 10px 5px 0px, rgba(255, 255, 255, 0.4) -5px 10px 0px, rgba(255, 255, 255, 0.3) 5px -5px 0px',
                            animation: `${waterBubble} ${Math.floor(Math.random() * 4) + 6}s infinite ease-out ${Math.floor(Math.random() * 3)}s`,
                            zIndex: 5,
                          }
                        },
                      }),
                      
                      // Regular flat view water styling - improved to match isometric quality
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'flat' && {
                        position: 'relative',
                        overflow: 'hidden',
                        backgroundColor: '#0088cc',
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,0.3) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0.3) 75%, transparent 75%, transparent)',
                          backgroundSize: '10px 10px',
                          animation: `${waterWave} 4s infinite linear`,
                          zIndex: 1,
                        },
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'linear-gradient(-45deg, rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%, transparent)',
                          backgroundSize: '7px 7px',
                          animation: `${waterWave2} 3s infinite linear`,
                          zIndex: 2,
                        },
                        animation: `${waterShimmer} 4s infinite ease-in-out`,
                      }),
                      
                      // Coin animations in isometric view
                      ...(hasCoin && viewMode === 'isometric' && {
                        animation: `${coinRotate} 2s infinite linear`,
                        borderRadius: '50%',
                        boxShadow: '0 0 5px rgba(255, 215, 0, 0.7)',
                        // Replace text 'c' with a circle
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          backgroundColor: '#FFD700',
                          border: '2px solid #B8860B',
                        }
                      }),
                      
                      // Unit styling in isometric view
                      ...(unitAtPos && viewMode === 'isometric' && {
                        animation: `${robotHover} 2s infinite ease-in-out`,
                        // Replace text with a robot shape
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '20px',
                          height: '20px',
                          borderRadius: '2px',
                          backgroundColor: unitAtPos.color,
                          border: '1px solid rgba(0,0,0,0.3)',
                          boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                          zIndex: 1,
                        },
                        // Robot eyes
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '10px',
                          height: '4px',
                          borderRadius: '1px',
                          backgroundColor: 'rgba(255,255,255,0.8)',
                          zIndex: 2,
                          top: '8px',
                        }
                      })
                    }}
                  >
                    {/* Only show text labels in flat view */}
                    {viewMode === 'flat' && (unitAtPos ? unitAtPos.name : (hasCoin ? 'c' : ''))}
                  </Box>
                );
              })}
            </React.Fragment>
          );
        })}
      </Box>

      {/* D-pad control */}
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

      {/* View mode toggle button */}
      <Tooltip title={`Switch to ${viewMode === 'flat' ? 'isometric' : 'flat'} view`}>
        <IconButton 
          onClick={toggleViewMode}
          color="primary"
          sx={{ 
            position: 'fixed', 
            bottom: 16, 
            right: 16,
            backgroundColor: 'white',
            boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
            '&:hover': {
              backgroundColor: '#f5f5f5'
            }
          }}
        >
          {viewMode === 'flat' ? <ViewInArIcon /> : <LanguageIcon />}
        </IconButton>
      </Tooltip>
    </Box>
  );
};
