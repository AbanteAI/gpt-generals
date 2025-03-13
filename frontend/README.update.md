# GPT Generals Frontend Update

## What's New
- Migrated from Webpack to Vite for faster development and builds
- Switched from vanilla TypeScript to React with TypeScript
- Implemented Material UI (MUI) for modern UI components
- Maintained the same grid-based map visualization with improved styling
- Updated tests to work with React components
- Kept API separation with improved functional exports

## How to Run the Frontend
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

## Development
- Run tests: `npm test`
- Watch tests: `npm run test:watch`
- The project uses React with TypeScript and MUI components
- The API interface remains separate from the UI components

## Project Structure
- `/src` - Source files
  - `/components` - React components
  - `/tests` - Test files
  - `api.ts` - API functions (same functionality as before)
  - `App.tsx` - Main React application component
  - `main.tsx` - Application entry point
  - `models.ts` - TypeScript interfaces and models
