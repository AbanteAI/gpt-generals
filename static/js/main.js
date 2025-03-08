document.addEventListener('DOMContentLoaded', function() {
    const gridElement = document.getElementById('grid');
    const chatElement = document.getElementById('chat');
    const commandInput = document.getElementById('command');
    const sendButton = document.getElementById('send-btn');
    
    // Connect to WebSocket server
    const socket = io();
    
    // Handle game state updates
    socket.on('update_game_state', function(data) {
        renderGrid(data);
    });
    
    // Handle chat messages
    socket.on('chat_message', function(data) {
        addChatMessage(data.message);
    });
    
    // Send command when button is clicked or Enter is pressed
    sendButton.addEventListener('click', sendCommand);
    commandInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendCommand();
        }
    });
    
    function sendCommand() {
        const command = commandInput.value.trim();
        if (command) {
            socket.emit('command', command);
            commandInput.value = '';
        }
    }
    
    function renderGrid(gameState) {
        const grid = gameState.grid;
        let html = '';
        
        for (let y = 0; y < grid.length; y++) {
            for (let x = 0; x < grid[y].length; x++) {
                const cell = grid[y][x];
                if (cell === "A" || cell === "B") {
                    html += `<span class="unit-${cell.toLowerCase()}">${cell}</span>`;
                } else if (cell === "r") {
                    html += `<span class="resource">${cell}</span>`;
                } else {
                    html += cell;
                }
            }
            html += '\n';
        }
        
        gridElement.innerHTML = html;
    }
    
    function addChatMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        messageElement.textContent = message;
        chatElement.appendChild(messageElement);
        chatElement.scrollTop = chatElement.scrollHeight;
    }
    
    // Add welcome message
    addChatMessage('Welcome to GPT Generals! Enter commands below.');
});
