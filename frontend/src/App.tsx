import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import { GameState } from './models';
import { GameBoard } from './components/GameBoard';
import { getGameState } from './api';

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGameState = async () => {
      try {
        const state = await getGameState();
        setGameState(state);
      } catch (err) {
        setError('Failed to fetch game state');
        console.error(err);
      }
    };

    fetchGameState();
    
    // Set up polling every second
    const intervalId = setInterval(fetchGameState, 1000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        GPT Generals
      </Typography>
      <Typography variant="body1" paragraph>
        A game with LLM-controlled units competing to collect coins.
      </Typography>
      
      <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
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
            <Typography>Loading game state...</Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default App;
