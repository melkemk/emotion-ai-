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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api = os.getenv("GROQ_API_KEY", "")
if not api:
    raise ValueError("GROQ_API_KEY environment variable not set")

chat = ChatGroq(model_name="llama3-70b-8192", temperature=0.7, api_key=api)

app = Flask(__name__)
CORS(app)

def get_db():
    conn = sqlite3.connect('app.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS characters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, name TEXT, traits TEXT,
                  FOREIGN KEY (book_id) REFERENCES books (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, character_id INTEGER,
                  content TEXT, is_user BOOLEAN, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (character_id) REFERENCES characters (id))''')
    conn.commit()
    conn.close()
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

def get_stored_history(character_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT content, is_user FROM messages ")
    rows = c.fetchall()
    conn.close()
    return [{'content': row['content'], 'is_user': row['is_user']} for row in rows]

def store_message(user_id, character_id, content, is_user):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, character_id, content, is_user) VALUES (?, ?, ?, ?)",
              (user_id, character_id, content, is_user))
    conn.commit()
    conn.close()

def estimate_tokens(text):
    return len(text) // 4

def truncate_history(history, max_tokens=5000):
    truncated = []
    total_tokens = 0
    for msg in reversed(history):
        msg_str = f"User: {msg['content']}" if msg['is_user'] else f"Character: {msg['content']}"
        msg_tokens = estimate_tokens(msg_str)
        if total_tokens + msg_tokens > max_tokens:
            break
        truncated.insert(0, msg)
        total_tokens += msg_tokens
    return truncated

def convert_to_langchain_messages(session_history, name):
    # Convert session history to LangChain message objects
    messages = []
    for msg in session_history:
        if msg['is_user']:
            messages.append(HumanMessage(content=msg['content']))
        else:
            messages.append(AIMessage(content=msg['content'], name=name))
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
    if not file.filename.endswith('.pdf'):
        logger.error("Only PDF files are supported.")
        return jsonify({'error': 'Only PDF files are supported'}), 400

    temp_path = "temp_book.pdf"
    file.save(temp_path) 

    try: 
        loader = PyPDFLoader(temp_path)
        pages = loader.load()
        text = "\n".join([page.page_content for page in pages])

        prompt = f"Extract all characters from the following text and provide their names and key traits:\n\n{text[:10000]}"
        response = chat.invoke(prompt)
        lines = response.content.split('\n')
        characters = []
        for line in lines:
            if line.strip():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    name = parts[0].strip().split('.', 1)[-1].strip()
                    traits = parts[1].strip()
                    characters.append({'name': name, 'traits': traits})

        conn = get_db()
        c = conn.cursor()  
        book_title = request.form.get('book_title', file.filename.rsplit('.', 1)[0])
        c.execute("INSERT INTO books (title) VALUES (?)", (book_title,))
        book_id = c.lastrowid
        for char in characters:
            c.execute("INSERT INTO characters (book_id, name, traits) VALUES (?, ?, ?)",
                      (book_id, char['name'], char['traits']))
        conn.commit()
        chars_with_ids = [{'id': c.lastrowid - len(characters) + i + 1, 'name': char['name'], 'traits': char['traits']}
                          for i, char in enumerate(characters)]
        conn.close()

        os.remove(temp_path)
        logger.info(f"Extracted {len(characters)} characters from {book_title}.")
        return jsonify({'characters': chars_with_ids, 'book_id': book_id})
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Error extracting characters: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat_route(): 
    data = request.json
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

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, traits FROM characters WHERE id = ?", (character_id,))
    row = c.fetchone()
    conn.close()
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
        # Generate psychological parameters (using past history )
        param_prompt = parameter_prompt_template.format(traits=traits, message=user_message, past_history=past_history_str)
        param_response = chat.invoke(param_prompt)
        s = param_response.content.find('{')
        e = param_response.content.rfind('}') + 1
        param_json = param_response.content[s:e]
        params = json.loads(param_json)

        # Generate emotions (using past history and current message)
        emotion_prompt = emotion_prompt_template.format(traits=traits, message=user_message, **params)
        emotion_response = chat.invoke(emotion_prompt)
        s = emotion_response.content.find('{')
        e = emotion_response.content.rfind('}') + 1
        emotion_json = emotion_response.content[s:e]
        emotion_output = EmotionOutput.model_validate_json(emotion_json)
        anger = emotion_output.anger
        sadness = emotion_output.sadness
        joy = emotion_output.joy

        # Generate response (past history as string, session history as message objects)
        response_prompt = response_prompt_template.format(
            name=name, traits=traits, past_history=past_history_str,
            anger=anger, sadness=sadness, joy=joy
        )
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
        logger.error(f"Error in chat route: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
