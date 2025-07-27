import axios from 'axios';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    // Handle different error types
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      error.message = 'Unable to connect to the server. Please check if the API is running.';
    } else if (error.response?.status === 500) {
      error.message = 'Server error occurred. Please try again later.';
    } else if (error.response?.status === 429) {
      error.message = 'Too many requests. Please wait a moment before trying again.';
    }
    
    return Promise.reject(error);
  }
);

// API functions
export const apiService = {
  // Send a query to the AI
  sendQuery: async (question) => {
    try {
      console.log('Sending query:', question);
      console.log('API URL:', API_BASE_URL);
      
      const response = await apiClient.post('/query', { question });
      console.log('API Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('API Error Details:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw new Error(error.message || 'Failed to send query');
    }
  },

  // Send a streaming query to the AI
  sendStreamingQuery: async (question, onChunk, onComplete, onError) => {
    try {
      const response = await fetch(`${API_BASE_URL}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '{}') continue; // Empty data
            
            try {
              const parsed = JSON.parse(data);
              
              if (line.includes('event: start')) {
                // Processing started
                continue;
              } else if (line.includes('event: chunk')) {
                onChunk(parsed.chunk);
              } else if (line.includes('event: complete')) {
                onComplete(parsed);
                return;
              } else if (line.includes('event: error')) {
                onError(new Error(parsed.message || 'Streaming error'));
                return;
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', data);
            }
          }
        }
      }
    } catch (error) {
      onError(error);
    }
  },

  // Check API health
  checkHealth: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(error.message || 'Health check failed');
    }
  },

  // Get metrics (optional)
  getMetrics: async () => {
    try {
      const response = await apiClient.get('/metrics');
      return response.data;
    } catch (error) {
      throw new Error(error.message || 'Failed to fetch metrics');
    }
  },
};

// Utility functions
export const utils = {
  // Format timestamp for display
  formatTimestamp: (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  },

  // Generate unique message ID
  generateMessageId: () => {
    return Date.now() + Math.random();
  },

  // Validate message content
  isValidMessage: (message) => {
    return message && typeof message === 'string' && message.trim().length > 0;
  },

  // Truncate long text for display
  truncateText: (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  },

  // Check if running in development mode
  isDevelopment: () => {
    return process.env.NODE_ENV === 'development';
  },
};

export default apiService;
