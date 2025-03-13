import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Grid, TextField, Button, Chip, Alert } from '@mui/material';
import { GameState } from './models';
import { GameBoard } from './components/GameBoard';
import { ChatPanel } from './components/ChatPanel';
import { gameClient } from './api';

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [playerName, setPlayerName] = useState<string>('Player');
  const [playerNameInput, setPlayerNameInput] = useState<string>('Player');
  const [showNameInput, setShowNameInput] = useState<boolean>(true);

  useEffect(() => {
    // Subscribe to game state updates
    const unsubscribeGameState = gameClient.subscribeToGameState((state) => {
      setGameState(state);
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
    
    // Clean up subscriptions on unmount
    return () => {
      unsubscribeGameState();
      unsubscribeConnection();
    };
  }, [error]);

  const handleSetPlayerName = () => {
    if (playerNameInput.trim()) {
      setPlayerName(playerNameInput);
      setShowNameInput(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, pb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h3" component="h1">
          GPT Generals
        </Typography>
        <Chip 
          label={isConnected ? "Connected" : "Disconnected"} 
          color={isConnected ? "success" : "error"} 
          variant="outlined" 
        />
      </Box>
      
      <Typography variant="body1" paragraph>
        A game with LLM-controlled units competing to collect coins.
      </Typography>
      
      {/* Player name input */}
      {showNameInput && (
        <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Enter your name to start chatting
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
    </Container>
  );
};

export default App;
