import subprocess
import sys

import pandas as pd
from sklearn.model_selection import train_test_split


# requirements.txt 설치 함수
def install_requirements():
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )


def import_dataset():
    df = pd.read_excel("240819_dataset_augmented_longreason_wg.xlsx")  # local 용
    df = df.dropna(subset=["input_sentence", "upper_objective", "type"])
    # "description"이 들어간 모든 열을 object 타입으로 변환
    for col in df.columns:
        if "description" in col:
            df[col] = df[col].astype("object")
    dfObjective = df[df["type"] == "Objective"]
    dfKeyresult = df[df["type"] == "Key Result"]

    trainObjective, testObjective = train_test_split(
        dfObjective, test_size=0.2, random_state=99
    )
    trainKeyresult, testKeyresult = train_test_split(
        dfKeyresult, test_size=0.2, random_state=99
    )
    train_df = pd.concat([trainObjective, trainKeyresult], ignore_index=True)
    test_df = pd.concat([testObjective, testKeyresult], ignore_index=True)

    return train_df, test_df


# if __name__ == "__main__":
# install_requirements()
# select_llm()

train_df, test_df = import_dataset()