from ai.krEVprompt import (
    krEV_task_description,
    krEV_example_prompt,
    krEV_suffix,
    kr_background_template,
    krEV_connectivity_description,
    krEV_measurability_description,
    krEV_directivity_description,
    krEV_connectivity_examples,
)

from langchain.prompts import FewShotPromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from parse import parse_data
from main import llm


# 기존 3개 함수를 하나로 합치고 type 파라미터로 구분하는 함수입니다.
def krEV(input_sentence, upper_objective, guideline, example, isguide, isexample, type):
    memory = ConversationBufferMemory()

    # 메모리의 system_message에 Task Description 추가
    print(krEV_task_description)
    memory.save_context(
        inputs={"human": krEV_task_description},
        outputs={"AI": "저의 역할을 이해했습니다."},
    )

    # guideline
    if isguide:
        prefix_guideline = "- 주어진 가이드라인을 평가에 이용하세요"
        guideline = guideline
    else:
        prefix_guideline = " "
        guideline = " "
        for example in example:
            example["guideline"] = " "

    # example
    if isexample:
        prefix_example = "- 예시는 참고용일 뿐입니다. 현재 주어진 input_sentence와 upper_objective에 집중하여 평가하세요."
    else:
        prefix_example = " "

    # type에 따라 prefix(description)가 달라짐
    if type == 0:  # con
        prefix = krEV_connectivity_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    elif type == 1:  # mea
        prefix = krEV_measurability_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    elif type == 2:  # dir
        prefix = krEV_directivity_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    else:  # error
        print("type parameter를 다시 확인하십시오. 0,1,2 중 하나여야 합니다.")

    print(prefix)
    memory.save_context(
        inputs={"human": prefix},
        outputs={"AI": "평가 기준, 출력 형식, 주의사항을 이해했습니다."},
    )

    if isexample:
        krEV_fewshot_prompt = FewShotPromptTemplate(
            prefix=" ",
            examples=example,
            example_prompt=krEV_example_prompt,
            suffix=" ",
        )
        example_prompt = krEV_fewshot_prompt.format()

        print(example_prompt)
        memory.save_context(
            inputs={"human": example_prompt},
            outputs={"AI": "예시를 잘 보았습니다. 이를 활용해 평가하겠습니다."},
        )

    # # 기업 background 정보 전달
    # keyResult_background = kr_background_template.format(
    #     company="회사명",  # 회사명
    #     field="업종",  # 업종
    #     team="팀명",  # 팀명
    # )

    # print(keyResult_background)
    # memory.save_context(
    #     inputs={"system": keyResult_background},
    #     outputs={"AI": "평가할 기업의 배경 정보를 학습했습니다."},
    # )

    # suffix (모델의 최종 입력으로 사용)
    suffix = krEV_suffix.format(
        guideline=guideline,
        input_sentence=input_sentence,
        upper_objective=upper_objective,
    )
    print(suffix)

    krEV_chain = ConversationChain(
        llm=llm,
        memory=memory,
    )

    krEV_res = krEV_chain.run(suffix)

    krEV_res = parse_data(krEV_res)
    return krEV_res


res = krEV(
    "밥을 먹는다",
    "건강해진다",
    "출력 양식을 잘 지키십시오",
    krEV_connectivity_examples,
    True,
    True,
    0,
)

print(res)
