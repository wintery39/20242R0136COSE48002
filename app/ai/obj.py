from ai.objEVprompt import (
    objEV_task_description,
    objEV_example_prompt,
    objEV_suffix,
    objEV_align_description,
    objEV_value_description,
    objEV_align_examples,
    objEV_value_examples,
)

from ai.objRVprompt import (
    objRV_task_description,
    objRV_example_prompt,
    objRV_suffix,
    objRV_examples,
)

from langchain.prompts import FewShotPromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from ai.parse import parse_data
from ai.main import llm


# 기존 3개 함수를 하나로 합치고 objtype 파라미터로 구분하는 함수입니다.
def objEV(
    input_sentence, upper_objective, guideline, example, isguide, isexample, objtype
):
    memory = ConversationBufferMemory()

    # 메모리의 system_message에 Task Description 추가
    memory.save_context(
        inputs={"human": objEV_task_description},
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
    if objtype == 0:  # align
        prefix = objEV_align_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    elif objtype == 1:  # value
        prefix = objEV_value_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    else:  # error
        print("objtype parameter를 다시 확인하십시오. 0,1 중 하나여야 합니다.")

    # suffix(평가 문장 등 정보 담음)
    suffix = objEV_suffix.format(
        input_sentence=input_sentence,
        upper_objective=upper_objective,
        guideline=guideline,
    )

    if isexample:
        objEV_fewshot_prompt = FewShotPromptTemplate(
            prefix=prefix + "\n\n",
            examples=example,
            example_prompt=objEV_example_prompt,
            suffix=suffix,
        )
        final_prompt = objEV_fewshot_prompt.format(
            input_sentence=input_sentence, upper_objective=upper_objective
        )
    else:
        final_prompt = prefix + suffix

    print(type(final_prompt))
    print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    objEV_chain = ConversationChain(
        llm=llm,
        memory=memory,
    )

    objEV_res = objEV_chain.run(final_prompt)

    objEV_res = parse_data(objEV_res)
    return objEV_res


# res1 = objEV(
#     "밥을 먹는다",
#     "건강해진다",
#     "출력 양식을 잘 지키십시오",
#     objEV_align_examples,
#     True,
#     True,
#     0,
# )
# print(res1)


def objRV(
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

    prefix = objRV_task_description.format(
        prefix_guideline=prefix_guideline, prefix_example=prefix_example
    )

    # suffix(평가 문장 등 정보 담음)
    suffix = objRV_suffix.format(
        guideline=guideline,
        input_sentence=input_sentence,
        upper_objective=upper_objective,
        EV_description=EV_description,
    )

    if isexample:
        objRV_fewshot_prompt = FewShotPromptTemplate(
            prefix=prefix + "\n\n",
            examples=example,
            example_prompt=objRV_example_prompt,
            suffix=suffix,
        )
        final_prompt = objRV_fewshot_prompt.format(
            input_sentence=input_sentence, upper_objective=upper_objective
        )
    else:
        final_prompt = prefix + suffix

    print(type(final_prompt))
    print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    objRV_chain = ConversationChain(llm=llm)

    objRV_res = objRV_chain.run(final_prompt)

    objRV_res = parse_data(objRV_res)
    return objRV_res


res2 = objRV(
    "밥을 먹는다",
    "배불러진다",
    "밥을 먹으면 어떤 상태가 될까요?",
    objRV_examples,
    "밥을 먹는 것은 배부른 것과 관련성이 큽니다",
    True,
    True,
)

print(res2)
