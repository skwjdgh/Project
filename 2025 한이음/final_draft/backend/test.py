from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

print("API KEY:", os.getenv("OPENAI_API_KEY"))

client = OpenAI(api_key=api_key)
prompt = f"""사용자가 다음과 같이 말했습니다:\n\n\"{"등본 요청"}\"\n\n이 사용자의 주요 목적이 무엇인지 한 줄로 요약해 주세요. (예: '주민등록등본 발급 요청')"""
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "당신은 공공기관 키오스크 안내 도우미입니다. 사용자의 목적만 파악해 짧게 알려주세요"},
        {"role": "user", "content": prompt}
    ]
)
summary = response.choices[0].message.content.strip()

print("🤖 분석된 목적:", summary)



