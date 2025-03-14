import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { CssBaseline } from '@mui/material';
import { AdminProvider } from './context/AdminContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CssBaseline />
    <AdminProvider>
      <App />
    </AdminProvider>
  </React.StrictMode>
);
