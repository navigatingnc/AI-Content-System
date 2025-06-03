import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App'; // Assuming App.tsx is the main app component
// You might need to add a global CSS file here if you have one, e.g., import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
