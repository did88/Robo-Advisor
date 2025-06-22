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
    """Create table and seed basic data if empty."""
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
            sales TEXT,
            market_cap TEXT,
            risk_level TEXT,
            main_products TEXT,
            max_return_1y REAL,
            max_loss_1y REAL,
            max_return_3y REAL,
            max_loss_3y REAL
        )
        """
    )
    cur = conn.execute("SELECT COUNT(*) FROM stocks")
    if cur.fetchone()[0] == 0:
        sample = [
            (
                "삼성전자",
                "반도체",
                10.5,
                "15%",
                "40%",
                "280조원",
                "500조원",
                "낮음",
                "스마트폰, 반도체",
                45.0,
                -22.0,
                150.0,
                -45.0,
            ),
            (
                "LG화학",
                "화학/2차전지",
                15.2,
                "12%",
                "30%",
                "50조원",
                "70조원",
                "중간",
                "배터리, 석유화학",
                40.0,
                -18.0,
                120.0,
                -35.0,
            ),
            (
                "NAVER",
                "인터넷",
                25.3,
                "20%",
                "10%",
                "8조원",
                "40조원",
                "높음",
                "포털, 클라우드",
                60.0,
                -30.0,
                200.0,
                -50.0,
            ),
        ]
        conn.executemany(
            "INSERT INTO stocks (name, sector, per, roe, debt_ratio, sales, market_cap, risk_level, main_products, max_return_1y, max_loss_1y, max_return_3y, max_loss_3y) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample,
        )
        conn.commit()
    conn.close()


init_db()
def get_db_connection():
    """Return a SQLite connection with row factory configured."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 시스템 프롬프트 템플릿: 전략형 응답 유도
SYSTEM_PROMPT_TEMPLATE = """
너는 API 사용법을 중학생도 이해할 수 있게 쉽게 설명해 주는 봇이야.
투자 리스크나 투자 판단에 대한 내용은 언급하지 마.

아래 형식을 따라 대답해:
📌 [요약]
API가 무엇인지 한 문장으로 소개

📖 [상세 설명]
중학생 눈높이에 맞춰 간단하게 설명

📦 [주요 제품]
기업이나 서비스의 핵심 제품을 한 줄로 알려줘
"""


def extract_stock_names(text: str):
    """사용자 입력에서 종목명을 추출"""
    conn = get_db_connection()
    cur = conn.execute("SELECT name FROM stocks")
    names = [row[0] for row in cur.fetchall()]
    conn.close()
    return [name for name in names if name in text]


def build_stock_info(names):
    """종목명에 해당하는 간단한 정보를 문자열로 반환"""
    if not names:
        return "언급된 종목이 없습니다."
    info_lines = []
    conn = get_db_connection()
    for name in names:
        row = conn.execute(
            "SELECT main_products FROM stocks WHERE name = ?",
            (name,),
        ).fetchone()
        if row:
            info_lines.append(f"{name} 주요 제품: {row['main_products']}")
    conn.close()
    return "\n".join(info_lines)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify(
            {
                "reply": "메시지를 입력해주세요.",
                "name": None,
                "per": None,
                "roe": None,
                "debt_ratio": None,
                "sales": None,
                "market_cap": None,
                "sector": None,
                "risk_level": None,
                "main_products": None,
                "max_return_1y": None,
                "max_loss_1y": None,
                "max_return_3y": None,
                "max_loss_3y": None,
            }
        )

    # 기본 투자 성향 저장 (실제 서비스에서는 사용자가 선택)
    profile = session.get('profile')
    if not profile:
        profile = '장기/안정형'
        session['profile'] = profile

    stock_names = extract_stock_names(user_msg)
    stock_info = build_stock_info(stock_names)

    system_content = f"{SYSTEM_PROMPT_TEMPLATE}\n사용자 투자 성향: {profile}"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "system", "content": stock_info},
        {"role": "user", "content": user_msg},
    ]

    # 기본 지표 값
    per = roe = debt_ratio = sales = market_cap = sector = risk_level = None
    main_products = None
    max_return_1y = max_loss_1y = max_return_3y = max_loss_3y = None
    stock_name = stock_names[0] if stock_names else None
    if stock_name:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT sector, per, roe, debt_ratio, sales, market_cap, risk_level, main_products, max_return_1y, max_loss_1y, max_return_3y, max_loss_3y FROM stocks WHERE name = ?",
            (stock_name,),
        ).fetchone()
        conn.close()
        if row:
            sector = row["sector"]
            per = row["per"]
            roe = row["roe"]
            debt_ratio = row["debt_ratio"]
            sales = row["sales"]
            market_cap = row["market_cap"]
            risk_level = row["risk_level"]
            main_products = row["main_products"]
            max_return_1y = row["max_return_1y"]
            max_loss_1y = row["max_loss_1y"]
            max_return_3y = row["max_return_3y"]
            max_loss_3y = row["max_loss_3y"]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        print("🔥 GPT API 호출 중 에러:", e)
        answer = "API 호출 중 오류가 발생했습니다."

    return jsonify(
        {
            "reply": answer,
            "name": stock_name,
            "per": per,
            "roe": roe,
            "debt_ratio": debt_ratio,
            "sales": sales,
            "market_cap": market_cap,
            "sector": sector,
            "risk_level": risk_level,
            "main_products": main_products,
            "max_return_1y": max_return_1y,
            "max_loss_1y": max_loss_1y,
            "max_return_3y": max_return_3y,
            "max_loss_3y": max_loss_3y,
        }
    )


if __name__ == '__main__':
    app.run(debug=True)
