import os
from flask import Flask, render_template, request, redirect, url_for, session, Response, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
from openai import OpenAI
import logging
from logging.handlers import RotatingFileHandler
import bleach
from markdown import markdown
from markupsafe import Markup
import requests
import json

chat2_history = ""

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')

# Configure logging
logging.basicConfig(level=logging.INFO)
file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(file_handler)

# Database configuration
if os.environ.get('DATABASE_URL'):
    # Heroku provides DATABASE_URL, but it needs to be modified for SQLAlchemy
    db_url = os.environ.get('DATABASE_URL')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # Local SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models after initializing db
from models import ChatLog, Reaction

# Hugging Face API configuration
client = OpenAI(
    base_url=os.environ.get('OPENAI_BASE_URL'),
    api_key=os.environ.get('HUGGINGFACE_API_KEY')
)

def sanitize_markdown(content):
    # Convert markdown to HTML
    html = markdown(content)
    # Sanitize the HTML
    allowed_tags = ['p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'code', 'pre']
    allowed_attributes = {'*': ['class']}
    sanitized_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
    return Markup(sanitized_html)

@app.route('/')
def index():
    if 'authenticated' in session and session['authenticated']:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(os.environ.get('PASSWORD_HASH'), password):
            session['authenticated'] = True
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('login'))
    active_chats = ChatLog.query.filter(ChatLog.is_active == True).order_by(ChatLog.created_at).all()
    
    # Sanitize and render markdown for AI responses
    for chat in active_chats:
        if chat.ai_response:
            chat.ai_response = sanitize_markdown(chat.ai_response)
    
    return render_template('chat.html', chats=active_chats)

@app.route('/submit', methods=['GET'])
def submit():
    if 'authenticated' not in session or not session['authenticated']:
        current_app.logger.warning('Unauthenticated user attempted to submit a prompt')
        return redirect(url_for('login'))
    
    prompt = bleach.clean(request.args.get('prompt', ''))
    history = json.loads(bleach.clean(request.args.get('history', '[]')))
    current_app.logger.info(f'User submitted prompt: {prompt}')
    
    # Log user input
    user_chat_log = ChatLog(user_input=prompt, is_active=True)
    db.session.add(user_chat_log)
    db.session.commit()

    def generate():
        with app.app_context():
            try:
                messages = history + [{"role": "user", "content": prompt}]
                chat_completion = client.chat.completions.create(
                    model="tgi",
                    messages=messages,
                    stream=True,
                    max_tokens=100
                )

                full_response = ""
                for message in chat_completion:
                    content = message.choices[0].delta.content
                    if content:
                        full_response += content
                        yield f"data: {content.replace('\n', '<br>')}\n\n"

                # Log AI response
                ai_chat_log = ChatLog(user_input=None, ai_response=full_response, is_active=True, ai_model="Model 1")
                db.session.add(ai_chat_log)
                db.session.commit()
                current_app.logger.info(f'AI response: {full_response}')
                yield f"data: [DONE]{ai_chat_log.id}\n\n"
            except Exception as e:
                current_app.logger.error(f"Error generating response: {str(e)}")
                yield f"data: Error: {str(e)}\n\n"
            finally:
                yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/submit_chat2', methods=['POST'])
def submit_chat2():
    if 'authenticated' not in session or not session['authenticated']:
        current_app.logger.warning('Unauthenticated user attempted to submit a prompt to Chat 2')
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    prompt = bleach.clean(data.get('prompt', ''))
    history = data.get('history', [])

    current_app.logger.info(f'User submitted prompt to Chat 2: {prompt}')
    
    API_URL = os.environ.get('CHAT2_API_URL')
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Prepare the conversation history
    conversation = "Hér má sjá skemmtilegt samtal milli tveggja einstaklinga. \n\nJóna: Hæ, hvað segir þú?\n\nGunnar: Ég segi bara allt gott!\n\n"
    for message in history:
        if message['role'] == 'user':
            conversation += f"Jóna: {message['content']}\n\n"
        else:
            conversation += f"Gunnar: {message['content']}\n\n"
    conversation += f"Jóna: {prompt}\n\nGunnar:"

    payload = {
        "inputs": conversation,
        "parameters": {
            "temperature": 1,
            "max_new_tokens": 30
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_response = response.json()[0]['generated_text']

        print("--- ai_response 1 ---")
        print(ai_response)

        # Remove the conversation prefix from ai_response
        ai_response = ai_response.replace(conversation, "", 1).strip()

        print("--- ai_response 2---")
        print(ai_response)

        # Extract the AI's response
        ai_response = ai_response.split("\n")[0].strip()

        print("--- ai_response 3---")
        print(ai_response)
        
        # Log AI response
        ai_chat_log = ChatLog(user_input=None, ai_response=ai_response, is_active=True, ai_model="Model 2")
        db.session.add(ai_chat_log)
        db.session.commit()
        
        current_app.logger.info(f'AI response from Chat 2: {ai_response}')
        return jsonify({'response': ai_response})
    except Exception as e:
        current_app.logger.error(f"Error generating response for Chat 2: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/react', methods=['POST'])
def react():
    if 'authenticated' not in session or not session['authenticated']:
        app.logger.warning('Unauthenticated user attempted to react to a message')
        return redirect(url_for('login'))
    
    chat_id = int(bleach.clean(request.form['chat_id']))
    emoji = bleach.clean(request.form['emoji'])
    is_ai_message = request.form.get('is_ai_message', 'false') == 'true'
    
    app.logger.info(f'User reacted to chat {chat_id} with emoji {emoji}')
    
    if is_ai_message:
        reaction = Reaction(ai_chat_id=chat_id, emoji=emoji)
    else:
        reaction = Reaction(user_chat_id=chat_id, emoji=emoji)
    
    db.session.add(reaction)
    db.session.commit()
    
    return '', 204

@app.route('/reset', methods=['POST'])
def reset():
    global chat2_history
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('login'))
    
    # Deactivate all active chat logs
    ChatLog.query.filter_by(is_active=True).update({ChatLog.is_active: False})
    db.session.commit()
    
    # Reset Chat 2 history
    chat2_history = ""
    
    return '', 204

if __name__ == '__main__':
    app.run(debug=app.config['FLASK_ENV'] == 'development')