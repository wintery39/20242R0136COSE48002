from ai.krRVprompt import krRV_example_prompt, krRV_examples, krRV_examples_1, krRV_examples_2, krRV_examples_3, krRV_suffix, krRV_task_description, kr_background_template

from langchain.prompts import PromptTemplate
from langchain.prompts import FewShotPromptTemplate
from langchain.chains import ConversationChain
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
import copy
import json
import time
import re

from ai.main import llm, train_df, test_df
from ai.parse import parse_data

def krRV1(input_sentence, upper_objective, ex_description, guideline_krRV, example_krRV, isguide, isexample):
    # 메모리 생성
  kr_memory = ConversationBufferMemory()

  # 1. 메모리의 system_message에 Task Description 추가
  kr_memory.save_context(
    inputs={"human": krRV_task_description},
    outputs={"AI": "해결할 과제를 학습했습니다."},
  )
  
  if isguide:
    prefix_guideline = '- 주어진 가이드라인을 수정에 이용하세요'
    guideline_krRV = guideline_krRV
  else:
    prefix_guideline = ' '
    guideline_krRV = ' '
    for example in example_krRV:
      example["guideline"] = ' '

  if isexample:
    prefix_example = '- 예시는 참고용일 뿐입니다. 현재 주어진 문장에 집중하여 수정하세요.'
  else:
    prefix_example = ' '

  prefix = krRV_task_description.format(prefix_guideline = prefix_guideline, prefix_example = prefix_example)
  suffix = krRV_suffix.format(input_sentence = input_sentence, upper_objective = upper_objective,
                              ex_description = ex_description,
                              guideline_krRV = guideline_krRV)

  krRV_fewshot_prompt = FewShotPromptTemplate(
    prefix = prefix,
    examples = example_krRV,
    example_prompt = krRV_example_prompt,
    suffix = suffix
  )

  if isexample:
    final_prompt = krRV_fewshot_prompt.format(prefix_guideline = prefix_guideline, prefix_example = prefix_example)
  else:
    final_prompt = prefix + suffix

  # print(type(final_prompt))
  # print('*'*50, '\n', final_prompt, '\n', '*'*50)

  chain_krRV = ConversationChain(
    llm=llm,
    memory=kr_memory,
  )

  krRV = chain_krRV.run(final_prompt)

  res = parse_data(krRV)
  return res

# res = krRV1("밥을 먹는다", "건강해진다", "두 문장은 연관성이 높습니다", "측정은 어렵습니다. 직접성이 있습니다. 평가 요소를 살피십시오", krRV_examples_1, True, True)
# print(res)
# print(type(res))

# def krRVsaveResult(df_data, index, result_kr):

#   # df_data에 값 저장
#   df_data.loc[index, 'predict_revision_description'] = str(result_kr['predict_revision_description'])
#   df_data.loc[index, 'predict_revision'] = str(result_kr['predict_revision'])

# def krRV(df_data, index, isguide, isexample):
#   # 메모리 생성
#   kr_memory = ConversationBufferMemory()

#   # 1. 메모리의 system_message에 Task Description 추가
#   kr_memory.save_context(
#     inputs={"human": krRV_task_description},
#     outputs={"AI": "해결할 과제를 학습했습니다."},
#   )

#   # 1.5 df_data에서 값 가져오기
#   input_sentence = df_data.loc[index, 'input_sentence']
#   upper_objective = df_data.loc[index, 'upper_objective']

#   predict_connectivity_description = df_data.loc[index, 'predict_connectivity_description']
#   predict_measurability_description = df_data.loc[index, 'predict_measurability_description']
#   predict_directivity_description = df_data.loc[index, 'predict_directivity_description']

#   company = df_data.loc[index, 'company']
#   field = df_data.loc[index, 'field']
#   team = df_data.loc[index, 'team']
  
#   if (df_data.loc[index, "type"] != "Key Result"):
#     print("Key Result가 아닙니다.")
#     return

#   guideline_krRV = ''
#   if isguide:
#     guideline_krRV = df_data.loc[index, 'Keyresult_Question']

#   print("index: ", index)
#   print(f"row_num: {df_data.loc[index]['row_num']}")
#   print("guideline_RV: ", str(guideline_krRV))
#   print(f"input_sentence: {input_sentence}")
#   print(f"upper_objective: {upper_objective}")
#   print('\n')


#   # 2. 메모리의 human_message에 background 정보 추가
#   kr_background = kr_background_template.format(
#     company=company,                  #회사명
#     field=field,                      #업종
#     team=team,                        #팀명
#   )

#   kr_memory.save_context(
#     inputs={"system": kr_background},
#     outputs={"AI": "기업의 배경 정보를 학습했습니다."},
#   )

#   # 2.5 평가요소마다 메모리 만들기
#   krRV_memory= copy.deepcopy(kr_memory)


#   # 평가 시행
#   krRV = krRV1(input_sentence, upper_objective, krRV_memory,
#               predict_connectivity_description, predict_measurability_description,predict_directivity_description,
#               guideline_krRV, krRV_examples, isguide, isexample)

#   return krRV

# res = krRV(test_df, 59, True, True)
# print(res)