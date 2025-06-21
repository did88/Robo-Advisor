from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
import os
import sqlite3

# .env 파일에서 OPENAI_API_KEY와 FLASK_SECRET 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")

DB_PATH = "stocks.db"


def init_db():
    """Create table and seed basic data if empty"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            sector TEXT,
            per REAL,
            roe TEXT,
            debt_ratio TEXT,
            note TEXT
        )
        """
    )
    cur = conn.execute("SELECT COUNT(*) FROM stocks")
    if cur.fetchone()[0] == 0:
        sample = [
            (
                "삼성전자",
                "IT",
                10,
                "15%",
                "20%",
                "반도체 수요 회복 예상",
            ),
            (
                "LG화학",
                "화학/2차전지",
                15,
                "12%",
                "30%",
                "배터리 사업 성장",
            ),
            (
                "NAVER",
                "인터넷",
                25,
                "20%",
                "10%",
                "플랫폼 사업 확대",
            ),
        ]
        conn.executemany(
            "INSERT INTO stocks (name, sector, per, roe, debt_ratio, note) VALUES (?, ?, ?, ?, ?, ?)",
            sample,
        )
        conn.commit()
    conn.close()


init_db()
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row

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


def extract_stock_names(text: str):
    """사용자 입력에서 종목명을 추출"""
    cur = conn.execute("SELECT name FROM stocks")
    names = [row[0] for row in cur.fetchall()]
    return [name for name in names if name in text]


def build_stock_info(names):
    """종목명에 해당하는 간단한 정보를 문자열로 반환"""
    if not names:
        return "언급된 종목이 없습니다."
    info_lines = []
    for name in names:
        row = conn.execute(
            "SELECT sector, per, roe, debt_ratio, note FROM stocks WHERE name = ?",
            (name,),
        ).fetchone()
        if row:
            info_lines.append(
                f"{name} (업종: {row['sector']}, PER: {row['per']}, ROE: {row['roe']}, 부채비율: {row['debt_ratio']}) - {row['note']}"
            )
    return "\n".join(info_lines)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '').strip()
    if not user_msg:
        return jsonify({'reply': '메시지를 입력해주세요.'})

    # 기본 투자 성향 저장 (실제 서비스에서는 사용자가 선택)
    profile = session.get('profile')
    if not profile:
        profile = '장기/안정형'
        session['profile'] = profile

    stock_names = extract_stock_names(user_msg)
    stock_info = build_stock_info(stock_names)

    strategy_prompt = (
        f"사용자 투자 성향: {profile}\n{stock_info}\n"
        "위 정보를 참고해 분석적이고 전략적인 조언을 제시해."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": strategy_prompt},
        {"role": "user", "content": user_msg},
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        print("🔥 GPT API 호출 중 에러:", e)
        answer = 'API 호출 중 오류가 발생했습니다.'

    return jsonify({'reply': answer})


if __name__ == '__main__':
    app.run(debug=True)
