import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Grid, TextField, Button } from '@mui/material';
import { GameState, ChatHistory, ChatMessage } from './models';
import { GameBoard } from './components/GameBoard';
import { ChatPanel } from './components/ChatPanel';
import { getGameState, getChatHistory } from './api';

const App: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playerName, setPlayerName] = useState<string>('Player');
  const [playerNameInput, setPlayerNameInput] = useState<string>('Player');
  const [showNameInput, setShowNameInput] = useState<boolean>(true);

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

  const handleSetPlayerName = () => {
    if (playerNameInput.trim()) {
      setPlayerName(playerNameInput);
      setShowNameInput(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, pb: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        GPT Generals
      </Typography>
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
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
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
                <Typography>Loading game state...</Typography>
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
