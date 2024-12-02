# JSON 문자열을 딕셔너리로 파싱
import json
import time
import re

from ai.main import llm

def parse_data(json_string):
    # print("입력 JSON 문자열:\n", json_string)
    try:
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError:
        # print("Error: 유효하지 않은 JSON 형식입니다.")

        # LLM을 통해 올바른 JSON 형식으로 수정 요청
        prompt = """ 다음 입력을 JSON 파싱이 가능한 형식으로 변환하십시오. 
        1. 출력은 반드시 중괄호 {}로 시작하고 끝나야 합니다. 2. 각 줄 끝에는 반드시 쉼표(,)를 추가하십시오. 마지막 줄 제외. 3. 모든 키와 값은 큰따옴표(")로 감싸야 합니다. 숫자는 제외합니다. 4. 출력 시 모든 특수문자를 제거하십시오. 5. JSON 포맷만 반환하십시오. (추가 설명 금지)
        """
        res1 = llm.invoke(json_string + prompt).content
        res2 = llm.invoke(res1 + prompt).content
        # print("LLM 수정 결과:\n", res2)
        match = re.search(r"\{.*\}", res2, re.DOTALL)
        res2 = match.group(0)

        # 다시 파싱 시도
        try:
            data = json.loads(res2)
            #print("수정 성공\n")
            return data
        except json.JSONDecodeError:
            print("LLM이 수정한 JSON도 유효하지 않습니다.\n")
            print(res2)
            return None

# input: score, des 세트 3개
# output: 과반수 score, 병합된 des
def whowins(score1, score2, score3, des1, des2, des3):
    scores = [score1, score2, score3]
    dess = [des1, des2, des3]

    score_des_dict = {}
    for score, des in zip(scores, dess):
        if score in score_des_dict:
            score_des_dict[score].append(des)
        else:
            score_des_dict[score] = [des]

    # 점수들의 집합을 생성하여 유일한 값들의 개수를 셈
    unique_scores = set(scores)

    if len(unique_scores) == 1:
        # 모든 값이 같을 경우
        win_score = score1
        win_des = llm.invoke("세 문장을 조합해서 재구성해줘: " + ", ".join(score_des_dict[win_score])).content
    elif len(unique_scores) == 2:
        # 두 값이 같고 하나만 다른 경우
        for score in unique_scores:
            if scores.count(score) == 2:
                win_score = score
                win_des = llm.invoke("두 문장을 조합해서 재구성해줘: " + ", ".join(score_des_dict[win_score])).content
                break
    else:
        # 셋 다 다른 경우, 중간값을 반환
        win_score = sorted(scores)[1]
        win_des = score_des_dict[win_score][0]

    json_string = "win_score: " + str(win_score) + ',\n' + "win_des: " + win_des +',\n'

    res = parse_data(json_string)
    iterator = iter(res.items())
    key1, value1 = iterator.__next__()
    key2, value2 = iterator.__next__()
    win_score = value1
    win_des = value2
    return win_score, win_des
  

def selfC(EVRVfunc, input_sentence, upper_objective, memory, guideline, example1, example2, example3, isguide, isexample, criteria):
  print("\nselfC")
  res1 = EVRVfunc(input_sentence, upper_objective, memory, guideline, example1, isguide, isexample)
  iterator = iter(res1.items())
  key1, value1 = iterator.__next__()
  key2, value2 = iterator.__next__()
  des_1, score_1 = value1, value2
  print(f"des_1: {des_1}")
  print(f"score_1: {score_1}")
  time.sleep(3)

  res2 = EVRVfunc(input_sentence, upper_objective, memory, guideline, example2, isguide, isexample)
  iterator = iter(res2.items())
  key1, value1 = iterator.__next__()
  key2, value2 = iterator.__next__()
  des_2, score_2 = value1, value2
  print(f"des_2: {des_2}")
  print(f"score_2: {score_2}")
  time.sleep(3)

  res3 = EVRVfunc(input_sentence, upper_objective, memory, guideline, example3, isguide, isexample)
  iterator = iter(res3.items())
  key1, value1 = iterator.__next__()
  key2, value2 = iterator.__next__()
  des_3, score_3 = value1, value2
  print(f"des_3: {des_3}")
  print(f"score_3: {score_3}")
  time.sleep(3)

  winscore, windes = whowins(score_1, score_2, score_3, des_1, des_2, des_3)
  res = {f"predict_{criteria}_description": windes, f"predict_{criteria}_score": winscore}
  time.sleep(3)
  return res