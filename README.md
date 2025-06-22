# Robo-Advisor Chat Demo

프레젠테이션을 위한 로보 어드바이저 데모 웹앱입니다. GPT API와 yfinance를 활용하여 실시간 주가 정보를 보여주는 챗봇을 구현했습니다. GPT-4o 모델을 사용합니다. 아래와 같이 실행할 수 있습니다.

## 설치
```bash
pip install -r requirements.txt
```

OpenAI API 키를 환경 변수 `OPENAI_API_KEY`로 설정합니다.

## 실행
```bash
python app.py
```

브라우저에서 `http://localhost:5000` 에 접속합니다. 티커나 기업명을 입력하면 yfinance에서 실시간 데이터를 조회해 간단한 재무 지표를 확인할 수 있습니다.
