import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Grid, TextField, Button, Chip, Alert } from '@mui/material';
import { GameState } from './models';
import { GameBoard } from './components/GameBoard';
import { ChatPanel } from './components/ChatPanel';
import { LobbyScreen } from './components/LobbyScreen';
import { gameClient } from './api';

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [playerName, setPlayerName] = useState<string>('Player');
  const [playerNameInput, setPlayerNameInput] = useState<string>('Player');
  const [showNameInput, setShowNameInput] = useState<boolean>(true);
  
  // New state for lobby system
  const [inGame, setInGame] = useState<boolean>(false);
  const [currentRoomId, setCurrentRoomId] = useState<string | null>(null);

  useEffect(() => {
    // Subscribe to game state updates
    const unsubscribeGameState = gameClient.subscribeToGameState((state) => {
      setGameState(state);
      // If we receive a valid game state, we're in a game
      if (state && state.mapGrid.length > 0) {
        setInGame(true);
      }
      // Clear any errors when we get new state
      setError(null);
    });
    
    // Subscribe to connection state updates
    const unsubscribeConnection = gameClient.subscribeToConnectionState((connected) => {
      setIsConnected(connected);
      if (!connected) {
        setError('Connection to server lost. Attempting to reconnect...');
      } else if (error && error.includes('Connection to server lost')) {
        setError(null);
      }
    });
    
    // Subscribe to lobby state updates
    const unsubscribeLobbyState = gameClient.subscribeToLobbyState((lobbyState) => {
      // Check if we're already tracking a specific room
      if (currentRoomId) {
        const currentRoom = lobbyState.rooms.find(room => room.id === currentRoomId);
        
        // If our current room is now in playing state, we're in a game
        if (currentRoom && currentRoom.status === 'playing') {
          setInGame(true);
        }
      } else {
        // Check if we're in any room that's in playing state
        // This handles the case where the host starts a game and we need to join it
        for (const room of lobbyState.rooms) {
          const playerInRoom = room.players.some(player => player.name === playerName);
          if (playerInRoom && room.status === 'playing') {
            // We found a playing room we're in - join it
            setCurrentRoomId(room.id);
            setInGame(true);
            // Request the game state for this room
            gameClient.requestGameState();
            break;
          }
        }
      }
    });
    
    // Request initial lobby state
    if (isConnected) {
      gameClient.requestLobbyState();
    }
    
    // Clean up subscriptions on unmount
    return () => {
      unsubscribeGameState();
      unsubscribeConnection();
      unsubscribeLobbyState();
    };
  }, [error, currentRoomId, isConnected]);

  const handleSetPlayerName = () => {
    if (playerNameInput.trim()) {
      setPlayerName(playerNameInput);
      setShowNameInput(false);
    }
  };
  
  const handleJoinGame = (roomId: string | null) => {
    setCurrentRoomId(roomId);
    setInGame(true);
  };
  
  const handleReturnToLobby = () => {
    setInGame(false);
    setCurrentRoomId(null);
    gameClient.requestLobbyState();
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, pb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h3" component="h1">
          GPT Generals
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {inGame && (
            <Button 
              variant="outlined" 
              color="secondary" 
              onClick={handleReturnToLobby}
            >
              Return to Lobby
            </Button>
          )}
          <Chip 
            label={isConnected ? "Connected" : "Disconnected"} 
            color={isConnected ? "success" : "error"} 
            variant="outlined" 
          />
        </Box>
      </Box>
      
      <Typography variant="body1" paragraph>
        A game with LLM-controlled units competing to collect coins.
      </Typography>
      
      {/* Player name input */}
      {showNameInput && (
        <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Enter your name to start
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField 
              fullWidth 
              size="small" 
              value={playerNameInput}
              onChange={(e) => setPlayerNameInput(e.target.value)}
              label="Your Name"
              onKeyPress={(e) => e.key === 'Enter' && handleSetPlayerName()}
            />
            <Button variant="contained" onClick={handleSetPlayerName}>
              Set Name
            </Button>
          </Box>
        </Paper>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {!showNameInput && (
        inGame ? (
          // Game screen
          <Grid container spacing={3}>
            {/* Game Board Section */}
            <Grid item xs={12} md={7}>
              <Paper elevation={3} sx={{ p: 2 }}>
                {gameState ? (
                  <>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Turn: {gameState.turn}
                    </Typography>
                    <GameBoard gameState={gameState} />
                  </>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography>
                      {isConnected ? "Waiting for game state..." : "Connecting to server..."}
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
            
            {/* Chat Panel Section */}
            <Grid item xs={12} md={5}>
              <ChatPanel 
                playerName={playerName}
                height={500}
              />
            </Grid>
          </Grid>
        ) : (
          // Lobby screen
          <LobbyScreen 
            playerName={playerName}
            onNameChange={setPlayerName}
            onJoinGame={handleJoinGame}
          />
        )
      )}
    </Container>
  );
};

export default App;
