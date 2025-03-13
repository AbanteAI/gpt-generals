import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardActions, 
  CardContent, 
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider, 
  FormControl,
  Grid, 
  IconButton,
  InputLabel,
  MenuItem,
  Paper, 
  Select,
  TextField, 
  Typography,
  CircularProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import { gameClient } from '../api';
import { GameRoom, LobbyPlayer, PLAYER_COLORS } from '../models';

interface LobbyScreenProps {
  playerName: string;
  onNameChange: (name: string) => void;
  onJoinGame: (roomId: string | null) => void;
}

export const LobbyScreen: React.FC<LobbyScreenProps> = ({ 
  playerName, 
  onNameChange,
  onJoinGame
}) => {
  const [rooms, setRooms] = useState<GameRoom[]>([]);
  const [currentRoom, setCurrentRoom] = useState<GameRoom | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [openCreateDialog, setOpenCreateDialog] = useState<boolean>(false);
  const [roomName, setRoomName] = useState<string>(`${playerName}'s Room`);
  const [selectedColor, setSelectedColor] = useState<string>(PLAYER_COLORS[0]);
  
  // Load lobby state on component mount and periodically
  useEffect(() => {
    fetchLobbyState();
    const interval = setInterval(fetchLobbyState, 5000);
    
    return () => {
      clearInterval(interval);
    };
  }, []);

  // Update room name when player name changes
  useEffect(() => {
    if (!currentRoom) {
      setRoomName(`${playerName}'s Room`);
    }
  }, [playerName, currentRoom]);

  const fetchLobbyState = async () => {
    try {
      setIsLoading(true);
      await gameClient.requestLobbyState();
      setError(null);
    } catch (err) {
      setError("Failed to fetch lobby state");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Subscribe to lobby state updates
  useEffect(() => {
    const unsubscribe = gameClient.subscribeToLobbyState((lobbyState) => {
      setRooms(lobbyState.rooms);
      
      // Find if player is in any room
      const playerInRoom = lobbyState.rooms.find(room => 
        room.players.some(player => player.name === playerName)
      );
      
      if (playerInRoom) {
        setCurrentRoom(playerInRoom);
      } else {
        setCurrentRoom(null);
      }
    });
    
    return () => {
      unsubscribe();
    };
  }, [playerName]);

  const handleCreateRoom = async () => {
    try {
      setIsLoading(true);
      const success = await gameClient.createRoom(roomName, playerName, selectedColor);
      if (success) {
        setOpenCreateDialog(false);
        fetchLobbyState();
      } else {
        setError("Failed to create room");
      }
    } catch (err) {
      setError("Error creating room");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoinRoom = async (roomId: string) => {
    try {
      setIsLoading(true);
      const success = await gameClient.joinRoom(roomId, playerName, selectedColor);
      if (success) {
        fetchLobbyState();
      } else {
        setError("Failed to join room");
      }
    } catch (err) {
      setError("Error joining room");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLeaveRoom = async () => {
    if (!currentRoom) return;
    
    try {
      setIsLoading(true);
      const success = await gameClient.leaveRoom();
      if (success) {
        fetchLobbyState();
      } else {
        setError("Failed to leave room");
      }
    } catch (err) {
      setError("Error leaving room");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartGame = async () => {
    if (!currentRoom) return;
    
    try {
      setIsLoading(true);
      const success = await gameClient.startGame();
      if (success) {
        // Notify parent component that game is starting
        onJoinGame(currentRoom.id);
      } else {
        setError("Failed to start game");
      }
    } catch (err) {
      setError("Error starting game");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePlayerInfo = async () => {
    try {
      await gameClient.updatePlayerInfo(playerName, selectedColor);
    } catch (err) {
      console.error("Error updating player info:", err);
    }
  };

  // When a user changes their name
  const handleNameChange = (newName: string) => {
    onNameChange(newName);
    handleUpdatePlayerInfo();
  };

  // When a user changes their color
  const handleColorChange = (color: string) => {
    setSelectedColor(color);
    handleUpdatePlayerInfo();
  };

  const renderRoomPlayers = (players: LobbyPlayer[]) => {
    return (
      <Box>
        {players.map((player, index) => (
          <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Box 
              sx={{ 
                width: 16, 
                height: 16, 
                borderRadius: '50%', 
                bgcolor: player.color,
                mr: 1 
              }} 
            />
            <Typography variant="body2">
              {player.name} {player.isHost && "(Host)"}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  };

  // If player is in a room, show the room details and waiting screen
  if (currentRoom) {
    const isHost = currentRoom.players.some(p => p.name === playerName && p.isHost);
    
    return (
      <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Room: {currentRoom.name}
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Players:
          </Typography>
          
          {renderRoomPlayers(currentRoom.players)}
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel id="color-select-label">Your Color</InputLabel>
              <Select
                labelId="color-select-label"
                value={selectedColor}
                label="Your Color"
                onChange={(e) => handleColorChange(e.target.value as string)}
              >
                {PLAYER_COLORS.map((color, idx) => (
                  <MenuItem 
                    key={idx} 
                    value={color}
                    sx={{ 
                      '&.Mui-selected': { backgroundColor: `${color}44` } 
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box 
                        sx={{ 
                          width: 16, 
                          height: 16, 
                          borderRadius: '50%', 
                          bgcolor: color,
                          mr: 1 
                        }} 
                      />
                      <span>Color {idx + 1}</span>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Box>
              <Button 
                variant="outlined" 
                color="secondary" 
                onClick={handleLeaveRoom}
                sx={{ mr: 1 }}
                disabled={isLoading}
              >
                Leave Room
              </Button>
              
              {isHost && (
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleStartGame}
                  disabled={isLoading || currentRoom.players.length === 0}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Start Game'}
                </Button>
              )}
            </Box>
          </Box>
        </Paper>
      </Box>
    );
  }

  // Otherwise show the lobby with available rooms
  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Game Lobby</Typography>
        
        <Box>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setOpenCreateDialog(true)}
            sx={{ mr: 2 }}
          >
            Create Room
          </Button>
          
          <IconButton onClick={fetchLobbyState} disabled={isLoading}>
            {isLoading ? <CircularProgress size={24} /> : <RefreshIcon />}
          </IconButton>
        </Box>
      </Box>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      
      <Box sx={{ mb: 4 }}>
        <Paper elevation={3} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Your Profile</Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Your Name"
                value={playerName}
                onChange={(e) => handleNameChange(e.target.value)}
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel id="color-select-label">Your Color</InputLabel>
                <Select
                  labelId="color-select-label"
                  value={selectedColor}
                  label="Your Color"
                  onChange={(e) => handleColorChange(e.target.value as string)}
                >
                  {PLAYER_COLORS.map((color, idx) => (
                    <MenuItem 
                      key={idx} 
                      value={color}
                      sx={{ 
                        '&.Mui-selected': { backgroundColor: `${color}44` } 
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box 
                          sx={{ 
                            width: 16, 
                            height: 16, 
                            borderRadius: '50%', 
                            bgcolor: color,
                            mr: 1 
                          }} 
                        />
                        <span>Color {idx + 1}</span>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      </Box>
      
      <Typography variant="h5" gutterBottom>
        Available Rooms
      </Typography>
      
      {rooms.length === 0 ? (
        <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="textSecondary">
            No rooms available. Create a new room to start playing!
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {rooms.map((room) => (
            <Grid item xs={12} sm={6} md={4} key={room.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {room.name}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Host: {room.hostName}
                  </Typography>
                  
                  <Typography variant="body2" gutterBottom>
                    Players: {room.players.length}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary">
                    Status: {room.status.charAt(0).toUpperCase() + room.status.slice(1)}
                  </Typography>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  {renderRoomPlayers(room.players)}
                </CardContent>
                
                <CardActions>
                  <Button 
                    fullWidth 
                    variant="contained" 
                    color="primary"
                    onClick={() => handleJoinRoom(room.id)}
                    disabled={isLoading || room.status !== 'waiting'}
                  >
                    {room.status === 'waiting' ? 'Join Room' : 'Game in Progress'}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* Create Room Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)}>
        <DialogTitle>Create New Room</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Room Name"
            fullWidth
            variant="outlined"
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateRoom} 
            variant="contained" 
            disabled={isLoading || !roomName.trim()}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
