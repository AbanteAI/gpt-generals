import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Alert, Chip } from '@mui/material';
import { GameState } from './models';
import { GameBoard } from './components/GameBoard';
import { gameClient } from './api';

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);

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

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
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
      
      <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
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
    </Container>
  );
};

export default App;
