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
  50% { background-position: 10px 0; }
  100% { background-position: 0 0; }
`;

const robotHover = keyframes`
  0% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-3px) rotate(-1deg); }
  50% { transform: translateY(-4px) rotate(0deg); }
  75% { transform: translateY(-3px) rotate(1deg); }
  100% { transform: translateY(0) rotate(0deg); }
`;

const robotGlow = keyframes`
  0% { box-shadow: 0 0 8px 2px rgba(255, 255, 255, 0.3); }
  50% { box-shadow: 0 0 15px 5px rgba(255, 255, 255, 0.5); }
  100% { box-shadow: 0 0 8px 2px rgba(255, 255, 255, 0.3); }
`;

const antennaBlinking = keyframes`
  0% { opacity: 0.3; }
  25% { opacity: 1; }
  50% { opacity: 0.3; }
  75% { opacity: 0.7; }
  100% { opacity: 0.3; }
`;

const scanLine = keyframes`
  0% { height: 0%; top: 0; opacity: 0.8; }
  80% { height: 100%; top: 0; opacity: 0.8; }
  100% { height: 100%; top: 0; opacity: 0; }
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
                      
                      // Isometric view enhancements
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'isometric' && {
                        animation: `${waterWave} 3s infinite linear`,
                        backgroundImage: 'linear-gradient(45deg, #0077BE 25%, #0099FF 50%, #0077BE 75%)',
                        backgroundSize: '20px 20px',
                      }),
                      
                      // Regular flat view water styling
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'flat' && {
                        backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%, transparent)',
                        backgroundSize: '10px 10px'
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
                      
                      // Enhanced Robot styling in isometric view
                      ...(unitAtPos && viewMode === 'isometric' && {
                        position: 'relative',
                        animation: `${robotHover} 3s infinite ease-in-out`,
                        transformStyle: 'preserve-3d',
                        zIndex: 5,
                        overflow: 'visible',
                        
                        // Robot body - main body piece
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '22px',
                          height: '22px',
                          borderRadius: '4px',
                          backgroundColor: unitAtPos.color,
                          border: '1px solid rgba(0,0,0,0.5)',
                          boxShadow: isSelected 
                            ? `0 0 12px 3px ${unitAtPos.color}` 
                            : '0 3px 6px rgba(0,0,0,0.4)',
                          zIndex: 1,
                          top: '1px',
                          left: '4px',
                          transform: 'rotateX(-20deg) translateZ(2px)',
                          ...(isSelected && {
                            animation: `${robotGlow} 1.5s infinite ease-in-out`
                          })
                        },
                        
                        // Robot head - smaller piece on top
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '14px',
                          height: '10px',
                          top: '-6px',
                          left: '8px',
                          backgroundColor: unitAtPos.color,
                          borderRadius: '3px 3px 0 0',
                          border: '1px solid rgba(0,0,0,0.5)',
                          borderBottom: 'none',
                          boxShadow: '0 -2px 3px rgba(0,0,0,0.2)',
                          zIndex: 2,
                          transform: 'rotateX(-10deg) translateZ(4px)',
                        },
                        
                        // Robot eyes - small glowing indicators
                        '& .robot-eyes': {
                          position: 'absolute',
                          width: '10px',
                          height: '3px',
                          backgroundColor: 'rgba(255,255,255,0.9)',
                          borderRadius: '1px',
                          zIndex: 3,
                          top: '-2px',
                          left: '10px',
                          boxShadow: '0 0 3px rgba(255,255,255,0.8)',
                          transform: 'rotateX(-10deg) translateZ(6px)',
                        },
                        
                        // Left antenna
                        '& .robot-antenna-left': {
                          position: 'absolute',
                          width: '1px',
                          height: '6px',
                          backgroundColor: 'rgba(255,255,255,0.8)',
                          top: '-12px',
                          left: '10px',
                          zIndex: 3,
                          transform: 'rotateX(-10deg) translateZ(4px)',
                          '&::after': {
                            content: '""',
                            position: 'absolute',
                            width: '3px',
                            height: '3px',
                            borderRadius: '50%',
                            backgroundColor: 'red',
                            top: '-3px',
                            left: '-1px',
                            animation: `${antennaBlinking} 1.2s infinite`
                          }
                        },
                        
                        // Right antenna
                        '& .robot-antenna-right': {
                          position: 'absolute',
                          width: '1px',
                          height: '6px',
                          backgroundColor: 'rgba(255,255,255,0.8)',
                          top: '-12px',
                          left: '20px',
                          zIndex: 3,
                          transform: 'rotateX(-10deg) translateZ(4px)',
                          '&::after': {
                            content: '""',
                            position: 'absolute',
                            width: '3px',
                            height: '3px',
                            borderRadius: '50%',
                            backgroundColor: 'blue',
                            top: '-3px',
                            left: '-1px',
                            animation: `${antennaBlinking} 1.5s infinite`
                          }
                        },
                        
                        // Left arm
                        '& .robot-arm-left': {
                          position: 'absolute',
                          width: '3px',
                          height: '13px',
                          backgroundColor: 'rgba(0,0,0,0.6)',
                          top: '6px',
                          left: '1px',
                          zIndex: 0,
                          transform: 'rotate(-20deg)',
                          borderRadius: '1px',
                        },
                        
                        // Right arm
                        '& .robot-arm-right': {
                          position: 'absolute',
                          width: '3px',
                          height: '13px',
                          backgroundColor: 'rgba(0,0,0,0.6)',
                          top: '6px',
                          right: '1px',
                          zIndex: 0,
                          transform: 'rotate(20deg)',
                          borderRadius: '1px',
                        },
                        
                        // Left leg
                        '& .robot-leg-left': {
                          position: 'absolute',
                          width: '4px',
                          height: '10px',
                          backgroundColor: 'rgba(0,0,0,0.7)',
                          bottom: '-4px',
                          left: '7px',
                          zIndex: 0,
                          transform: 'rotate(-5deg)',
                          borderRadius: '0 0 2px 2px',
                        },
                        
                        // Right leg
                        '& .robot-leg-right': {
                          position: 'absolute',
                          width: '4px',
                          height: '10px',
                          backgroundColor: 'rgba(0,0,0,0.7)',
                          bottom: '-4px',
                          right: '7px',
                          zIndex: 0,
                          transform: 'rotate(5deg)',
                          borderRadius: '0 0 2px 2px',
                        },
                        
                        // Scan line effect
                        '& .robot-scan': {
                          position: 'absolute',
                          width: '100%',
                          height: '5%',
                          backgroundColor: 'rgba(255,255,255,0.3)',
                          top: 0,
                          left: 0,
                          zIndex: 4,
                          animation: `${scanLine} 3s infinite`,
                          pointerEvents: 'none',
                        },
                        
                        // Robot name label - ensure it's visible in isometric view
                        '& .robot-name': {
                          position: 'absolute',
                          top: '-20px',
                          left: '50%',
                          transform: 'translateX(-50%) rotateX(0deg)',
                          color: '#FFFFFF',
                          fontSize: '14px',
                          fontWeight: 'bold',
                          textShadow: '0px 0px 3px #000000, 0px 0px 6px #000000',
                          zIndex: 10,
                          fontFamily: '"Orbitron", "Roboto Mono", monospace',
                          letterSpacing: '1px',
                          pointerEvents: 'none',
                        }
                      })
                    }}
                  >
                    {/* Show text labels in flat view */}
                    {viewMode === 'flat' && (unitAtPos ? unitAtPos.name : (hasCoin ? 'c' : ''))}
                    
                    {/* Add robot components in isometric view */}
                    {viewMode === 'isometric' && unitAtPos && (
                      <>
                        <div className="robot-antenna-left" />
                        <div className="robot-antenna-right" />
                        <div className="robot-eyes" />
                        <div className="robot-arm-left" />
                        <div className="robot-arm-right" />
                        <div className="robot-leg-left" />
                        <div className="robot-leg-right" />
                        <div className="robot-scan" />
                        <div className="robot-name">{unitAtPos.name}</div>
                      </>
                    )}
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
