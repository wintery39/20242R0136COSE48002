import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv("../.env")
api_key = os.getenv("OPENAI_API_KEY")

gpt = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2
) #gpt-4o모델 사용

# gpt api test

# res = gpt.invoke("hello").content
# print(res)