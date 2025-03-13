# GPT Generals Frontend

A React-based frontend for the GPT Generals game that displays the game map and state.

## What's New
- Migrated from Webpack to Vite for faster development and builds
- Switched from vanilla TypeScript to React with TypeScript
- Implemented Material UI (MUI) for modern UI components
- Maintained the same grid-based map visualization with improved styling
- Updated tests to work with React components
- Kept API separation with improved functional exports

## Setup and Development

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```
   This will start Vite's development server with hot module replacement at http://localhost:5173

4. Or build for production:
   ```
   npm run build
   ```
   And then preview the production build:
   ```
   npm run preview
   ```

5. Testing:
   - Run tests: `npm test`
   - Watch tests: `npm run test:watch`

## Project Structure
- `/src` - Source files
  - `/components` - React components
  - `/tests` - Test files
  - `api.ts` - API functions for fetching game state (currently using mock data)
  - `App.tsx` - Main React application component
  - `main.tsx` - Application entry point
  - `models.ts` - TypeScript interfaces matching the game's backend

## Features

- Displays a grid-based map with land and water tiles
- Shows units and coins on the map
- Updates automatically every second with mock data
- Modern, responsive UI using Material UI components
- Improved developer experience with Vite's hot module replacement
