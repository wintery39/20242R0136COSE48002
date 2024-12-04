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

from ai.llm_select import llm
from ai.parse import EV_parse_data, RV_parse_data
from ai.selfC import whowins


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
        obj_prefix = objEV_align_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    elif objtype == 1:  # value
        obj_prefix = objEV_value_description.format(
            prefix_guideline=prefix_guideline, prefix_example=prefix_example
        )
    else:  # error
        print("objtype parameter를 다시 확인하십시오. 0,1 중 하나여야 합니다.")

    # suffix(평가 문장 등 정보 담음)
    obj_suffix = objEV_suffix.format(
        guideline=guideline,
        input_sentence=input_sentence,
        upper_objective=upper_objective,
    )

    if isexample:
        objEV_fewshot_prompt = FewShotPromptTemplate(
            prefix=obj_prefix + "\n\n",
            examples=example,
            example_prompt=objEV_example_prompt,
            suffix=obj_suffix,
        )
        final_prompt = objEV_fewshot_prompt.format()
    else:
        final_prompt = obj_prefix + obj_suffix

    print(type(final_prompt))
    print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    objEV_chain = ConversationChain(
        llm=llm,
        memory=memory,
    )

    objEV_res = objEV_chain.run(final_prompt)

    objEV_res = EV_parse_data(objEV_res)
    return objEV_res


# res2 = objEV(
#     "식량을 많이 준비한다.",
#     "살아남는다.",
#     "출력 양식을 잘 지키십시오",
#     objEV_align_examples,
#     True,
#     True,
#     0,
# )
# print(res2)


def objEV_selfC(
    input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
):
    res1 = objEV(
        input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
    )

    description1 = res1["description"]
    score1 = res1["score"]

    res2 = objEV(
        input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
    )

    description2 = res2["description"]
    score2 = res2["score"]

    res3 = objEV(
        input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
    )

    description3 = res3["description"]
    score3 = res3["score"]

    return whowins(description1, description2, description3, score1, score2, score3)


# res1 = objEV_selfC(
#     "식량을 많이 준비한다.",
#     "살아남는다.",
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
    print(objRV_res)

    objRV_res = RV_parse_data(objRV_res)
    return objRV_res


# res2 = objRV(
#     "백화점에 간다.",
#     "친구 생일을 준비한다.",
#     "백화점에는 선물이 많이 있습니다.",
#     objRV_examples,
#     "생일에는 보통 선물을 사 주므로 연관성이 있습니다. ",
#     True,
#     True,
# )

# print(res2)