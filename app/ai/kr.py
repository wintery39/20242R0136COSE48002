import warnings

warnings.filterwarnings("ignore")


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

from ai.llm_select import llm
from ai.parse import EV_parse_data, RV_parse_data
from ai.selfC import whowins


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

    # print(type(final_prompt))
    # print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    krEV_chain = ConversationChain(
        llm=llm,
        memory=keyResult_memory,
    )

    krEV_res = krEV_chain.run(final_prompt)
    # print(krEV_res)

    krEV_res = EV_parse_data(krEV_res)
    return krEV_res


def krEV_selfC(
    input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
):
    res1 = krEV(
        input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
    )
    print(res1)
    description1 = res1["description"]
    score1 = res1["score"]
    print("res1", description1, score1)

    res2 = krEV(
        input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
    )
    description2 = res2["description"]
    score2 = res2["score"]
    print("res2", description2, score2)

    res3 = krEV(
        input_sentence, upper_objective, guideline, example, isguide, isexample, krtype
    )
    description3 = res3["description"]
    score3 = res3["score"]
    print("res3", description3, score3)

    return whowins(description1, description2, description3, score1, score2, score3)


# res = krEV_selfC(
#     "밥을 먹는다",
#     "건강해진다",
#     "출력 양식을 잘 지키십시오",
#     krEV_connectivity_examples,
#     True,
#     True,
#     0,
# )

# print(res)

# res1 = krEV(
#     "밥을 먹는다",
#     "건강해진다",
#     "출력 양식을 잘 지키십시오",
#     krEV_connectivity_examples,
#     True,
#     True,
#     0,
# )

# print(res1)

# res2 = krEV(
#     "밥을 먹는다",
#     "건강해진다",
#     "출력 양식을 잘 지키십시오",
#     krEV_connectivity_examples,
#     True,
#     True,
#     0,
# )

# print(res2)

# res3 = krEV(
#     "밥을 먹는다",
#     "건강해진다",
#     "출력 양식을 잘 지키십시오",
#     krEV_connectivity_examples,
#     True,
#     True,
#     0,
# )

# res = whowins(
#     res1["score"],
#     res2["score"],
#     res3["score"],
#     res1["description"],
#     res2["description"],
#     res3["description"],
# )
# print(res)


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

    # print(type(final_prompt))
    # print("*" * 50, "\n", final_prompt, "\n", "*" * 50)

    krRV_chain = ConversationChain(llm=llm)

    krRV_res = krRV_chain.run(final_prompt)
    # print(krRV_res)

    krRV_res = RV_parse_data(krRV_res)
    return krRV_res


# erstr = """
#     "description" : "밥을 잘 먹는다"
#     "score" :

# """
# err2 = "descritpino"
# tres = EV_parse_data(erstr)
# print(tres)

# res2 = krEV(
#     "LVUP를 켜고 게임을 한다.",
#     "LVUP 오거나이저 기능 활용의 다변화 시도",
#     "오거나이저 기능을 활용해보는 상황이 나온다",
#     krEV_connectivity_examples,
#     True,
#     True,
#     0,
# )

# print(res2)