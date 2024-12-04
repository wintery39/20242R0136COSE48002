# JSON 문자열을 딕셔너리로 파싱
import json
import time
import re

from ai.llm_select import llm

EV_error = {"description": None, "score": None}

RV_error = {"descritpion": None, "revision": None}


# 키와 값의 타입을 검증하는 함수
def EV_validate(data):
    required_keys = {"description": str, "score": int}

    # 각 키를 검사
    for key, expected_type in required_keys.items():
        if key not in data or not isinstance(
            data[key], expected_type
        ):  # key와 value type 체크
            return False

    return True


def EV_parse_data(raw_string):
    # 일단 파싱 및 테스트 시도
    try:
        data = json.loads(raw_string)
        if EV_validate(data):
            return data  # 올바른 상황
        else:
            return EV_error  # json 형식이지만 key, value 등에서 오류가 있는 상황
    # LLM 사용해서 파싱
    except json.JSONDecodeError:
        # LLM을 통해 올바른 JSON 형식으로 수정 요청
        #         1. 출력은 반드시 중괄호 {}로 시작하고 끝나야 합니다. 2. key는 description, score 2개이며 각 타입은 str, int 입니다. 3. 모든 키와 값은 큰따옴표(")로 감싸야 합니다. score의 value인 int는 제외합니다. 4. 출력 시 모든 특수문자를 제거하십시오. 5. JSON 포맷만 반환하십시오. (추가 설명 금지)
        prompt = """다음 입력을 JSON 파싱이 가능한 형식으로 변환하십시오. 모든 str type 키와 값은 큰따옴표(")로 감싸야 합니다. 특수문자를 제거하십시오."""
        res = llm.invoke(raw_string + prompt).content

        match = re.search(r"\{.*\}", res, re.DOTALL)
        if match != None:
            res = match.group(0)

        try:  # 파싱 시도
            data = json.loads(res)
            if EV_validate(data):  # key, value가 유효함
                return data
            else:  # 유효하지 않으면 EV 에러 값 리턴
                return EV_error

        except json.JSONDecodeError:  # 파싱 실패
            return EV_error


def RV_validate(data):
    required_keys = {"description": str, "revision": str}

    # 각 키를 검사
    for key, expected_type in required_keys.items():
        if key not in data:  # key 체크
            return False
        if not isinstance(data[key], expected_type):  # value의 type 체크
            return False

    return True


def RV_parse_data(raw_string):
    # 일단 파싱 및 테스트 시도
    try:
        data = json.loads(raw_string)
        if RV_validate(data):
            return data  # 파싱이 되면 그대로 리턴
        else:
            return RV_error
    # LLM 사용해서 파싱
    except json.JSONDecodeError:
        # LLM을 통해 올바른 JSON 형식으로 수정 요청
        #         1. 출력은 반드시 중괄호 {}로 시작하고 끝나야 합니다. 2. key는 description, revision 2개이며 각 타입은 str, int 입니다. 3. 모든 키와 값은 큰따옴표(")로 감싸야 합니다. score의 value인 int는 제외합니다. 4. 출력 시 모든 특수문자를 제거하십시오. 5. JSON 포맷만 반환하십시오. (추가 설명 금지)
        prompt = """다음 입력을 JSON 파싱이 가능한 형식으로 변환하십시오. 모든 str type 키와 값은 큰따옴표(")로 감싸야 합니다. 특수문자를 제거하십시오."""

        res = llm.invoke(raw_string + prompt).content

        match = re.search(r"\{.*\}", res, re.DOTALL)
        res = match.group(0)

        try:  # 파싱 시도
            data = json.loads(res)
            if RV_validate(data):  # key, value가 유효함
                return data
            else:  # 유효하지 않으면 EV 에러 값 리턴
                return RV_error

        except json.JSONDecodeError:  # 파싱 실패
            return RV_error