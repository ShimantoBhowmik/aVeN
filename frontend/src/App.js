import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, CheckCircle } from 'lucide-react';
import Message from './components/Message';
import TypingIndicator from './components/TypingIndicator';
import { apiService, utils } from './utils/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      id: utils.generateMessageId(),
      type: 'bot',
      content: "Hello! I'm Aven AI, your intelligent finance assistant. I can help you with questions about Aven's credit card benefits, application process, and general financial services. How can I assist you today?",
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(null);
  const [connectionError, setConnectionError] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check API connection on mount
  useEffect(() => {
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      const healthData = await apiService.checkHealth();
      setIsConnected(healthData.status === 'healthy');
      setConnectionError('');
    } catch (error) {
      setIsConnected(false);
      setConnectionError(error.message);
      console.error('Health check failed:', error);
    }
  };

  const sendMessage = async (question = inputMessage) => {
    if (!question.trim()) return;

    const userMessage = { 
      id: utils.generateMessageId(),
      type: 'user', 
      content: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputMessage('');

    try {
      const response = await apiService.sendQuery(question);
      
      // Add a streaming message placeholder
      const streamingMessageId = Date.now();
      const streamingMessage = {
        id: streamingMessageId,
        type: 'bot',
        content: '',
        sources: response.sources || [],
        isStreaming: true,
        fullContent: response.answer
      };
      
      setMessages(prev => [...prev, streamingMessage]);
      setIsLoading(false);

      // Simulate streaming by gradually revealing the content
      const words = response.answer.split(' ');
      let currentWordIndex = 0;
      
      const streamInterval = setInterval(() => {
        if (currentWordIndex < words.length) {
          const currentContent = words.slice(0, currentWordIndex + 1).join(' ');
          
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMessageId 
              ? { ...msg, content: currentContent }
              : msg
          ));
          
          currentWordIndex++;
        } else {
          // Streaming complete
          setMessages(prev => prev.map(msg => 
            msg.id === streamingMessageId 
              ? { ...msg, isStreaming: false }
              : msg
          ));
          clearInterval(streamInterval);
        }
      }, 50); // Adjust speed as needed (50ms per word)
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'bot',
        content: 'I apologize, but I encountered an error while processing your question. Please try again or contact support@aven.com if the issue persists.',
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputMessage);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <Bot className="header-icon" />
            <h1>Aven AI</h1>
          </div>
          <div className={`connection-status ${isConnected === null ? 'checking' : isConnected ? 'connected' : 'disconnected'}`}>
            <CheckCircle size={16} />
            <span>
              {isConnected === null ? 'Checking...' : isConnected ? 'Connected' : `Disconnected${connectionError ? `: ${connectionError}` : ''}`}
            </span>
          </div>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about Aven's services..."
            className="message-input"
            rows="1"
            disabled={isLoading || !isConnected}
          />
          <button
            onClick={() => sendMessage(inputMessage)}
            disabled={!inputMessage.trim() || isLoading || !isConnected}
            className="send-button"
          >
            <Send size={20} />
          </button>
        </div>
        <div className="input-footer">
          <span>Aven AI can make mistakes. Please verify important information.</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
