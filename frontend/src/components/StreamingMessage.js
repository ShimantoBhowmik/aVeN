import React from 'react';
import { Bot } from 'lucide-react';
import Sources from './Sources';
import './StreamingMessage.css';

const StreamingMessage = ({ 
  streamedContent, 
  isComplete, 
  sources, 
  guardrailTriggered, 
  timestamp 
}) => {
  return (
    <div className="message bot-message streaming">
      <div className="message-avatar">
        <Bot size={20} />
      </div>
      <div className="message-content">
        <div className="message-bubble">
          <div className="message-text">
            {streamedContent}
            {!isComplete && (
              <span className="streaming-cursor">|</span>
            )}
          </div>
          
          {isComplete && sources && sources.length > 0 && (
            <Sources sources={sources} />
          )}
        </div>
        
        <div className="message-timestamp">
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default StreamingMessage;
