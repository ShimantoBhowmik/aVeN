import React, { useState, useEffect, useCallback } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';
import './VoiceToText.css';

const VoiceToText = ({ onTranscript, isDisabled = false, className = '' }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [recognition, setRecognition] = useState(null);
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState('');

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';
      recognitionInstance.maxAlternatives = 1;

      recognitionInstance.onstart = () => {
        setIsListening(true);
        setError('');
      };

      recognitionInstance.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcriptPart = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcriptPart;
          } else {
            interimTranscript += transcriptPart;
          }
        }

        const fullTranscript = finalTranscript || interimTranscript;
        setTranscript(fullTranscript);
        
        if (onTranscript) {
          onTranscript(fullTranscript, event.results[event.results.length - 1].isFinal);
        }
      };

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setError(getErrorMessage(event.error));
        setIsListening(false);
      };

      recognitionInstance.onend = () => {
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
      setIsSupported(true);
    } else {
      setIsSupported(false);
      setError('Speech recognition not supported in this browser');
    }
  }, [onTranscript]);

  const getErrorMessage = (error) => {
    switch (error) {
      case 'no-speech':
        return 'No speech detected. Please try again.';
      case 'audio-capture':
        return 'Microphone not accessible. Please check permissions.';
      case 'not-allowed':
        return 'Microphone access denied. Please enable microphone permissions.';
      case 'network':
        return 'Network error occurred. Please check your connection.';
      default:
        return 'Speech recognition error occurred.';
    }
  };

  const startListening = useCallback(() => {
    if (recognition && !isListening && !isDisabled) {
      setTranscript('');
      setError('');
      recognition.start();
    }
  }, [recognition, isListening, isDisabled]);

  const stopListening = useCallback(() => {
    if (recognition && isListening) {
      recognition.stop();
    }
  }, [recognition, isListening]);

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <div className={`voice-to-text-error ${className}`}>
        <AlertCircle size={16} />
        <span>Voice input not supported</span>
      </div>
    );
  }

  return (
    <div className={`voice-to-text ${className}`}>
      <button
        onClick={toggleListening}
        disabled={isDisabled}
        className={`voice-button ${isListening ? 'listening' : ''} ${isDisabled ? 'disabled' : ''}`}
        title={isListening ? 'Stop recording' : 'Start voice input'}
        type="button"
      >
        {isListening ? <MicOff size={18} /> : <Mic size={18} />}
      </button>
      
      {error && (
        <div className="voice-error">
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}
      
      {isListening && (
        <div className="listening-indicator">
          <div className="pulse-ring"></div>
          <span>Listening...</span>
        </div>
      )}
    </div>
  );
};

export default VoiceToText;
