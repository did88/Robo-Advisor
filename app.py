from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

# .env 파일에서 OPENAI_API_KEY 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# 시스템 프롬프트: 전략형 응답 유도
system_prompt = """
너는 투자 판단을 도와주는 전략형 로보 어드바이저야.  
금융 라이센스 여부는 언급하지 말고, 아래 포맷에 따라 구체적으로 조언해.

다음 형식을 반드시 지켜:
📌 [요약]  
한 문장으로 투자 매력도 또는 주의점 제시

📊 [분석 근거]  
재무지표, 업황, 기업전략 등 2~3개로 구성

⚠️ [리스크]  
투자 시 주의할 요소 1~2개

💡 [투자 판단]  
어떤 투자자에게 적합한지 또는 어떤 전략에 잘 맞는지
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '')
    if not user_msg:
        return jsonify({'reply': '메시지를 입력해주세요.'})
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        print("🔥 GPT API 호출 중 에러:", e)
        answer = 'API 호출 중 오류가 발생했습니다.'
    
    return jsonify({'reply': answer})

if __name__ == '__main__':
    app.run(debug=True)
