import google.generativeai as genai
import re
import json
from config import GOOGLE_API_KEY

# llm model
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash-001")

def text_to_json(text):
    if text:
        cleaned_text = re.sub(r"\*\*", "", text.strip())
        if not cleaned_text.strip():
            cleaned_text = None
    else:
        cleaned_text = None

    # JSON 형태로 반환
    result = {"Guideline": cleaned_text}
    return result

def key_result_query(company_name, department_name, objective, context):
    def generate_key_query_prompt(company_name, department_name, objective, context):
        prompt_template = f"""
            # Guideline
            ## Background
            You are a Korean OKR expert.
            Read the content of the {context} of the {company_name} company and familiarize yourself with the company's goals.
            After that, you will establish Key Results for a department named {department_name}.
            The department's OKRs must be subordinate goals that contribute to achieving the company's goals as outlined in {context}.
            The Objective of the department is '{objective}'.
            ## Instruction
            Now, you need to create questions for Key Results aligned with the above Objective.
            Create 5 detailed, most important, and critical questions to establish the department's Key Results aligned with the Objective.
            These questions will serve as guidelines for generating Key Results.
            The instructions for the questions are as follows: Key Results should be based on the following three criteria: Connectivity, Measurability, and Result Directivity.
            - Connectivity indicates how well the Key Result is connected to the Objective.
            - Measurability indicates whether the Key Result can be quantitatively measured, including defining the subjects and criteria for measurement.
            - Result Directivity indicates whether the content represents results (output, outcome) rather than activities, tasks, or inputs.
            Keep in mind that Key Results are generated based on these criteria.
            # Output
            Outputs must be in Korean, and should not include any other information.
            Please output the following JSON data in text format, excluding the JSON code block (json ``` etc.).
            Maintain the data structure exactly as it is, but present it in plain text without the JSON block.
            ## Format
            Question: Nth detailed question,
            Connectivity: Follow-up question related to Connectivity?,
            Measurability: Follow-up question related to Measurability?,
            Directivity: Follow-up question related to Result Directivity?

            Return the output in format with 3 questions in for.
        """

        return prompt_template

    key_query_prompt = generate_key_query_prompt(company_name, department_name, objective, context)
    key_query_response = model.generate_content(contents=key_query_prompt)
    response = key_query_response.text
    json_response = text_to_json(response)

    return json_response

# company_name='CJ씨푸드'
# company_type='food'
# company_type_kor='식품'
# department_name='우리맛연구팀'
# objective='간편한 한끼 식사로 균형잡힌 영양을 제공한다'
# context='곡류, 고기나 생선류, 채소류, 과일류, 유제품류, 유지류 등 총 6가지의 식품으로 짜인 밥상이 균형 잡힌 식단이라고 볼 수 있습니다. 이는 각 식품군이 우리 몸에 필요한 다양한 영양소를 제공하기 때문입니다. 특히 간편한 한 끼 식사를 위해서는 모든 영양소를 고루 섭취하는 균형 잡힌 식단이 중요합니다. 균형 잡힌 식사는 단순히 맛있게 먹는 것을 넘어 건강을 유지하고 질병을 예방하는 데 중요한 역할을 합니다. 따라서 식료품을 선택할 때는 단순히 맛이나 가격뿐만 아니라 영양적인 균형도 고려해야 합니다.'

# print(key_result_query(company_name, department_name, objective, context))

def objective_query(company_name, department_name, upper_objective, context):
    def generate_o_query_prompt(company_name, department_name, upper_objective, context):
        prompt_template = f"""
        #Guideline
        ##Background
        You are Korean OKR expert.
        Read the {context} content of the {company_name} company and familiarize yourself with the company's goals.
        After that, you will establish Objective for a department named {department_name}.
        The department's OKRs must be subordinate goals that contribute to achieving the company's goals as outlined in {context}.
        Upper-Objective of the department is {upper_objective}.
        ## Insturction
        So now you want to create questions for Objective due to the upper-objective above.
        Create 3 detailed, most important, and critical questions to establish the department's Objectives due to successing {upper_objective}, and you will also generate some follow-up questions for 3 detailed questions.
        These questions serve as guidelines for generating Objectives. And you will also generate some follow-up questions for 3 detailed questions.
        And the instructions for the questions are as follows. Objectives should be based on the following three criteria: Align, Customer Recognition, and Customer Value.
        Align indicates how well the Objective is connected to the upper-objective, Customer Recognition indicates whether the Objective specifies the target customers or clearly mentions the customers, and Customer Value indicates whether the Objective accurately mentions the value provided to customers or the problems it solves.

        # Output
        ## Output Insturction
        Outputs must be in Korean, and should not include any other information.
        Please output the following JSON data in text format, excluding the JSON code block (json ``` etc.).
        And Follow-up questions must include examples, and the format of examples should follow Output Format.
        Your output should strictly adhere to the Output Format.
        ## Output Format
        Question: Nth detailed question,
        Align: "Follow-up question related to Connectivity(예: example of align)?",
        Customer Recognition": "Follow-up question related to Measurability(예: exmaple of customer recognitiony)?,
        Customer Value": "Follow-up question related to Result Directivity(예: exmaple of customer value)?

        Return the output in format with 3 detailed questions.
        """

        return prompt_template

    o_query_prompt = generate_o_query_prompt(company_name, department_name, upper_objective, context)
    o_query_response = model.generate_content(contents=o_query_prompt)
    response = o_query_response.text
    json_response = text_to_json(response)

    return json_response
