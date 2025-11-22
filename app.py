"""
Fixed Flask app (app.py) — improvements made:
- get_stored_history now filters by character_id and orders by id asc
- extract_characters inserts characters one-by-one and returns reliable IDs
- robust JSON extraction using regex and safe parsing
- improved error handling, input validation, and resource cleanup
- history truncation preserves chronological order and respects token budget
- safer construction of messages for the chat model
- added simple Dockerfile and Procfile as comments at the bottom for easy deployment (Render/Railway)

Notes:
- Replace ChatGroq invocation as needed depending on the library signature. The code keeps using HumanMessage/AIMessage.
- This file contains the main Flask app. See bottom comments for Dockerfile and Procfile contents.
"""

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from pydantic import BaseModel, Field
import os
import sqlite3
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import json
import re
import logging
import tempfile
from contextlib import closing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api = os.getenv("GROQ_API_KEY", "")
if not api:
    raise ValueError("GROQ_API_KEY environment variable not set")

# instantiate chat client - using currently supported model (Nov 2025)
chat = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7, api_key=api)

app = Flask(__name__)
CORS(app)
DB_PATH = os.getenv('SQLITE_PATH', 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS books
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS characters
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, name TEXT, traits TEXT,
                      FOREIGN KEY (book_id) REFERENCES books (id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, character_id INTEGER,
                      content TEXT, is_user INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (character_id) REFERENCES characters (id))''')
        conn.commit()
    logger.info("Database initialized successfully.")


with app.app_context():
    init_db()


class EmotionOutput(BaseModel):
    anger: int = Field(default=0, description="Anger level (1-5)")
    sadness: int = Field(default=0, description="Sadness level (1-5)")
    joy: int = Field(default=0, description="Joy level (1-5)")


parameter_prompt_template = PromptTemplate(
    input_variables=["traits", "message", "past_history"],
    template="""
You are simulating a character with traits: {traits}.
Given the past conversation history:
{past_history}

And the user's current message: "{message}"

Using Dorner's Psi Theory, determine the following psychological parameters on a scale of 1 to 7:
1. Valence Level: Attraction (positive) vs. aversion (negative).
2. Arousal Level: Readiness for action.
3. Selection Threshold: Ease of shifting between intentions.
4. Resolution Level: Accuracy of perception.
5. Goal-Directedness: Stability of motives.
6. Securing Rate: Frequency of environmental checks.

Return a JSON object:
{{
  "valence": <value>,
  "arousal": <value>,
  "selection_threshold": <value>,
  "resolution": <value>,
  "goal_directedness": <value>,
  "securing_rate": <value>
}}
"""
)

emotion_prompt_template = PromptTemplate(
    input_variables=["traits", "message", "valence", "arousal", "selection_threshold", "resolution", "goal_directedness", "securing_rate"],
    template="""
You are simulating a character with traits: {traits}.

Given the psychological parameters:
Valence Level: {valence}
Arousal Level: {arousal}
Selection Threshold: {selection_threshold}
Resolution Level: {resolution}
Goal-Directedness: {goal_directedness}
Securing Rate: {securing_rate}

And the user's message: "{message}"

Determine the anger, sadness, and joy levels on a scale of 1 to 5 based on Dorner's Psi Theory:
- Anger: Negative valence, high arousal, low resolution, high selection threshold, goal redirection.
- Sadness: Negative valence, low arousal, decreased action-readiness, increased affiliation demand.
- Joy: Positive valence, moderate to high arousal, high goal-directedness, low securing rate.

Return a JSON object:
{{"anger": <anger_level>, "sadness": <sadness_level>, "joy": <joy_level>}}
"""
)

response_prompt_template = PromptTemplate(
    input_variables=["name", "traits", "past_history", "anger", "sadness", "joy"],
    template="""
You are {name}, a character with these traits: {traits}.
Stay true to your identity and traits in your response. Reflect your current emotional state subtly without mentioning emotions explicitly.

Past conversation history: 
{past_history}

Current emotional state: Anger - {anger}/5, Sadness - {sadness}/5, Joy - {joy}/5.

Respond to the current conversation, keeping your traits and past history in mind.
"""
)


def get_stored_history(character_id: int, limit: int = 200):
    """Fetch messages for a specific character ordered chronologically."""
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT content, is_user FROM messages WHERE character_id = ? ORDER BY id ASC LIMIT ?",
            (character_id, limit),
        )
        rows = c.fetchall()
    return [{'content': row['content'], 'is_user': bool(row['is_user'])} for row in rows]


def store_message(user_id, character_id, content, is_user: bool):
    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (user_id, character_id, content, is_user) VALUES (?, ?, ?, ?)",
            (user_id, character_id, content, int(is_user)),
        )
        conn.commit()


def estimate_tokens(text: str) -> int:
    # crude token estimate; replace with tiktoken-based count if available
    return max(1, len(text) // 4)


def truncate_history(history, max_tokens=5000):
    # history assumed chronological [oldest ... newest]
    truncated = []
    total_tokens = 0
    for msg in reversed(history):  # start from newest and include until token budget
        msg_str = f"User: {msg['content']}" if msg['is_user'] else f"Character: {msg['content']}"
        msg_tokens = estimate_tokens(msg_str)
        if total_tokens + msg_tokens > max_tokens:
            break
        truncated.insert(0, msg)
        total_tokens += msg_tokens
    return truncated


def convert_to_langchain_messages(session_history, name):
    messages = []
    for msg in session_history:
        if msg.get('is_user'):
            messages.append(HumanMessage(content=msg.get('content')))
        else:
            messages.append(AIMessage(content=msg.get('content'), name=name))
    return messages


@app.route('/')
def index():
    return jsonify({'message': 'Hello, world!'})


@app.route('/extract_characters', methods=['POST'])
def extract_characters():
    if 'file' not in request.files:
        logger.error("No file provided.")
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        logger.error("Only PDF files are supported.")
        return jsonify({'error': 'Only PDF files are supported'}), 400

    # Save to a secure temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        temp_path = tmp.name
        file.save(temp_path)

    try:
        loader = PyPDFLoader(temp_path)
        pages = loader.load()
        text = "\n".join([page.page_content for page in pages])

        # Limit large uploads and sanitize
        max_chars = 15000
        prompt_text = text[:max_chars]

        prompt = f"Extract all characters from the following text and provide their names and key traits:\n\n{prompt_text}"
        response = chat.invoke(prompt)

        # parse lines like: Name: traits
        lines = (response.content or "").split('\n')
        characters = []
        for line in lines:
            if line.strip():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    name = parts[0].strip().split('.', 1)[-1].strip()
                    traits = parts[1].strip()
                    characters.append({'name': name, 'traits': traits})

        if not characters:
            # fallback: attempt to parse JSON body
            match = re.search(r"(\[\{[\s\S]*\}\])", response.content or "")
            if match:
                try:
                    characters = json.loads(match.group(1))
                except Exception:
                    characters = []

        # Insert book and characters into DB reliably
        book_title = request.form.get('book_title', file.filename.rsplit('.', 1)[0])
        with closing(get_db_connection()) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO books (title) VALUES (?)", (book_title,))
            book_id = c.lastrowid
            inserted = []
            for char in characters:
                c.execute("INSERT INTO characters (book_id, name, traits) VALUES (?, ?, ?)",
                          (book_id, char['name'], char['traits']))
                inserted.append({'id': c.lastrowid, 'name': char['name'], 'traits': char['traits']})
            conn.commit()

        os.remove(temp_path)
        logger.info(f"Extracted {len(inserted)} characters from {book_title}.")
        return jsonify({'characters': inserted, 'book_id': book_id})
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.exception("Error extracting characters")
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat_route():
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    character_id = data.get('character_id')
    user_message = data.get('message')
    session_history = data.get('history', [])

    if not user_id:
        logger.error("No user_id provided.")
        return jsonify({'error': 'No user ID provided'}), 400
    if not character_id:
        logger.error("No character_id provided.")
        return jsonify({'error': 'No character ID provided'}), 400
    if not user_message:
        logger.error("No message provided.")
        return jsonify({'error': 'No message provided'}), 400

    # basic sanitation
    if len(user_message) > 10000:
        return jsonify({'error': 'Message too long'}), 400

    with closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute("SELECT name, traits FROM characters WHERE id = ?", (character_id,))
        row = c.fetchone()
    if not row:
        logger.error(f"Character {character_id} not found.")
        return jsonify({'error': 'Character not found'}), 404
    name, traits = row['name'], row['traits']

    # Get past history (from database) and truncate
    stored_history = get_stored_history(character_id)
    truncated_past_history = truncate_history(stored_history, max_tokens=4000)
    past_history_str = "\n".join([f"User: {msg['content']}" if msg['is_user'] else f"{name}: {msg['content']}"
                                     for msg in truncated_past_history])

    # Convert current session history to LangChain message objects
    session_messages = convert_to_langchain_messages(session_history, name)

    try:
        # Generate psychological parameters (using past history)
        param_prompt = parameter_prompt_template.format(traits=traits, message=user_message, past_history=past_history_str)
        param_response = chat.invoke(param_prompt)

        # robust json extraction
        param_match = re.search(r"\{[\s\S]*\}", param_response.content or "")
        if not param_match:
            raise ValueError("Could not parse parameter JSON from model response")
        params = json.loads(param_match.group(0))

        # Generate emotions
        emotion_prompt = emotion_prompt_template.format(traits=traits, message=user_message, **params)
        emotion_response = chat.invoke(emotion_prompt)
        emotion_match = re.search(r"\{[\s\S]*\}", emotion_response.content or "")
        if not emotion_match:
            raise ValueError("Could not parse emotion JSON from model response")
        emotion_json = emotion_match.group(0)
        emotion_output = EmotionOutput.model_validate_json(emotion_json)
        anger = emotion_output.anger
        sadness = emotion_output.sadness
        joy = emotion_output.joy

        # Generate response; put system-style prompt first and then session messages then the user message
        response_prompt = response_prompt_template.format(
            name=name, traits=traits, past_history=past_history_str,
            anger=anger, sadness=sadness, joy=joy
        )

        # message sequence: system-like HumanMessage with instructions -> session history -> user input
        messages = [HumanMessage(content=response_prompt)] + session_messages + [HumanMessage(content=user_message)]

        ai_response = chat.invoke(messages)

        # Store messages
        store_message(user_id, character_id, user_message, True)
        store_message(user_id, character_id, ai_response.content, False)

        logger.info(f"Chat response generated for user {user_id} with character {character_id}.")
        return jsonify({
            'message': ai_response.content,
            'traits': traits,
            'parameters': params,
            'emotions': {'anger': anger, 'sadness': sadness, 'joy': joy}
        })
    except Exception as e:
        logger.exception("Error in chat route")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # production flags should be set via environment in deployed infra
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=(os.getenv('FLASK_DEBUG', 'false').lower() == 'true'))


# -------------------------
# Dockerfile (for reference)
# -------------------------
#
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . /app
# ENV FLASK_APP=app.py
# EXPOSE 5000
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
#
# -------------------------
# Procfile (for Render/Railway)
# -------------------------
# web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
#
# requirements.txt should include: Flask, python-dotenv, langchain-groq (or correct package), langchain-community,
# pydantic, gunicorn, flask-cors
