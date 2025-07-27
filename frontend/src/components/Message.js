import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, AlertTriangle } from 'lucide-react';
import Sources from './Sources';
import './Message.css';

const Message = ({ message }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-avatar">
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>
      <div className="message-content">
        <div className={`message-bubble ${message.isError ? 'error' : ''}`}>
          <div className="message-text">
            <ReactMarkdown>
              {message.content}
            </ReactMarkdown>
            {message.isStreaming && (
              <span className="streaming-cursor">|</span>
            )}
          </div>
        </div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <Sources sources={message.sources} />
        )}
      </div>
    </div>
  );
};

export default Message;