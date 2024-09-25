import React, { useState, useEffect, useRef } from 'react';
import EmojiPicker from 'emoji-picker-react';

function Chat({ username, apiUrl }) {
  const [userMessages, setUserMessages] = useState([]);
  const [aiMessages, setAiMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isEmojiPickerOpen, setIsEmojiPickerOpen] = useState(false);
  const [isFormattingOptionsOpen, setIsFormattingOptionsOpen] = useState(false);
  const [isChatWithAI, setIsChatWithAI] = useState(false);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [loading, setLoading] = useState(false);
  const chatBoxRef = useRef(null);
  const eventSourceRef = useRef(null);
  const emojiPickerRef = useRef(null);
  const lastMessageTimestampRef = useRef(null);

  useEffect(() => {
    eventSourceRef.current = new EventSource(`${apiUrl}/chat`);

    eventSourceRef.current.onmessage = (event) => {
      if (event.data.trim() !== "") {
        const message = JSON.parse(event.data);
          if (message.username !== username && (!lastMessageTimestampRef.current || new Date(message.timestamp) > new Date(lastMessageTimestampRef.current))) {
          if (!isChatWithAI) {
            setUserMessages((prevMessages) => [...prevMessages, message]);
            lastMessageTimestampRef.current = message.timestamp;
          }
        }
      }
    };

    eventSourceRef.current.onerror = (error) => {
      console.error('EventSource failed:', error);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
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
  }, [apiUrl, username, isChatWithAI]);

  useEffect(() => {
    if (isChatWithAI) {
      const fetchModels = async () => {
        try {
          const response = await fetch(`${apiUrl}/api/models`);
          if (response.ok) {
            const data = await response.json();
            //console.log('Fetched models:', data.models); // Log the fetched data
            if (Array.isArray(data.models) && data.models.length > 0) {
              const formattedModels = data.models.map(model => 
                typeof model === 'string' ? { name: model } : model
              );
              setModels(formattedModels);
              setSelectedModel(formattedModels[0].name);
            } else {
              console.error('Invalid models data structure:', data.models);
            }
          } else {
            console.error('Failed to fetch models:', response.statusText);
          }
        } catch (error) {
          console.error('An error occurred while fetching models:', error);
        }
      };
      fetchModels();
    }
  }, [isChatWithAI]);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [isChatWithAI ? aiMessages : userMessages]);

  const sendMessage = async () => {
    if (!inputMessage.trim()) {
      alert('Please enter a message.');
      return;
    }

    const sentMessage = { username, message: inputMessage, timestamp: new Date().toISOString() };

    if (isChatWithAI) {
      if (!selectedModel) {
        alert('Please select a model.');
        return;
      }

      setLoading(true);
      try {
        const response = await fetch(`${apiUrl}/api/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ model: selectedModel, prompt: inputMessage }),
        });

        if (response.ok) {
          const data = await response.json();
          setAiMessages((prevMessages) => [
            ...prevMessages,
            sentMessage,
            { username: selectedModel, message: data.response, timestamp: new Date().toISOString() }
          ]);
          setInputMessage('');
        } else {
          alert('Failed to get response from AI');
        }
      } catch (error) {
        alert(`An error occurred: ${error.message}`);
      } finally {
        setLoading(false);
      }
    } else {
      try {
        const response = await fetch(`${apiUrl}/send-message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(sentMessage),
        });

        if (response.ok) {
          setUserMessages((prevMessages) => [...prevMessages, sentMessage]);
          setInputMessage('');
        } else {
          alert('Failed to send message');
        }
      } catch (error) {
        alert(`An error occurred: ${error.message}`);
      }
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

  const switchToUserChat = () => {
    if (isChatWithAI) {
      setIsChatWithAI(false);
    }
  };

  const switchToAIChat = () => {
    if (!isChatWithAI) {
      setIsChatWithAI(true);
    }
  };

  return (
    <div className="section">
      <div id="modeContainer">
        <div id="chatType">
          <button onClick={switchToUserChat} className={!isChatWithAI ? 'active' : ''}>🧑🏽‍🦱</button>
          <button onClick={switchToAIChat} className={isChatWithAI ? 'active' : ''}>🤖</button>
        </div>
        <div id="chatBox" ref={chatBoxRef}>
          {(isChatWithAI ? aiMessages : userMessages).map((message, index) => (
            <div key={index} className={`message ${message.username === username ? 'sent' : 'received'}`}>
              <span className="username">{message.username}</span>
              <span className="message-content" dangerouslySetInnerHTML={{ __html: message.message }}></span>
              <span className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="message-container">
      {loading && <p>Loading...</p>}
        <div className="message-input-wrapper">
          {isChatWithAI ? (
            <>
              <select 
                value={selectedModel} 
                onChange={(e) => {
                  //console.log('Selected model:', e.target.value);
                  setSelectedModel(e.target.value);
                }} 
                className="model-selector"
              >
                <option value="">Select a model</option>
                {models.map((model) => {
                      //console.log('Rendering model:', model);
                      return <option key={model.id} value={model.name} >
                      {model.name}
                    </option>
                    })}
              </select>
              
            </>
          ) : (
            <>
              {isEmojiPickerOpen && (
                <div ref={emojiPickerRef} className="emoji-picker-container">
                  <EmojiPicker onEmojiClick={handleEmojiClick} />
                </div>
              )}
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
            </>
          )}
          <textarea
            id="messageInput"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message"
          />
        </div>
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default Chat;

