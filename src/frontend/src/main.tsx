/**
 * Frontend Application Entry Point
 * Initializes React 18 root and renders the application with Strict Mode
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Create React root and mount to DOM element with id='root'
// Non-null assertion (!) is safe since index.html guarantees the element exists
ReactDOM.createRoot(document.getElementById('root')!).render(
  // Strict Mode enables additional runtime checks and warnings during development
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
