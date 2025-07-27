# Aven AI Chat Frontend

A modern, ChatGPT-style React frontend for the Aven AI assistant. This application provides an intuitive chat interface for users to interact with Aven's financial AI assistant.

## Features

- 🤖 **ChatGPT-like Interface**: Clean, modern chat UI with message bubbles and typing indicators
- 🔒 **Safety First**: Displays guardrail notifications when content filters are triggered
- 📚 **Source Citations**: Shows sources and confidence scores for AI responses
- 🔄 **Real-time Status**: Connection status indicator for backend API
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- ⚡ **Fast & Efficient**: Optimized React components with smooth scrolling and animations

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Aven Rust API backend running on `http://localhost:8080`

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd /Users/shimantobhowmik/Downloads/Projects/aVeN/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables** (optional):
   Create a `.env` file in the frontend directory:
   ```bash
   REACT_APP_API_URL=http://localhost:8080
   ```

## Running the Application

1. **Start the backend API** (in a separate terminal):
   ```bash
   cd ../api
   cargo run
   ```

2. **Start the React development server**:
   ```bash
   npm start
   ```

3. **Open your browser** and navigate to `http://localhost:3000`

## Usage

1. **Chat Interface**: Type your questions in the input field at the bottom
2. **Send Messages**: Press Enter or click the send button
3. **View Responses**: AI responses appear with source citations when available
4. **Safety Features**: Guardrail notifications appear when content filters are triggered
5. **Connection Status**: Monitor the connection status in the top-right corner

### Example Questions

Try asking questions like:
- "What are the benefits of using an Aven credit card?"
- "How do I apply for an Aven card?"
- "What are your current interest rates?"
- "Tell me about Aven's privacy policy"

## API Integration

The frontend communicates with the Rust backend via these endpoints:

- **POST** `/query` - Send chat messages and receive AI responses
- **GET** `/health` - Check API connectivity
- **GET** `/metrics` - View guardrail metrics (optional)

### Request Format
```json
{
  "question": "Your question here"
}
```

### Response Format
```json
{
  "answer": "AI response text",
  "sources": [
    {
      "source": "document_name.txt",
      "score": 0.95
    }
  ],
  "context": "Retrieved context text",
  "guardrail_triggered": null
}
```

## Components

- **App.js** - Main application component with chat logic
- **MessageComponent** - Individual message rendering with markdown support
- **Connection Status** - Real-time API connectivity indicator
- **Typing Indicator** - Shows when AI is generating response

## Styling

- **Modern Design**: Clean, minimal interface inspired by ChatGPT
- **Dark/Light Themes**: Currently uses light theme with option to extend
- **Smooth Animations**: Typing indicators, hover effects, and transitions
- **Mobile First**: Responsive design that works on all screen sizes

## Customization

### Changing Colors
Edit the CSS variables in `App.css`:
```css
/* Primary brand color */
background-color: #4f46e5; /* Change to your brand color */

/* Message bubbles */
.bot-message .message-bubble {
  background-color: white; /* Bot message background */
}

.user-message .message-bubble {
  background-color: #4f46e5; /* User message background */
}
```

### Adding Features
- **Message History**: Implement localStorage to persist conversations
- **File Upload**: Add document upload capability
- **Voice Input**: Integrate speech-to-text functionality
- **Export Chat**: Add functionality to export conversations

## Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Deployment

### Using Nginx
1. Build the application: `npm run build`
2. Copy the `build/` directory to your web server
3. Configure Nginx to serve the static files and proxy API calls

### Using Docker
```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure the Rust backend is running on port 8080
   - Check firewall settings
   - Verify CORS configuration in the backend

2. **Messages Not Sending**
   - Check browser console for errors
   - Verify API endpoint configuration
   - Test backend health endpoint directly

3. **Styling Issues**
   - Clear browser cache
   - Check for CSS conflicts
   - Verify all dependencies are installed

### Development Tools

- **React DevTools**: Browser extension for debugging React components
- **Network Tab**: Monitor API requests and responses
- **Console Logs**: Check for JavaScript errors and API responses

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Aven AI assistant system. Please refer to the main project license for usage terms.

## Support

For issues and questions:
- Create an issue in the project repository
- Contact the development team
- Check the API documentation for backend-related issues
