from flask import Flask, render_template, request, jsonify
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '')
    if not user_msg:
        return jsonify({'reply': '메시지를 입력해주세요.'})
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are a helpful Robo-Advisor."},
                {"role": "user", "content": user_msg}
            ]
        )
        answer = response.choices[0].message.content.strip()
    except Exception:
        answer = 'API 호출 중 오류가 발생했습니다.'
    return jsonify({'reply': answer})

if __name__ == '__main__':
    app.run(debug=True)
