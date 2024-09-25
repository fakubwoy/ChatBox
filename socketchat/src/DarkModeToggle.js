import React from 'react';

function DarkModeToggle({ isDarkMode, setIsDarkMode }) {
  return (
    <div className="toggle-container">
      <label className="toggle-switch">
        <input
          type="checkbox"
          checked={isDarkMode}
          onChange={() => setIsDarkMode(!isDarkMode)}
        />
        <span className="slider"></span>
      </label>
    </div>
  );
}

export default DarkModeToggle;