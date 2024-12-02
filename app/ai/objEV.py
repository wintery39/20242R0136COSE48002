from ai.objEVprompt import obj_background_template, objEV_align_description, objEV_align_example_prompt, objEV_align_examples, objEV_align_examples_1, objEV_align_examples_2, objEV_align_examples_3, objEV_align_suffix, objEV_task_description, objEV_value_description, objEV_value_example_prompt, objEV_value_examples, objEV_value_examples_1, objEV_value_examples_2, objEV_value_examples_3, objEV_value_suffix

from langchain.prompts import PromptTemplate
from langchain.prompts import FewShotPromptTemplate
from langchain.chains import ConversationChain
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
import copy
import json
import time
import re

from ai.parse import parse_data, selfC
from ai.main import llm, train_df, test_df

def objalignEV(input_sentence, upper_objective, objEV_memory_tests, guideline_ali, example_ali, isguide, isexample):
  if isguide:
    prefix_guideline = '- 주어진 가이드라인을 평가에 이용하세요'
    guideline_ali = guideline_ali
  else:
    prefix_guideline = ' '
    guideline_ali = ' '
    for example in example_ali:
      example["guideline"] = ' '

  if isexample:
    prefix_example = '- 예시는 참고용일 뿐입니다. 현재 주어진 input_sentence와 upper_objective에 집중하여 평가하세요.'
  else:
    prefix_example = ' '

  prefix = objEV_align_description.format(prefix_guideline = prefix_guideline, prefix_example = prefix_example)
  suffix = objEV_align_suffix.format(input_sentence = input_sentence, upper_objective = upper_objective, guideline_ali = guideline_ali)

  objEV_align_fewshot_prompt = FewShotPromptTemplate(
    prefix = prefix + '\n\n',
    examples = example_ali,
    example_prompt = objEV_align_example_prompt,
    suffix = suffix
  )

  if isexample:
    final_prompt = objEV_align_fewshot_prompt.format(input_sentence=input_sentence, upper_objective=upper_objective)
  else:
    final_prompt = prefix + suffix

  # print(type(final_prompt))
  # print('*'*50, '\n', final_prompt, '\n', '*'*50)

  chain_align = ConversationChain(
    llm=llm,
    memory=objEV_memory_tests,
  )

  objEV_align = chain_align.run(final_prompt)

  res = parse_data(objEV_align)
  return res

def objvalueEV(input_sentence, upper_objective, objEV_memory_tests, guideline_val, example_val, isguide, isexample):
  if isguide:
    prefix_guideline = '- 주어진 가이드라인을 평가에 이용하세요'
    guideline_val = guideline_val
  else:
    prefix_guideline = ' '
    guideline_val = ' '
    for example in example_val:
      example["guideline"] = ' '

  if isexample:
    prefix_example = '- 예시는 참고용일 뿐입니다. 현재 주어진 input_sentence와 upper_objective에 집중하여 평가하세요.'
  else:
    prefix_example = ' '

  prefix = objEV_value_description.format(prefix_guideline = prefix_guideline, prefix_example = prefix_example)
  suffix = objEV_value_suffix.format(input_sentence = input_sentence, upper_objective = upper_objective, guideline_val = guideline_val)

  objEV_valnectivity_fewshot_prompt = FewShotPromptTemplate(
    prefix = prefix + '\n\n',
    examples = example_val,
    example_prompt = objEV_value_example_prompt,
    suffix = suffix
  )

  if isexample:
    final_prompt = objEV_valnectivity_fewshot_prompt.format(input_sentence=input_sentence, upper_objective=upper_objective)
  else:
    final_prompt = prefix + suffix

  # print(type(final_prompt))
  # print('*'*50, '\n', final_prompt, '\n', '*'*50)

  chain_value = ConversationChain(
    llm=llm,
    memory=objEV_memory_tests,
  )

  objEV_value = chain_value.run(final_prompt)

  res = parse_data(objEV_value)
  return res

def objEVsaveResult(df_data, index, result_obj):
    # predict_align_description
    try:
        df_data.loc[index, 'predict_align_description'] = str(result_obj.get('predict_align_description', 'N/A'))
    except (KeyError, ValueError, TypeError) as e:
        df_data.loc[index, 'predict_align_description'] = 'N/A'
        print(f"Error saving 'predict_align_description' for index {index}: {e}")

    # predict_align_score
    try:
        df_data.loc[index, 'predict_align_score'] = float(result_obj.get('predict_align_score', 0.0))
    except (KeyError, ValueError, TypeError) as e:
        df_data.loc[index, 'predict_align_score'] = 0.0
        print(f"Error saving 'predict_align_score' for index {index}: {e}")

    # predict_value_description
    try:
        df_data.loc[index, 'predict_value_description'] = str(result_obj.get('predict_value_description', 'N/A'))
    except (KeyError, ValueError, TypeError) as e:
        df_data.loc[index, 'predict_value_description'] = 'N/A'
        print(f"Error saving 'predict_value_description' for index {index}: {e}")

    # predict_value_score
    try:
        df_data.loc[index, 'predict_value_score'] = float(result_obj.get('predict_value_score', 0.0))
    except (KeyError, ValueError, TypeError) as e:
        df_data.loc[index, 'predict_value_score'] = 0.0
        print(f"Error saving 'predict_value_score' for index {index}: {e}")


# obj 평가

def objEV(df_data, index, isguide, isexample):
  # 메모리 생성
  obj_memory = ConversationBufferMemory()

  # 1. 메모리의 system_message에 Task Description 추가
  obj_memory.save_context(
    inputs={"human": objEV_task_description},
    outputs={"AI": "해결할 과제를 학습했습니다."},
  )

  # 1.5 df_data에서 값 가져오기
  input_sentence = df_data.loc[index, 'input_sentence']
  upper_objective = df_data.loc[index, 'upper_objective']
  company = df_data.loc[index, 'company']
  field = df_data.loc[index, 'field']
  team = df_data.loc[index, 'team']

  guideline_ali = ''
  guideline_val = ''
  if isguide:
    guideline_ali = df_data.loc[index, 'Align_Question']
    guideline_val = df_data.loc[index, 'Customer_Value_Question']

  print("index: ", index)
  print(f"row_num: {df_data.loc[index]['row_num']}")
  print("guideline_align: ", str(guideline_ali))
  print("guideline_value: ", str(guideline_val))
  print(f"input_sentence: {input_sentence}")
  print(f"upper_objective: {upper_objective}")
  print('\n')


  # 2. 메모리의 human_message에 background 정보 추가
  obj_background = obj_background_template.format(
    company=company,                  #회사명
    field=field,                      #업종
    team=team,                        #팀명
  )

  obj_memory.save_context(
    inputs={"system": obj_background},
    outputs={"AI": "기업의 배경 정보를 학습했습니다."},
  )

  # 2.5 평가요소마다 메모리 만들기
  objEV_memory_align = copy.deepcopy(obj_memory)
  objEV_memory_value = copy.deepcopy(obj_memory)

  # 평가 시행
  objEV_align = objalignEV(input_sentence, upper_objective, objEV_memory_align, guideline_ali, objEV_align_examples, isguide, isexample)
  objEV_value = objvalueEV(input_sentence, upper_objective, objEV_memory_value, guideline_val, objEV_value_examples, isguide, isexample)

  return objEV_align | objEV_value
  
def objEV_selfC(df_data, index, isguide, isexample):
  # 메모리 생성
  obj_memory = ConversationBufferMemory()

  # 1. 메모리의 system_message에 Task Description 추가
  obj_memory.save_context(
    inputs={"human": objEV_task_description},
    outputs={"AI": "해결할 과제를 학습했습니다."},
  )

  # 1.5 df_data에서 값 가져오기
  input_sentence = df_data.loc[index, 'input_sentence']
  upper_objective = df_data.loc[index, 'upper_objective']
  company = df_data.loc[index, 'company']
  field = df_data.loc[index, 'field']
  team = df_data.loc[index, 'team']

  guideline_ali = ''
  guideline_val = ''
  if isguide:
    guideline_ali = df_data.loc[index, 'Align_Question']
    guideline_val = df_data.loc[index, 'Customer_Value_Question']

  print("index: ", index)
  print(f"row_num: {df_data.loc[index]['row_num']}")
  print("guideline_align: ", guideline_ali)
  print("guideline_value: ", guideline_val)
  print(f"input_sentence: {input_sentence}")
  print(f"upper_objective: {upper_objective}")
  print('\n')


  # 2. 메모리의 human_message에 background 정보 추가
  obj_background = obj_background_template.format(
    company=company,                  #회사명
    field=field,                      #업종
    team=team,                        #팀명
  )

  obj_memory.save_context(
    inputs={"system": obj_background},
    outputs={"AI": "기업의 배경 정보를 학습했습니다."},
  )

  # 2.5 평가요소마다 메모리 만들기
  objEV_memory_align = copy.deepcopy(obj_memory)
  objEV_memory_value = copy.deepcopy(obj_memory)

  # 평가 시행
  objEV_align = selfC(objalignEV, input_sentence, upper_objective, objEV_memory_align, guideline_ali, objEV_align_examples_1, objEV_align_examples_2, objEV_align_examples_3, isguide, isexample, "align")
  objEV_value = selfC(objvalueEV, input_sentence, upper_objective, objEV_memory_value, guideline_val, objEV_value_examples_1, objEV_value_examples_2, objEV_value_examples_3, isguide, isexample, "value")

  # 결과 저장, 문자열 메소드 이용
  objEVsaveResult(df_data, index, objEV_align | objEV_value)

  #결과 출력
  # print("<obj evaluation>")
  # print(f"predict_align_score: {df_data.loc[index, 'predict_align_score']}")
  # print(f"predict_align_description: {df_data.loc[index, 'predict_align_description']}")
  # print(f"predict_value_score: {df_data.loc[index, 'predict_value_score']}")
  # print(f"predict_value_description: {df_data.loc[index, 'predict_value_description']}")
  # print('\n')
  
  
res = objEV(test_df, 10, True, True)
print(res)
print(type(res))