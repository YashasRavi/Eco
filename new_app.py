from flask import Flask, render_template, request, jsonify
import threading
import os
from new_monitor import monitor_csv
from flask_cors import CORS, cross_origin
from collections import defaultdict
import gpt_chat
import re
import os
from dotenv import load_dotenv, dotenv_values 

app = Flask(__name__)

CORS(app, support_credentials=True)

load_dotenv()

user_data = {}
user_messages = defaultdict(list)

@app.route('/')
@cross_origin(supports_credentials=True)
def index():
    return "Welcome to the Flask App!"

def start_monitoring():
    csv_path = os.getenv("CSV_URL")
    monitor_csv(csv_path, user_data)

@app.route('/message/<user_id>', methods=['POST'])
@cross_origin(supports_credentials=True)
def handle_message(user_id):
    message = request.json.get('message')
    chat_directions = "Do not user markdown formatting, * or #. NO numbered lists or bullet points, ONLY paragraph. Use 30-50 words, 50 words MAX"
    message = message + chat_directions
    
    user_messages[user_id].append({"role": "user", "content": message})
    gpt_response = gpt_chat.get_chatgpt_response(user_messages[user_id])
    user_messages[user_id].append({"role": "assistant", "content": gpt_response})
    
    return jsonify({"reply": gpt_response})

@app.route('/user/<user_id>', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def user_page(user_id):
    if request.method == 'POST':
        data = request.json
        user_data[user_id] = data
        if(len(user_messages) == 0):
            user_messages[user_id].append({"role": "assistant", "content": data["gpt_response"]})
        create_or_update_user_html(user_id, data)
        return jsonify({"status": "success"})
    
    data = user_data.get(user_id)
    if data:
        return render_template('test_page.html', data=data)
    else:
        return "User not found", 404

def create_or_update_user_html(user_id, data):
    user_page_path = os.path.join('templates', f'{user_id}.html')
    with app.app_context():
        with open(user_page_path, 'w') as f:
            f.write(render_template('test_page.html', data=data))
    print(f"Created/Updated HTML for user: {user_id}")

if __name__ == "__main__":
    monitoring_thread = threading.Thread(target=start_monitoring)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    app.run(debug=True)
