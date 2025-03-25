from xml.dom.minidom import CharacterData
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
import os
import sqlite3
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import json

load_dotenv()
api = os.getenv("GROQ_API_KEY", "abcd")
if not api:
    raise ValueError("GROQ_API_KEY environment variable not set")

chat = ChatGroq(model_name="llama3-70b-8192", temperature=0.7, api_key=api)

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS characters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, name TEXT, traits TEXT,
                  FOREIGN KEY (book_id) REFERENCES books (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, character_id INTEGER,
                  content TEXT, is_user BOOLEAN, anger INTEGER, sadness INTEGER, joy INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (character_id) REFERENCES characters (id))''')
    conn.commit()
    conn.close()

class EmotionOutput(BaseModel):
    anger: int = Field(default=0, description="Anger level (1-5)")
    sadness: int = Field(default=0, description="Sadness level (1-5)")
    joy: int = Field(default=0, description="Joy level (1-5)")

emotion_prompt_template = PromptTemplate(
    input_variables=["traits", "message", "valence", "arousal", "selection_threshold", "resolution", "goal_directedness", "securing_rate"],
    template="""
You are simulating a character with traits: {traits}.

Given the following psychological parameters:
Valence Level: {valence}
Arousal Level: {arousal}
Selection Threshold: {selection_threshold}
Resolution Level: {resolution}
Goal-Directedness: {goal_directedness}
Securing Rate: {securing_rate}

And the user's message: "{message}"

Determine the anger, sadness, and joy levels on a scale of 1 to 5 based on these inputs and the character's traits.
Definitions:
- Anger: Negative valence, high arousal, low resolution, high selection threshold, goal redirection.
- Sadness: Negative valence, low arousal, decreased action-readiness, increased affiliation demand.
- Joy: Positive valence, moderate to high arousal, high goal-directedness, low securing rate.

Return a JSON object:
{{"anger": <anger_level>, "sadness": <sadness_level>, "joy": <joy_level>}}
"""
)

response_prompt_template = PromptTemplate(
    input_variables=["name", "traits", "history", "anger", "sadness", "joy", "message"],
    template="""
You are {name}, a character with these traits: {traits}. Stay true to your identity and traits in your response. 
Reflect your current emotional state subtly without mentioning emotions explicitly.

Current emotional state: Anger - {anger}/5, Sadness - {sadness}/5, Joy - {joy}/5.

Conversation history (use this to maintain context):
{history}

User's message: "{message}"

Respond as {name}, keeping your traits and past interactions in mind.
"""
)

def get_db():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_history(user_id, character_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT content, is_user, anger, sadness, joy FROM messages WHERE user_id = ? AND character_id = ? ORDER BY timestamp",
              (user_id, character_id))
    rows = c.fetchall()
    history = ChatMessageHistory()
    for row in rows:
        if row['is_user']:
            history.add_user_message(row['content'])
        else:
            history.add_ai_message(row['content'])
    conn.close()
    return history

@app.route('/')
def index():
    return jsonify({'message': 'Hello, world!'})

@app.route('/extract_characters', methods=['POST'])
def extract_characters():
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    prompt = f"Extract all characters from the following text and provide their names and key traits:\n\n{text}"
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
    book_title = data.get('book_title', 'Untitled')
    c.execute("INSERT INTO books (title) VALUES (?)", (book_title,))
    book_id = c.lastrowid
    for char in characters:
        c.execute("INSERT INTO characters (book_id, name, traits) VALUES (?, ?, ?)",
                  (book_id, char['name'], char['traits']))
    conn.commit()
    chars_with_ids = [{'id': c.lastrowid - len(characters) + i + 1, 'name': char['name'], 'traits': char['traits']}
                      for i, char in enumerate(characters)]
    conn.close()
    return jsonify({'characters': chars_with_ids, 'book_id': book_id})

@app.route('/chat', methods=['POST'])
def chat_route():
    data = request.json
    user_id = data.get('user_id')
    character_id = data.get('character_id')
    user_message = data.get('message')
    print(data,)
    params = {
        'valence': data.get('valence', 3),
        'arousal': data.get('arousal', 3),
        'selection_threshold': data.get('selection_threshold', 3),
        'resolution': data.get('resolution', 3),
        'goal_directedness': data.get('goal_directedness', 3),
        'securing_rate': data.get('securing_rate', 3)
    }

    if not user_id:
        return jsonify({'error': 'No user ID provided'}), 400
    if not character_id:
        return jsonify({'error': 'No character ID provided'}), 400
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # Get character details
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, traits FROM characters WHERE id = ?", (character_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Character not found'}), 404
    name, traits = row['name'], row['traits']
    print(f"Selected character: {name} with traits: {traits}")

    # Get conversation history
    history = get_history(user_id, character_id)
    history.add_user_message(user_message)
    full_history = "\n".join([f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"{name}: {msg.content}" 
                             for msg in history.messages])
    print(f"Conversation history: {full_history}")

    try:
        # Compute emotions
        emotion_prompt = emotion_prompt_template.format(traits=traits, message=user_message, **params)
        emotion_response = chat.invoke(emotion_prompt)
        s = emotion_response.content.find('{')
        e = emotion_response.content.rfind('}') + 1
        json_content = emotion_response.content[s:e]
        emotion_output = EmotionOutput.model_validate_json(json_content)
        anger = emotion_output.anger
        sadness = emotion_output.sadness
        joy = emotion_output.joy
        print(f"Computed emotions - Anger: {anger}, Sadness: {sadness}, Joy: {joy}")

        # Generate AI response
        response_prompt = response_prompt_template.format(
            name=name, traits=traits, history=full_history, anger=anger, sadness=sadness, joy=joy, message=user_message
        )
        ai_response = chat.invoke(response_prompt)
        history.add_ai_message(ai_response.content)
        print(f"AI response: {ai_response.content}")

        # Store messages
        c.execute("INSERT INTO messages (user_id, character_id, content, is_user, anger, sadness, joy) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, character_id, user_message, 1, None, None, None))
        c.execute("INSERT INTO messages (user_id, character_id, content, is_user, anger, sadness, joy) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, character_id, ai_response.content, 0, anger, sadness, joy))
        conn.commit()

        # Prepare history for response
        c.execute("SELECT content, is_user, anger, sadness, joy FROM messages WHERE user_id = ? AND character_id = ? ORDER BY timestamp",
                  (user_id, character_id))
        rows = c.fetchall()
        history_response = [{'content': row['content'], 'is_user': row['is_user'],
                            'anger': row['anger'], 'sadness': row['sadness'], 'joy': row['joy']} for row in rows]
        conn.close()

        return jsonify({
            'anger': anger,
            'sadness': sadness,
            'joy': joy,
            'history': history_response,
            'message': ai_response.content
        })
    except Exception as e:
        conn.close()
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
