import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(dotenv_path="../env")
api_key = os.getenv("GOOGLE_API_KEY")

gemini = ChatGoogleGenerativeAI(
  model="gemini-pro"
)

# gemmini api test

# res = gemini.invoke("hello").content
# print(res)