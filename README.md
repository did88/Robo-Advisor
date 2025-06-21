# Robo-Advisor Chat Demo

프레젠테이션을 위한 로보 어드바이저 데모 웹앱입니다. GPT API를 활용하여 간단한 투자 상담 챗봇을 구현했습니다. 아래와 같이 실행할 수 있습니다.

## 설치
```bash
pip install -r requirements.txt
```

OpenAI API 키를 환경 변수 `OPENAI_API_KEY`로 설정합니다.

## 실행
```bash
python app.py
```

브라우저에서 `http://localhost:5000` 에 접속합니다. 예시로 "삼성전자에 투자해도 될까?" 라고 입력하면 GPT의 재무 조언을 확인할 수 있습니다.
