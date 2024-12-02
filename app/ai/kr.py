from ai.krEVprompt import (
    krEV_task_description,
    krEV_example_prompt,
    krEV_suffix,
    krEV_connectivity_description,
    krEV_measurability_description,
    krEV_directivity_description,
    krEV_connectivity_examples,
)

from ai.krRVprompt import (
    krRV_task_description,
    krRV_example_prompt,
    krRV_suffix,
    krRV_examples,
)

from langchain.prompts import FewShotPromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from ai.parse import parse_data
from ai.main import llm


# 기존 3개 함수를 하나로 합치고 type 파라미터로 구분하는 함수입니다.
def krEV(
    input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
):
    keyResult_memory = ConversationBufferMemory()

    # 메모리의 system_message에 Task Description 추가
    keyResult_memory.save_context(
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
    if krtype == 0:  # con
        prefix = krEV_connectivity_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    elif krtype == 1:  # mea
        prefix = krEV_measurability_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    elif krtype == 2:  # dir
        prefix = krEV_directivity_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    else:  # error
        print("type parameter를 다시 확인하십시오. 0,1,2 중 하나여야 합니다.")

    # suffix(평가 문장 등 정보 담음)
    suffix = krEV_suffix.format(
        input_sentence=input_sentence,
        upper_objective=upper_objective,
        guideline=guideline,
    )

    if isexample:
        krEV_fewshot_prompt = FewShotPromptTemplate(
            prefix=prefix + "\n\n",
            examples=example,
            example_prompt=krEV_example_prompt,
            suffix=suffix,
        )
        final_prompt = krEV_fewshot_prompt.format(
            input_sentence=input_sentence, upper_objective=upper_objective
        )
    else:
        final_prompt = prefix + suffix

    print(type(final_prompt))
    print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    krEV_chain = ConversationChain(
        llm=llm,
        memory=keyResult_memory,
    )

    krEV_res = krEV_chain.run(final_prompt)

    krEV_res = parse_data(krEV_res)
    return krEV_res


res1 = krEV(
    "밥을 먹는다",
    "건강해진다",
    "출력 양식을 잘 지키십시오",
    krEV_connectivity_examples,
    True,
    True,
    0,
)
print(res1)


def krRV(
    input_sentence,
    upper_objective,
    guideline,
    example,
    EV_description,
    isguide,
    isexample,
):

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

    prefix = krRV_task_description.format(
        prefix_guideline=prefix_guideline, prefix_example=prefix_example
    )

    # suffix(평가 문장 등 정보 담음)
    suffix = krRV_suffix.format(
        guideline=guideline,
        input_sentence=input_sentence,
        upper_objective=upper_objective,
        EV_description=EV_description,
    )

    if isexample:
        krRV_fewshot_prompt = FewShotPromptTemplate(
            prefix=prefix + "\n\n",
            examples=example,
            example_prompt=krRV_example_prompt,
            suffix=suffix,
        )
        final_prompt = krRV_fewshot_prompt.format(
            input_sentence=input_sentence, upper_objective=upper_objective
        )
    else:
        final_prompt = prefix + suffix

    print(type(final_prompt))
    print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    krRV_chain = ConversationChain(llm=llm)

    krRV_res = krRV_chain.run(final_prompt)

    krRV_res = parse_data(krRV_res)
    return krRV_res


# res2 = krRV(
#     "밥을 먹는다",
#     "배불러진다",
#     "밥을 먹으면 어떤 상태가 될까요?",
#     krRV_examples,
#     "밥을 먹는 것은 배부른 것과 관련성이 큽니다",
#     True,
#     True,
# )

# print(res2)
