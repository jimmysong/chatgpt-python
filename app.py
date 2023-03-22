import os
import openai

from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff


api_key = os.environ.get("OPENAI_API_KEY")
socket_key = os.environ.get("SOCKET_KEY")

if api_key is None:
    print("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
    exit
if socket_key is None:
    print("Socket key is not set. Please set the OPENAI_API_KEY environment variable.")
    exit

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

MODEL = 'gpt-3.5-turbo'

# Create Flask app and SocketIO instance
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = socket_key
socketio = SocketIO(app)

# Define event handler for generating text
@socketio.on('generate_text')
@cross_origin(origin='*')
def handle_generate_text(input_text):
    messages = [
        {"role": "system", "content": "You are an explainer for a 10-year old kid."},
        {"role": "user", "content": input_text},
    ]
    print(f"got asked {input_text}")
    response = completion_with_backoff(
        model=MODEL,
        messages=messages,
        temperature=0.1,
    )
    generated_text = response.choices[0].message.content
    emit('generated_text', generated_text)

# Define route for index page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app)

