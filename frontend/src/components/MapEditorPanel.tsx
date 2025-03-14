import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  ToggleButton, 
  ToggleButtonGroup, 
  Button, 
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Fab,
  SelectChangeEvent
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import TerraformIcon from '@mui/icons-material/Terrain';
import CoinsIcon from '@mui/icons-material/MonetizationOn';
import PeopleIcon from '@mui/icons-material/People';
import WaterIcon from '@mui/icons-material/Water';
import LandscapeIcon from '@mui/icons-material/Landscape';
import { TerrainType, Position } from '../models';
import { useAdmin } from '../context/AdminContext';

// Define the props for the component
interface MapEditorPanelProps {
  onPlaceUnit: (position: Position, playerId: string) => void;
  onPlaceCoin: (position: Position) => void;
  onChangeTerrain: (position: Position, terrain: TerrainType) => void;
  playerIds: string[];
}

export const MapEditorPanel: React.FC<MapEditorPanelProps> = ({
  onPlaceUnit,
  onPlaceCoin,
  onChangeTerrain,
  playerIds
}) => {
  const { isAdmin } = useAdmin();
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [mode, setMode] = useState<'unit' | 'coin' | 'terrain'>('unit');
  const [selectedPlayerId, setSelectedPlayerId] = useState<string>(playerIds[0] || '');
  const [selectedTerrain, setSelectedTerrain] = useState<TerrainType>(TerrainType.LAND);

  // Update selected player ID when player IDs change or if current selection is not valid
  useEffect(() => {
    if (playerIds.length > 0 && !playerIds.includes(selectedPlayerId)) {
      setSelectedPlayerId(playerIds[0]);
    }
  }, [playerIds, selectedPlayerId]);

  // If user is not admin, don't render anything
  if (!isAdmin) {
    return null;
  }

  const handleModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newMode: 'unit' | 'coin' | 'terrain' | null,
  ) => {
    if (newMode !== null) {
      setMode(newMode);

      // When mode changes, trigger the appropriate action
      // This will indicate to the GameBoard what editing mode we're in
      if (newMode === 'unit' && selectedPlayerId) {
        // Sending a dummy position that won't be used
        // The actual position will be provided when the user clicks on the board
        onPlaceUnit({ x: -1, y: -1 }, selectedPlayerId);
      } else if (newMode === 'coin') {
        onPlaceCoin({ x: -1, y: -1 });
      } else if (newMode === 'terrain') {
        onChangeTerrain({ x: -1, y: -1 }, selectedTerrain);
      }
    }
  };

  const handlePlayerChange = (event: SelectChangeEvent) => {
    const newPlayerId = event.target.value as string;
    setSelectedPlayerId(newPlayerId);
    
    // Update the current editor mode to use the new player ID
    if (mode === 'unit') {
      onPlaceUnit({ x: -1, y: -1 }, newPlayerId);
    }
  };

  const handleTerrainChange = (event: SelectChangeEvent) => {
    const newTerrain = event.target.value as TerrainType;
    setSelectedTerrain(newTerrain);
    
    // Update the current editor mode to use the new terrain type
    if (mode === 'terrain') {
      onChangeTerrain({ x: -1, y: -1 }, newTerrain);
    }
  };

  const handleActivateEditing = () => {
    // Toggle panel visibility
    const newOpen = !isOpen;
    setIsOpen(newOpen);
    
    // When closing the panel, deactivate editing mode
    if (!newOpen) {
      // Use dummy values to indicate no editing mode is active
      onPlaceCoin({ x: -2, y: -2 }); // This is a signal to reset editing mode
    } else {
      // When opening, activate current mode
      if (mode === 'unit' && selectedPlayerId) {
        onPlaceUnit({ x: -1, y: -1 }, selectedPlayerId);
      } else if (mode === 'coin') {
        onPlaceCoin({ x: -1, y: -1 });
      } else if (mode === 'terrain') {
        onChangeTerrain({ x: -1, y: -1 }, selectedTerrain);
      }
    }
  };

  return (
    <>
      {/* Floating toggle button */}
      <Fab 
        color="primary" 
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleActivateEditing}
      >
        {isOpen ? <CloseIcon /> : <EditIcon />}
      </Fab>

      {/* Editor panel */}
      {isOpen && (
        <Paper
          elevation={3}
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 16,
            width: 300,
            zIndex: 1000,
            p: 2,
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Map Editor</Typography>
            <IconButton size="small" onClick={handleActivateEditing}>
              <CloseIcon />
            </IconButton>
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Mode:
          </Typography>

          <ToggleButtonGroup
            value={mode}
            exclusive
            onChange={handleModeChange}
            fullWidth
            sx={{ mb: 2 }}
          >
            <ToggleButton value="unit">
              <Tooltip title="Place Units">
                <PeopleIcon />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="coin">
              <Tooltip title="Place Coins">
                <CoinsIcon />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="terrain">
              <Tooltip title="Change Terrain">
                <TerraformIcon />
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>

          {mode === 'unit' && (
            <FormControl fullWidth size="small" sx={{ mb: 2 }}>
              <InputLabel id="player-select-label">Player</InputLabel>
              <Select
                labelId="player-select-label"
                value={selectedPlayerId}
                label="Player"
                onChange={handlePlayerChange}
              >
                {playerIds.map((id) => (
                  <MenuItem key={id} value={id}>
                    Player {id.replace('p', '')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {mode === 'terrain' && (
            <FormControl fullWidth size="small" sx={{ mb: 2 }}>
              <InputLabel id="terrain-select-label">Terrain Type</InputLabel>
              <Select
                labelId="terrain-select-label"
                value={selectedTerrain}
                label="Terrain Type"
                onChange={handleTerrainChange}
              >
                <MenuItem value={TerrainType.LAND}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <LandscapeIcon sx={{ mr: 1, color: '#8BC34A' }} />
                    Land
                  </Box>
                </MenuItem>
                <MenuItem value={TerrainType.WATER}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <WaterIcon sx={{ mr: 1, color: '#0077BE' }} />
                    Water
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Click on the game board to place {mode === 'unit' ? 'a unit' : mode === 'coin' ? 'a coin' : 'terrain'}.
          </Typography>

          <Box sx={{ bgcolor: 'background.default', p: 1, borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Map editing is only available to admins. Changes will be applied immediately.
            </Typography>
          </Box>
        </Paper>
      )}
    </>
  );
};
