# GPT Generals Frontend

A simple frontend for the GPT Generals game that displays the game map and state.

## Setup

1. Install dependencies:
```
npm install
```

2. Build the project:
```
npm run build
```

For development with auto-rebuilding:
```
npm run watch
```

3. Run the frontend:
Open the `index.html` file in your web browser, or serve the directory with a simple HTTP server:
```
npx http-server .
```

## Structure

- `src/models.ts` - Data models matching the game's backend
- `src/api.ts` - API client to fetch game state (currently using mock data)
- `src/renderer.ts` - Responsible for rendering the game map to HTML
- `src/main.ts` - Main application logic, handles polling and updates

## Features

- Displays a grid-based map with land and water tiles
- Shows units and coins on the map
- Updates automatically every second with mock data
- Responsive grid layout
