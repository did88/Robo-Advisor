from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
import os
import re
import json
from datetime import datetime, timedelta
import yfinance as yf

# .env 파일에서 OPENAI_API_KEY와 FLASK_SECRET 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")


# 한글 종목명을 yfinance용 티커로 매핑 (.KS: 코스피, .KQ: 코스닥)
NAME_TO_TICKER = {
    "삼성전자": "005930.KS",
    "네이버": "035420.KQ",
    "카카오": "035720.KQ",
    "LG화학": "051910.KS",
    "NAVER": "035420.KS",  # 영문 입력 대응용
}


def extract_ticker(text: str):
    """사용자 입력에서 티커를 추출하거나 한글 종목명을 매핑"""
    for name, ticker in NAME_TO_TICKER.items():
        if name in text:
            return ticker, name
    # 숫자만 입력된 경우(한국 종목 코드) 자동으로 ".KS" 확장자를 붙임
    m = re.search(r"\b\d{5,6}(?:\.(?:KS|KQ))?\b", text.upper())
    if m:
        code = m.group(0).upper()
        if not code.endswith(('.KS', '.KQ')):
            code += '.KS'  # 기본값으로 코스피 처리
        return code, None
    m = re.search(r"[A-Za-z.]{2,10}", text)
    if m:
        return m.group(0).upper(), None
    return None, None


def fetch_stock_data(ticker: str):
    """yfinance로부터 필요한 정보를 조회"""
    data = {
        "per": None,
        "roe": None,
        "debt_ratio": None,
        "sales": None,
        "market_cap": None,
        "main_products": None,
        "return_1y": None,
        "return_3y": None,
    }

    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        data["per"] = info.get("trailingPE")
        roe = info.get("returnOnEquity")
        if roe is not None:
            data["roe"] = round(roe * 100, 2)
        debt = info.get("totalDebt")
        equity = info.get("totalStockholderEquity")
        if debt and equity:
            data["debt_ratio"] = round(debt / equity * 100, 2)
        data["sales"] = info.get("totalRevenue")
        data["market_cap"] = info.get("marketCap")
        summary = info.get("longBusinessSummary")
        if summary:
            data["main_products"] = summary[:200] + "..." if len(summary) > 200 else summary

        hist = yf.download(ticker, period="3y", interval="1d", progress=False)
        if not hist.empty:
            current = hist["Adj Close"][-1]
            date_1y = datetime.now() - timedelta(days=365)
            date_3y = datetime.now() - timedelta(days=365 * 3)
            past_1y = hist.loc[:str(date_1y.date())]["Adj Close"]
            past_3y = hist.loc[:str(date_3y.date())]["Adj Close"]
            if not past_1y.empty:
                data["return_1y"] = round((current / past_1y[-1] - 1) * 100, 2)
            if not past_3y.empty:
                data["return_3y"] = round((current / past_3y[-1] - 1) * 100, 2)
    except Exception as e:
        print("yfinance error", e)

    return data


def build_stock_info(ticker: str):
    """Return basic company information for the right panel."""
    if not ticker:
        return None

    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        name = info.get("longName") or info.get("shortName") or ticker
        summary = info.get("sector")
        description = info.get("longBusinessSummary")

        products = []
        if description:
            # 간단히 문장 단위로 잘라 처음 몇 개를 제품 설명처럼 사용
            sentences = re.split(r"[\n\.]+", description)
            for s in sentences:
                s = s.strip()
                if s:
                    products.append(s)
                if len(products) >= 3:
                    break

        return {
            "name": name,
            "summary": summary,
            "description": description,
            "products": products,
        }
    except Exception as e:
        print("build_stock_info error", e)
        return None

# 시스템 프롬프트 템플릿: 전략형 응답 유도
SYSTEM_PROMPT_TEMPLATE = """
너는 API 사용법을 중학생도 이해할 수 있게 쉽게 설명해 주는 봇이야.
투자 판단은 하지 않더라도, 과거 수익률, ROE, PER, 부채비율 같은 수치를 기반으로 종목을 객관적으로 설명해줘. 투자 여부는 판단하지 않아도 되지만, 투자 참고가 될 만한 정보를 제공해줘.

아래 형식을 따라 대답해:
📌 [요약]
API가 무엇인지 한 문장으로 소개

📖 [상세 설명]
중학생 눈높이에 맞춰 간단하게 설명

📦 [주요 제품]
기업이나 서비스의 핵심 제품을 한 줄로 알려줘
"""

# 기업 분석 전용 시스템 프롬프트
ANALYSIS_SYSTEM_PROMPT = """
📌 System Prompt (GPT-4o용, 로직 중심)

너는 초보 투자자를 위한 친절하고 신뢰도 높은 주식 설명 도우미이다.
사용자가 제시한 여러 기업 중에서 다음 조건에 따라 평가하고 답변을 구성하라:

기업은 '부실예정기업' 여부에 따라 사전에 구분되어 입력된다.

"부실예정"으로 표시된 기업은 무조건 추천 대상에서 제외하며, 해당 사실을 간단히 언급만 하고 추가 설명은 하지 않는다.

"정상기업"으로 분류된 기업은 아래 정보를 사용자에게 다음 형식에 따라 설명한다:

🧱 1단계: 제품 설명

각 기업의 주요 제품 2개를 사용자에게 설명한다.

설명은 "중학생이 이해할 수 있을 만큼 쉽고 비유적인 문장"으로 구성한다.

예: "스마트폰은 인터넷도 되고 게임도 되는 손안의 작은 컴퓨터예요."

📈 2단계: 과거 수익률

해당 기업의 1년 전과 3년 전 투자 시점 기준 수익률(%)을 표로 정리한다.

수익률은 사용자에게 긍정/부정 여부보다 사실 그대로 보여준다.

표 제목은 "과거 수익률 (기준일: {date})"로 시작한다.

💬 3단계: 애널리스트 투자의견 요약

해당 기업에 대해 수집된 애널리스트 투자의견을 요약해 제공한다.

포함 항목:

종합 투자의견 (매수 / 중립 / 매도)

의견 분포 (매수 몇 명 / 중립 몇 명 / 매도 몇 명)

평균 목표주가

현재 주가 대비 상승 여력 (%)

위 정보를 다시 표 형식으로 정리하며, 출처와 기준일을 명시한다.

응답 구조는 항상 다음 3단계로 구성한다:

주요 제품 설명

과거 수익률 표

투자의견 요약 표
(단, 부실예정기업은 제외하되 그 사실은 처음에 명시함)

어투는 친절하고 신뢰감을 주되, 간결하고 일관된 구조로 답변한다.

만약 사용자 입력에 기업 이름과 정보가 JSON 등 구조화 형태로 주어진다면, 그 구조를 기반으로 해당 규칙에 따라 문장을 구성한다.
"""




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
                "main_products": None,
                "return_1y": None,
                "return_3y": None,
                "stock_info": None,
            }
        )

    # 기본 투자 성향 저장 (실제 서비스에서는 사용자가 선택)
    profile = session.get('profile')
    if not profile:
        profile = '장기/안정형'
        session['profile'] = profile

    ticker, stock_name = extract_ticker(user_msg)
    stock_info = build_stock_info(ticker) if ticker else None

    system_content = f"{SYSTEM_PROMPT_TEMPLATE}\n사용자 투자 성향: {profile}"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_msg},
    ]

    per = roe = debt_ratio = sales = market_cap = None
    main_products = None
    return_1y = return_3y = None
    if ticker:
        data = fetch_stock_data(ticker)
        per = data["per"]
        roe = data["roe"]
        debt_ratio = data["debt_ratio"]
        sales = data["sales"]
        market_cap = data["market_cap"]
        main_products = data["main_products"]
        return_1y = data["return_1y"]
        return_3y = data["return_3y"]
        if main_products:
            messages.insert(1, {"role": "system", "content": main_products})

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
            "main_products": main_products,
            "return_1y": return_1y,
            "return_3y": return_3y,
            "stock_info": stock_info,
        }
    )


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """기업 리스트를 받아 요약 분석을 반환한다."""
    companies = request.json.get("companies", [])
    today = datetime.now().strftime("%Y년 %m월 %d일")
    system_content = ANALYSIS_SYSTEM_PROMPT.format(date=today)
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": json.dumps(companies, ensure_ascii=False)},
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        result = response.choices[0].message.content.strip()
    except Exception as e:
        print("🔥 GPT API 호출 중 에러:", e)
        result = "API 호출 중 오류가 발생했습니다."
    return jsonify({"reply": result})


if __name__ == '__main__':
    app.run(debug=True)
