from ai.llm_gpt import gpt
from ai.llm_gemini import gemini


def select_llm():
    user_input = 1
    # user_input = int(input("사용할 llm을 입력하세요(gpt는 0, gemini는 1) : "))
    if user_input == 0:
        llm = gpt
    else:
        llm = gemini
    return llm


llm = select_llm()