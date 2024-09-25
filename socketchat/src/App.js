import React, { useState} from 'react';
import Login from './Login';
import Chat from './Chat';
import { FileUpload, FileDownload } from './File';
import DarkModeToggle from './DarkModeToggle';
import "./App.css";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [serverIP, setServerIP] = useState('');
  const [apiUrl, setApiUrl] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);

  const handleLogin = (username, serverIP) => {
    setUsername(username);
    setServerIP(serverIP);
    setApiUrl(`http://${serverIP}:12345`);
    setIsLoggedIn(true);
  };

  return (
    <div className={`app-container ${isDarkMode ? 'dark-mode' : ''}`}>
      <DarkModeToggle isDarkMode={isDarkMode} setIsDarkMode={setIsDarkMode} />
      <div className="container">
        {!isLoggedIn ? (
          <Login onLogin={handleLogin} />
        ) : (
          <>
            <Chat username={username} serverIP={serverIP} apiUrl={apiUrl} />
            <FileUpload apiUrl={apiUrl} />
            <FileDownload apiUrl={apiUrl} />
          </>
        )}
      </div>
    </div>
  );
}

export default App;