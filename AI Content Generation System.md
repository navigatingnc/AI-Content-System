# AI Content Generation System

A comprehensive platform that leverages free accounts and tokens from major AI providers to build tools and generate content. The system intelligently prioritizes tasks in a queue based on each AI provider's specific competencies.

## Features

- **Task Queue Management**: Submit, prioritize, and track content generation tasks
- **AI Provider Integration**: Leverage free accounts from multiple AI providers
- **Token Management**: Optimize token usage across providers
- **Content Generation**: Generate text, code, images, and more
- **User Management**: Register, authenticate, and manage user roles

## Supported AI Providers

| AI Provider | Primary Competency | Use Cases |
|-------------|-------------------|-----------|
| GPT (OpenAI) | Image generation | Creating visual content, illustrations, graphics |
| MANUS | Project code generation | Building complete software projects, complex coding tasks |
| Claude (Anthropic) | Alternative code generation | Secondary code generation, different coding approaches |
| Grok, Gemini, Perplexity | Prompt generation | Creating optimized prompts for other AI systems |
| Lindy.ai | Meeting tracking | Transcription, summarization, and tracking of meetings |
| Lumenor | Monthly people images | Generating consistent images of people on a monthly basis |

## System Architecture

The system follows a modern microservices architecture with:

- **Backend**: Flask-based API with SQLAlchemy for database operations
- **Frontend**: React with TypeScript, using modern UI components
- **Task Queue**: Redis-based priority queue system
- **Storage**: Efficient content and user data storage

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Redis
- MySQL

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-content-system.git
   cd ai-content-system
   ```

2. Set up the backend:
   ```
   cd backend/ai_content_backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```
   cd frontend/ai_content_frontend
   pnpm install
   ```

4. Configure environment variables:
   - Create a `.env` file in the backend directory with database and Redis connection details
   - Configure AI provider API keys in the admin interface after setup

### Running the Application

1. Start the backend:
   ```
   cd backend/ai_content_backend
   source venv/bin/activate
   python -m src.main
   ```

2. Start the frontend:
   ```
   cd frontend/ai_content_frontend
   pnpm run dev
   ```

3. Access the application at `http://localhost:3000`

## Usage

1. Register an account and log in
2. Add AI provider accounts in the admin interface
3. Create tasks specifying content requirements
4. Monitor task progress in the dashboard
5. View and download generated content

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
