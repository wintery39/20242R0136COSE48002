import subprocess
import sys

from ai.llm_gpt import gpt
from ai.llm_gemini import gemini

import pandas as pd
from sklearn.model_selection import train_test_split

# requirements.txt 설치 함수
def install_requirements():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    

def select_llm():
    user_input = 1
    # user_input = int(input("사용할 llm을 입력하세요(gpt는 0, gemini는 1) : "))
    if user_input == 0:
        llm = gpt
    else:
        llm = gemini
    return llm



# if __name__ == "__main__":
    # install_requirements()
    # select_llm()

llm = select_llm()
    