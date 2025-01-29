from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate
# from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel, Field
import os
from langchain_core.prompts import PromptTemplate
import json

load_dotenv()
print(111,'started')
api ="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"
if not api:
    raise ValueError("GROQ_API_KEY environment variable not set")

chat = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7,api_key = api 
)

app = Flask(__name__)
CORS(app)

session_histories = {}

def get_history(user_id):
    if user_id not in session_histories:
        session_histories[user_id] = ChatMessageHistory()
    return session_histories[user_id]

class EmotionOutput(BaseModel):
    anger: int = Field(default=0, description="Anger level (1-5)")
    sadness: int = Field(default=0, description="Sadness level (1-5)")


emotion_prompt_template = PromptTemplate(
    input_variables=["valence", "arousal", "selection_threshold", "resolution", "goal_directedness", "securing_rate"],
    template="""
Given the following psychological parameters:
Valence Level: {valence}
Arousal Level: {arousal}
Selection Threshold: {selection_threshold}
Resolution Level: {resolution}
Goal-Directedness: {goal_directedness}
Securing Rate: {securing_rate}
   Definitions:
    Anger: Arises when an obstacle (often another agent) clearly prevents the achievement of a relevant goal. Characteristics: negative valence, high arousal, low resolution level, high action-readiness, high selection threshold, and goal redirection to counter the obstacle.
    Sadness: Occurs when all perceived paths to achieving active, relevant goals are blocked, without a specific obstacle. Characteristics: negative valence, low arousal, decreased action-readiness due to goal inhibition, and an increased demand for affiliation (support-seeking behavior).

    Determine the anger and sadness levels on a scale of 1 to 5, based on these inputs.


Return a JSON object with anger and sadness levels as follows:
{{"anger": <anger_level>, "sadness": <sadness_level>}}
"""
)

@app.route('/')
def index():
    return jsonify({'message': 'Hello, world!'})

@app.route('/chat', methods=['POST'])
def chat_route():
    data = request.json
    user_id = data.get('user_id')
    user_message = data.get('message')
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
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    history = get_history(user_id)
    history.add_user_message(user_message)

    try:
        emotion_response = chat.invoke(emotion_prompt_template.format(**params))
        print("Raw emotion response:", emotion_response)

        s = emotion_response.content.find('{')
        e = emotion_response.content.rfind('}') + 1
        json_content = emotion_response.content[s:e]
        emotion_output = EmotionOutput.model_validate_json(json_content)
        anger = emotion_output.anger
        sadness = emotion_output.sadness 

        user_emotion_message = (
            f"User message: {user_message}, "
            f"Anger level: {anger} (1-5), Sadness level: {sadness} (1-5)."
        )
        history.add_user_message(user_emotion_message)

        full_history = "\n".join([msg.content for msg in history.messages])
        
        ai_response = chat.invoke(full_history,)
        print("Full history:", full_history)
        print("AI response:", ai_response.content)
        history.add_ai_message(ai_response.content)
        message = ai_response.content
        print(message,'message')
        return jsonify({
            'anger': anger,
            'sadness': sadness,
            'history': [msg.content for msg in history.messages],
            'message': message
        })

    except Exception as e:
        print(f"Error while processing emotions: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
