# AI Chat Application

This is a Flask-based web application that allows users to interact with two different AI models. The application provides a chat interface where users can send prompts and receive responses from both models simultaneously.

## Features

- Dual chat interface for interacting with two AI models
- Streaming responses for model 1
- User authentication
- Emoji reactions to AI responses
- Markdown rendering for AI responses
- Chat history persistence using SQLAlchemy

## Prerequisites

Before deploying this application, you need to create inference endpoints for both models on HuggingFace:

1. Model 1: Create a standard inference endpoint that supports streaming.
2. Model 2: Create a custom inference endpoint with a custom handler. This model doesn't use streaming.

Make sure you have the endpoint URLs and API keys for both models before proceeding with the installation.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/haffi112/ai-chat-application.git
   cd ai-chat-application
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following content:
   ```
   HUGGINGFACE_API_KEY=your_huggingface_api_key
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   PASSWORD_HASH=your_password_hash
   OPENAI_BASE_URL=your_url_here
   CHAT2_API_URL=your_url_here
   ```
   Replace the placeholder values with your actual API keys, endpoints, and desired configuration.

5. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```
   flask run
   ```

The application should now be running on `http://localhost:5000`.

## Deployment

To deploy the application to a production environment:

1. Set the `FLASK_ENV` variable in the `.env` file to `production`.
2. Use a production-ready web server like Gunicorn:
   ```
   gunicorn app:app
   ```
3. Set up a reverse proxy (e.g., Nginx) to handle incoming requests.
4. Ensure all sensitive information is properly secured and not exposed in the repository.

## Usage

1. Access the application through a web browser.
2. Log in using the password set in the `PASSWORD_HASH` environment variable.
3. Enter prompts in the chat interface to interact with both AI models.
4. Use emoji reactions to respond to AI messages.
5. Click "Byrja upp á nýtt" to reset the chat history.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.