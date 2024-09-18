import React, { useState } from 'react';

function Login({ onLogin }) {
  const [serverIP, setServerIP] = useState('');
  const [username, setUsername] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (serverIP && username) {
      onLogin(username, serverIP);
    } else {
      alert('Please enter both server IP and username.');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div id="loginForm">
      <h2>Welcome to ChatBox</h2>
      <input
        type="text"
        value={serverIP}
        onChange={(e) => setServerIP(e.target.value)}
        placeholder="Enter server IP"
        onKeyDown={handleKeyDown}
      />
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Enter your username"
        onKeyDown={handleKeyDown}
      />
      <button onClick={handleSubmit}>Connect</button>
    </div>
  );
}

export default Login;
