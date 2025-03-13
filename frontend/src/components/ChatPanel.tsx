import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  List, 
  ListItem, 
  ListItemText,
  Divider
} from '@mui/material';
import { ChatMessage, ChatHistory } from '../models';
import { getChatHistory, sendChatMessage } from '../api';

const MESSAGE_COLORS = {
  player: '#e3f2fd', // Light blue
  system: '#ffebee', // Light red
  unit: '#e8f5e9'    // Light green
};

interface ChatPanelProps {
  playerName?: string;
  height?: string | number;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ 
  playerName = 'Player',
  height = 400
}) => {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch chat history on component mount and every 3 seconds
  useEffect(() => {
    fetchChatHistory();
    
    const interval = setInterval(fetchChatHistory, 3000);
    return () => clearInterval(interval);
  }, []);

  // Scroll to bottom whenever chat history updates
  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const fetchChatHistory = async () => {
    try {
      const history = await getChatHistory();
      setChatHistory(history.messages);
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    try {
      const success = await sendChatMessage(playerName, message, 'player');
      if (success) {
        setMessage('');
        fetchChatHistory(); // Refresh chat history to see the new message
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Paper elevation={3} sx={{ height: height, display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        Chat
      </Typography>
      
      {/* Messages area */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'auto', 
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 1
      }}>
        {chatHistory.length === 0 ? (
          <Typography sx={{ textAlign: 'center', color: 'text.secondary', mt: 2 }}>
            No messages yet. Start the conversation!
          </Typography>
        ) : (
          chatHistory.map((msg, index) => (
            <Paper 
              key={index} 
              elevation={0}
              sx={{ 
                p: 1, 
                backgroundColor: MESSAGE_COLORS[msg.senderType] || '#f5f5f5',
                alignSelf: msg.sender === playerName ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                borderRadius: 2
              }}
            >
              <Typography variant="subtitle2" fontWeight="bold">
                {msg.sender} • {formatTimestamp(msg.timestamp)}
              </Typography>
              <Typography variant="body2">{msg.content}</Typography>
            </Paper>
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>
      
      {/* Message input area */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type a message..."
          size="small"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          sx={{ mr: 1 }}
        />
        <Button 
          variant="contained" 
          onClick={handleSendMessage}
          disabled={!message.trim() || loading}
        >
          Send
        </Button>
      </Box>
    </Paper>
  );
};
