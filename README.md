# GenAI Assistant

A conversational AI assistant for Redmine project management, built with FastAPI backend and Streamlit frontend.

## Project Overview

The GenAI Assistant is a chatbot that uses OpenAI's GPT-3.5-turbo model to answer Redmine-related queries. It consists of:

- **FastAPI Backend**: Handles API requests and communicates with OpenAI
- **Streamlit Frontend**: Provides a user-friendly chat interface
- **Docker Support**: For easy deployment and scaling

## Architecture

### Backend (FastAPI)

- RESTful API with `/chat` endpoint for processing queries
- OpenAI integration for generating intelligent responses
- Environment variable configuration for API keys
- Error handling and fallback responses

### Frontend (Streamlit)

- Clean, modern chat interface
- Session state management for conversation history
- Responsive design with custom styling
- Clear visual distinction between user and assistant messages

## Setup and Installation

### Prerequisites

- Python 3.10+
- Docker (optional)
- OpenAI API key

### Environment Variables

Create a `.env` file in the project root with:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the FastAPI backend:

```bash
python app.py
```

3. Run the Streamlit frontend:

```bash
cd streamlit_app
streamlit run app.py
```

### Docker Deployment

1. Build the Docker image:

```bash
docker build -t redmine-assistant-api .
```

2. Run the Docker container:

```bash
docker run -p 8080:8080 --env-file .env -d --name redmine-api redmine-assistant-api
```

3. Check container status:

```bash
docker ps
```

4. View logs:

```bash
docker logs redmine-api
```

## API Endpoints

### Root
- **URL**: `/`
- **Method**: GET
- **Response**: Status message

### Health Check
- **URL**: `/health`
- **Method**: GET
- **Response**: `{"status": "healthy"}`

### Chat
- **URL**: `/chat`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "query": "How do I create a new issue in Redmine?",
    "conversation_history": [
      {"role": "user", "content": "previous message"},
      {"role": "assistant", "content": "previous response"}
    ]
  }
  ```
- **Response**:
  ```json
  {
    "response": "To create a new issue in Redmine..."
  }
  ```

## Project Structure

```
.
├── app.py                  # FastAPI backend
├── requirements.txt        # Project dependencies
├── Dockerfile             # Docker configuration
├── .env                   # Environment variables (not in repo)
├── data/                  # Data directory
│   ├── embeddings/        # Vector embeddings
│   ├── outputs/           # Generated outputs
│   └── prompts/           # Prompt templates
├── notebooks/             # Jupyter notebooks for exploration and analysis
├── src/                   # Source code
│   ├── agents/            # Agent implementations
│   ├── handlers/          # Request handlers
│   ├── llm/               # Language model integrations
│   │   └── openai.py      # OpenAI integration
│   ├── models/            # Data models and schemas
│   ├── redmine/           # Redmine API integration
│   ├── databases/         # Database connections
│   └── utils/             # Utility functions
├── streamlit_app/         # Streamlit frontend
    └── app.py             # Streamlit app entry point
├── github/workflows/      # GitHub Actions workflows
```

## Features

- **Context-Aware Responses**: Maintains conversation history for better follow-up responses
- **Error Handling**: Graceful fallback to demo responses if API calls fail
- **Clean UI**: Modern chat interface with clear message distinction
- **Containerization**: Docker support for easy deployment

## Future Enhancements

- Authentication and user management
- Direct integration with Redmine API
- Multi-language support
- Advanced conversation capabilities
- Performance optimizations

## License

[MIT License](LICENSE)