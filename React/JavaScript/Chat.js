import React, { useState, useEffect, useRef } from 'react';
import EmojiPicker from 'emoji-picker-react';

function Chat({ username, serverIP, apiUrl }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isEmojiPickerOpen, setIsEmojiPickerOpen] = useState(false);
  const [isFormattingOptionsOpen, setIsFormattingOptionsOpen] = useState(false);
  const chatBoxRef = useRef(null);
  const eventSourceRef = useRef(null);
  const emojiPickerRef = useRef(null);

  useEffect(() => {
    eventSourceRef.current = new EventSource(`${apiUrl}/chat`);

    eventSourceRef.current.onmessage = (event) => {
      if (event.data.trim() !== "") {
        const message = JSON.parse(event.data);
        setMessages((prevMessages) => [...prevMessages, message]);
      }
    };

    eventSourceRef.current.onerror = (error) => {
      console.error('EventSource failed:', error);
      eventSourceRef.current.close();
    };

    const handleClickOutside = (event) => {
      if (emojiPickerRef.current && !emojiPickerRef.current.contains(event.target)) {
        setIsEmojiPickerOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [apiUrl]);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim()) {
      alert('Please enter a message.');
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, message: inputMessage }),
      });

      if (response.ok) {
        setInputMessage('');
      } else {
        alert('Failed to send message');
      }
    } catch (error) {
      alert(`An error occurred: ${error.message}`);
    }
  };
  
  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const formatText = (prefix, suffix = prefix) => {
    const textarea = document.getElementById('messageInput');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);

    if (!selectedText) return;

    const formattedText = prefix + selectedText + suffix;
    setInputMessage(
      inputMessage.substring(0, start) + formattedText + inputMessage.substring(end)
    );

    setTimeout(() => {
      textarea.selectionStart = start + prefix.length;
      textarea.selectionEnd = end + prefix.length;
      textarea.focus();
    }, 0);
  };

  const handleEmojiClick = (emojiObject) => {
    setInputMessage(prevMessage => prevMessage + emojiObject.emoji);
  };

  return (
    <div className="section">
      <h1>Chatting on {serverIP} as {username}</h1>
      <div id="chatBox" ref={chatBoxRef}>
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.username === username ? 'sent' : 'received'}`}>
            <span className="username">{message.username}</span>
            <span className="message-content" dangerouslySetInnerHTML={{ __html: message.message }}></span>
            <span className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
      <div className="message-container">
      {isEmojiPickerOpen && (
            <div ref={emojiPickerRef} className="emoji-picker-container">
              <EmojiPicker onEmojiClick={handleEmojiClick} />
            </div>
          )}
        <div className="message-input-wrapper">
          <div className="button-column">
            <button 
              onClick={() => setIsEmojiPickerOpen(!isEmojiPickerOpen)} 
              className="tooltip"
            >
              😊
              <span className="tooltiptext">Insert Emoji</span>
            </button>
            <button 
              onClick={() => setIsFormattingOptionsOpen(!isFormattingOptionsOpen)} 
              className="tooltip"
            >
              &lt;/&gt;
              <span className="tooltiptext">Formatting Options</span>
            </button>
          </div>
          <textarea
            id="messageInput"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message"
          />
          
          {isFormattingOptionsOpen && (
            <div className="formatting-options">
              <button onClick={() => formatText('<b>', '</b>')} className="tooltip">
                <b>B</b>
                <span className="tooltiptext">Bold (Ctrl+B)</span>
              </button>
              <button onClick={() => formatText('<i>', '</i>')} className="tooltip">
                <i>I</i>
                <span className="tooltiptext">Italic (Ctrl+I)</span>
              </button>
              <button onClick={() => formatText('<u>', '</u>')} className="tooltip">
                <u>U</u>
                <span className="tooltiptext">Underline (Ctrl+U)</span>
              </button>
              <button onClick={() => formatText('<s>', '</s>')} className="tooltip">
                <s>S</s>
                <span className="tooltiptext">Strikethrough (Ctrl+S)</span>
              </button>
              <button onClick={() => formatText('<mark>', '</mark>')} className="tooltip">
                <mark>H</mark>
                <span className="tooltiptext">Highlight (Ctrl+H)</span>
              </button>
            </div>
          )}
        </div>
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default Chat;
