import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 정의되어 있지 않습니다.")

llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=OPENAI_API_KEY)

def load_prompt(path: str) -> PromptTemplate:
    with open(path, 'r', encoding='utf-8') as f:
        template = f.read()
    return PromptTemplate.from_template(template)

summary_prompt = load_prompt("prompts/summary_prompt.txt")
trend_prompt   = load_prompt("prompts/trend_prompt.txt")

summary_chain = summary_prompt | llm
trend_chain   = trend_prompt | llm
