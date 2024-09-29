from app import db
from datetime import datetime

class ChatLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.Text, nullable=True)
    ai_response = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_model = db.Column(db.String(50), nullable=True)  # New field for AI model name
    user_reactions = db.relationship('Reaction', backref='user_chat', foreign_keys='Reaction.user_chat_id', lazy=True)
    ai_reactions = db.relationship('Reaction', backref='ai_chat', foreign_keys='Reaction.ai_chat_id', lazy=True)

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_chat_id = db.Column(db.Integer, db.ForeignKey('chat_log.id'), nullable=True)
    ai_chat_id = db.Column(db.Integer, db.ForeignKey('chat_log.id'), nullable=True)
    emoji = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)