import requests
import torch.multiprocessing as mp
import torch
import re

if __name__=="__main__":
    mp.set_start_method('spawn', force=True) 

#async
from celery_server import capp
from model import return_gpu_model, change_model, return_now_name
from repo import update_okr_score_and_reason

### llama
llama_input_template = """
상위목표 = {upper_objective}
핵심결과 = {input_sentence}
"""


###
llama_system_prompt_template = {}

llama_system_prompt_template["align"] = """
"""

llama_system_prompt_template["value"] = """
"""

llama_system_prompt_template["goal"] = """
"""

llama_system_prompt_template["connectivity"] = """
당신은 상위목표를 토대로 핵심결과를 평가하는 전문가입니다.
평가기준은 '연결성'입니다. 하단에 있는 연결성의 평가기준에 대한 설명을 보고, 이를 엄격히 준수해서 평가합니다.
# 연결성의 평가기준
## 평가기준에 대한 설명
연결성은 반드시 다음과 같은 두 가지 기준으로 평가합니다.
기준 1. 상위목표의 달성에 핵심결과가 기여하는가? 즉, 상위목표와 핵심결과가 연관되는가?
기준 2. 핵심결과 문장이 나타내는 바가 구체적이고 명확한가?
## 평가기준에 따른 점수
평가기준에 대한 설명을 반드시 엄격히 준수합니다. 그리고 평가기준을 만족하는 정도에 따라 점수를 다르게 주세요.
기준 1이 가장 중요한 평가 척도이므로, 기준 1을 만족하지 못하면 반드시 낮은 점수를, 만족하면 높은 점수를 줍니다.
4~5점: 기준 1과 기준 2를 모두 만족한다.
3~3.5점: 기준 1은 만족하지만, 기준 2는 만족하지 못한다.
2~2.5점: 기준2는 만족하지만, 기준 1은 만족하지 못한다.
1~1.5점: 기준 1과 기준 2를 모두 만족하지 못한다.
# 출력
출력은 반드시 아래와 같은 형식을 엄격히 지켜주세요.
## 출력에 대한 설명
이유는 반드시 한국어의 문법적 형식을 갖춘 완전한 한국어로만 이루어진 문장이어야 하며, '(이)다'라는 종결어미로 끝나야 합니다.
이유는 연결성의 평가기준에 기반하여 평가기준을 만족하지 못한 혹은 평가기준을 만족한 이유에 대해 서술해야합니다.
## 출력 형식
이유: [한국어로 된 완전한 문장]
점수: [1부터 5사이의 이유에 따른 점수, 소수점 단위 0.5]
"""

llama_system_prompt_template["measurability"] = """
"""

llama_system_prompt_template["directivity"] = """
"""


llama_krRV_template = """
<입력>
상위목표 = {upper_objective}
핵심결과 = {input_sentence}
기업명 = {company}
업종 = {field}
조직명 = {team}
</입력>
"""

llama_objRV_template = """
<입력>
상위목표 = {upper_objective}
목표 = {input_sentence}
기업명 = {company}
업종 = {field}
조직명 = {team}
</입력>
"""

llama_system_prompt_RV_template = """
당신은 OKR 문장 교정 전문가입니다. 
다음은 평가 기준입니다.
{rv_d}
다음은 문장에 대한 부가 정보입니다.
{context} 

부가 정보를 고려하여 문장이 평가 기준에 완전히 부합하도록 교정해주세요.

반드시 아래의 출력 형식을 지키십시오.
교정문장: [교정 문장]
"""

# +
##polyglot
polyglot_keyresult_template = """
###맥락:
상위목표 = {upper_objective}
핵심결과 = {keyresult}
업종 = {field}.
조직명 = {team}.

###답변:
점수:"""

polyglot_objective_template = """
###맥락:
상위목표 = {upper_objective}
현재목표 = {objective}
업종 = {field}.
조직명 = {team}.

###답변:
점수:"""


polyglot_system_prompt_template = dict()

polyglot_system_prompt_template["align"] = """
###질문:
당신은 문장 평가 전문가입니다.
평가기준은 '얼라인'입니다. 평가기준에 대한 설명을 보고, 이를 엄격히 준수해서 평가합니다. 상위목표가 '최상위 O'라면 현재목표가 최상위 목표라는 것을 의미합니다.
평가 기준에 따라 평가할 때, 상위목표, 업종, 조직명을 반드시 참고해 주십시오.

<평가기준>
## 평가기준에 대한 설명
얼라인은 다음과 같은 두 가지 기준으로 평가합니다.
기준 1. 현재 목표가 최상위 목표가 아니라면 상위목표와 현재목표의 전략적 연결이 있는가?
기준 2. 상위목표와 현재목표의 전략적 연결이 직접적인가?
기준 3. 현재 목표의 초점이 명확한가?
## 평가기준에 따른 점수
평가기준에 대한 설명을 반드시 엄격히 준수합니다. 그리고 평가기준을 만족하는 정도에 따라 점수를 다르게 주세요.
4.5~5점: 기준 1과 기준 2, 기준 3을 모두 만족한다.
3~4점: 기준 1과 기준 2는 만족하지만, 기준 3을 만족하지 못한다.
2~2.5점: 기준 1은 만족하지만, 기준 2와 기준 3을 만족하지 못한다.
1~1.5점: 기준 1과 기준 2, 기준 3을 모두 만족하지 못한다.

<출력>
출력은 반드시 아래와 같은 형식을 엄격히 지켜주세요.

점수: [1부터 5사이의 점수, 소수점 단위 0.5]
이유: [점수를 준 이유]
"""

polyglot_system_prompt_template["value"] = """
###질문:
당신은 문장 평가 전문가입니다.
평가기준은 '고객가치'입니다. 평가기준에 대한 설명을 보고, 이를 엄격히 준수해서 평가합니다.
평가 기준에 따라 평가할 때, 상위목표, 업종, 조직명을 반드시 참고해 주십시오.

<평가기준>
## 평가기준에 대한 설명
고객가치는 다음과 같은 두 가지 기준으로 평가합니다.
기준 1. 고객에게 제공하는 가치가 현재 고객에게 필요한가?
기준 2. 고객가치를 명확히 표현했는가?
기준 3. 고객에 관한 문제가 있는가?
## 평가기준에 따른 점수
평가기준에 대한 설명을 반드시 엄격히 준수합니다. 그리고 평가기준을 만족하는 정도에 따라 점수를 다르게 주세요.
4.5~5점: 기준 1과 기준 2를 만족한다.
3~4점: 기준2는 만족하지만, 기준 1은 만족하지 못한다.
2~2.5점: 기준 3은 만족하지만, 기준 1, 기준 2는 만족하지 못한다.
1~1.5점: 기준 1과 기준 2, 기준 3을 모두 만족하지 못한다.

<출력>
출력은 반드시 아래와 같은 형식을 엄격히 지켜주세요.

점수: [1부터 5사이의 점수, 소수점 단위 0.5]
이유: [점수를 준 이유]
"""
polyglot_system_prompt_template["goal"] = """
"""

polyglot_system_prompt_template["connectivity"] = """
###질문:
당신은 문장 평가 전문가입니다.
평가기준은 '연결성'입니다. 평가기준에 대한 설명을 보고, 이를 엄격히 준수해서 평가합니다.
평가 기준에 따라 평가할 때, 상위목표, 업종, 조직명을 반드시 참고해 주십시오.

<평가기준>
## 평가기준에 대한 설명
연결성은 다음과 같은 두 가지 기준으로 평가합니다.
기준 1. 상위목표를 달성하는 데 핵심결과가 기여하는가?
기준 2. 핵심결과 문장이 나타내는 바가 구체적이고 명확한가?
## 평가기준에 따른 점수
평가기준에 대한 설명을 반드시 엄격히 준수합니다. 그리고 평가기준을 만족하는 정도에 따라 점수를 다르게 주세요.
4.5~5점: 기준 1과 기준 2를 모두 만족한다.
3~4점: 기준 1은 만족하지만, 기준 2는 만족하지 못한다.
2~2.5점: 기준2는 만족하지만, 기준 1은 만족하지 못한다.
1~1.5점: 기준 1과 기준 2를 모두 만족하지 못한다.

<출력>
출력은 반드시 아래와 같은 형식을 엄격히 지켜주세요.

점수: [1부터 5사이의 점수, 소수점 단위 0.5]
이유: [점수를 준 이유]
"""

polyglot_system_prompt_template["measurability"] = """
###질문:
당신은 문장 평가 전문가입니다.
평가기준은 '측정 가능성'입니다. 평가기준에 대한 설명을 보고, 이를 엄격히 준수해서 평가합니다.
평가 기준에 따라 평가할 때, 상위목표, 업종, 조직명을 반드시 참고해 주십시오.

<평가기준>
## 평가기준에 대한 설명
측정 가능성은 다음과 같은 세 가지 기준으로 평가합니다.
기준 1. 측정할 대상이 있는가?
기준 2. 측정 대상을 측정할 수 있는가?
기준 3. 측정 대상이 양적으로 평가되는가?
## 평가기준에 따른 점수
평가기준에 대한 설명을 반드시 엄격히 준수합니다. 그리고 평가기준을 만족하는 정도에 따라 점수를 다르게 주세요.
5점: 기준 1과 기준 2, 기준 3을 모두 만족한다.
3.5~4.5점: 기준 1과 기준 2는 만족하지만, 기준 3을 만족하지 못한다. 
2~3점: 기준 1은 만족하지만, 기준 2와 기준 3은 만족하지 못한다.
1~1.5점: 기준 1과 기준 2, 기준 3을 모두 만족하지 못한다.

<출력>
출력은 반드시 아래와 같은 형식을 엄격히 지켜주세요.

점수: [1부터 5사이의 점수, 소수점 단위 0.5]
이유: [점수를 준 이유]
"""

polyglot_system_prompt_template["directivity"] = """
###질문:
당신은 문장 평가 전문가입니다.
평가기준은 '결과 지향성'입니다. 평가기준에 대한 설명을 보고, 이를 엄격히 준수해서 평가합니다.
평가 기준에 따라 평가할 때, 상위목표, 업종, 조직명을 반드시 참고해 주십시오.

<평가기준>
## 평가기준에 대한 설명
결과 지향성은 다음과 같은 두 가지 기준으로 평가합니다.
기준 1. 핵심결과 문장이 방향, 행동이 아닌 결과를 평가하는가?
기준 2. 핵심결과 문장에 '무엇이 달라지는가'와 '얼마나 달라지는가'가 명시되어있는가?
## 평가기준에 따른 점수
평가기준에 대한 설명을 반드시 엄격히 준수합니다. 그리고 평가기준을 만족하는 정도에 따라 점수를 다르게 주세요.
4.5~5점: 기준 1과 기준 2를 모두 만족한다.
3.5~4점: 기준 1은 만족하지만, 기준 2는 만족하지 못한다.
2.5~3점: 기준2는 만족하지만, 기준 1은 만족하지 못한다.
1~2점: 기준 1과 기준 2를 모두 만족하지 못한다.

<출력>
출력은 반드시 아래와 같은 형식을 엄격히 지켜주세요.

점수: [1부터 5사이의 점수, 소수점 단위 0.5]
이유: [점수를 준 이유]
"""


# +
##gemma

gemma_input_template = """
<start_of_turn>user
<입력>
업종 = {field}
팀명 = {team}
상위목표 = {upper_objective}
핵심결과 = {input_sentence}
<end_of_turn>
</입력>
"""
gemma_system_prompt_template = dict()

gemma_system_prompt_template["align"] = """
"""

gemma_system_prompt_template["value"] = """
"""

gemma_system_prompt_template["goal"] = """
"""


gemma_system_prompt_template["connectivity"] = """
당신은 OKR(Objectives and Key Results) 전문가입니다. 현재, 입력된 세부 목표(Key Results)의 상위목표와의 연관성을 평가하는 임무를 맡고 있습니다.
다음 정보를 바탕으로 세부 목표의 상위 목표와의 연관성을 1에서 5점 중 하나로 평가하세요.
1점 = 완전 무관
2점 = Objective 구현과는 연결성이 있다고 보기 어렵지만, 향후 매우 간접적으로 영향을 주고 받을 수 있다고 볼 수 있는 경우
3점 = Objective 구현을 설명하는 필수/핵심 요소나 구현된 모습이라고 볼 수 없으나 연결을 충분히 설명할 수 있는 경우
4점 = 5점과 3점 사이에서 판단
5점 = Objective 구현에 필수적이고 핵심적인 요소인 경우, Objective가 구현된 구체적인 결과/모습인 경우
상위 목표와의 연관성 이유를 먼저 생각하고 이에 기반해서 1-5점 사이의 점수를 내려주세요.당신의 답변이 확신을 주어야 사람들이 당신을 유능한 모델이라고 생각할 것입니다.
출력은 한 번만 생성하세요.
<출력>
점수: [1-5 범위의 숫자]
이유: [점수를 준 이유]
</출력>
"""

gemma_system_prompt_template["measurability"] = """
당신은 OKR(Objectives and Key Results) 전문가입니다. 현재, 입력된 세부 목표(Key Results)의 측정가능성을 평가하는 임무를 맡고 있습니다.
다음 정보를 바탕으로 세부 목표의 측정 가능성을 1에서 5점 중 하나로 평가하세요.
1점 = 측정과 완전 무관한 내용
2점 = 측정할 대상은 있으나 양적으로나 질적으로 달라지는 정도가 없어서 측정이 안되는 경우
3점 = 4,5점과 1,2점 사이에서 판단
4점 = 측정 대상이 달라지는 정도가 양적으로가 아닌 정성적인 설명을 통해 측정할 수 있는 경우
5점 = 측정 대상이 양적으로 명확하게 달라지는 정도가 나타나는 경우
측정 가능성 이유를 먼저 생각하고 이에 기반해서 1-5점 사이의 점수를 내려주세요.당신의 답변이 확신을 주어야 사람들이 당신을 유능한 모델이라고 생각할 것입니다.
출력은 한 번만 생성하세요.
<출력>
점수: [1-5 범위의 숫자]
이유: [점수를 준 이유]
</출력>
"""

gemma_system_prompt_template["directivity"] = """
당신은 OKR-Objectives and Key Results 전문가입니다. 현재, 입력된 세부 목표(Key Results)의 결과 지향성을 평가하는 임무를 맡고 있습니다.
세부 목표 내용이 행위나 할 일(activity, task, input)을 나타내지 않고, 결과(output, outcome)를 나타내는지에 대해 1-5점 사이로 평가해 주세요
다음 정보를 바탕으로 세부 목표의 결과 지향성을 1에서 5점 중 하나로 평가하세요.
1점 = 결과가 아닌 방향이나 행동이나 할일로 표현된 경우
2점 = 3점과 1점 사이에서 판단
3점 = 결과를 구성하는 '무엇'은 있는데 얼마나가 없는 경우, 혹은 행동으로나 결과로 모두 설명이 가능할 때 
4점 = 5점과 3점 사이에서 판단
5점 = 방향, 행동이 아닌 결과가 명확하게 표현된 경우 
평가 이유를 먼저 생각하고 이에 기반해서 1-5점 사이의 점수를 내려주세요.당신의 답변이 확신을 주어야 사람들이 당신을 유능한 모델이라고 생각할 것입니다.
출력은 한 번만 생성하세요.
<출력>
점수: [1-5 범위의 숫자]
이유: [점수를 준 이유]
</출력>
"""



# -

def extract_data2(text):
    score_match = re.findall(r"점수:\s*([\d.]+)", text)
    description_match = re.findall(r"이유:\s*(.*)", text)
    predict_score = score_match[0].strip() if score_match else None
    predict_description = description_match[0].strip() if description_match else None
    return {"score": predict_score, "reason": predict_description}

def extract_predict_value(text):
    match = re.search(r'<출력>(.*?)<end_of_turn>', text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        score_match = re.search(r'점수:\s*(\d+\.?\d*)', content)
        reason_match = re.search(r'이유:\s*(.*)', content)
        
        score = score_match.group(1) if score_match else None
        reason = reason_match.group(1).strip() if reason_match else None
        
        return {'score': score, 'reason': reason}
    return {'score': None, 'reason': None}

def polyglot_score_and_reason(text):
    pattern = r"###답변:\s*점수\s*:\s*(\d+(\.\d+)?)(?:\s*.*?)?\s*이유\s*:\s*(.*?)(?=\n|$)"
    match = re.search(pattern, text, re.DOTALL)
    
    result = {
            "score": None,
            "reason": None
    }
    if match:
        result = {
            "score": float(match.group(1)),
            "reason": match.group(3).strip()
        }
    return result


@capp.task(ignore_result=False)
def eval_generate(request_data, eval_type):
    name = return_now_name()
    predict_value = {"score": None, "reason": None}

    if name == "llama":
        text = llama_input_template.format(upper_objective=request_data["upper_objective"], input_sentence=request_data["input_sentence"])
        system_prompt = ""
        if request_data["isObjective"] == True:
            if eval_type == 0:
                system_prompt = llama_system_prompt_template["align"]
            elif eval_type == 1:
                system_prompt = llama_system_prompt_template["value"]
            else:
                system_prompt = llama_system_prompt_template["goal"]
        else:
            if eval_type == 0:
                system_prompt = llama_system_prompt_template["connectivity"]
            elif eval_type == 1:
                system_prompt = llama_system_prompt_template["measurability"]
            else:
                system_prompt = llama_system_prompt_template["directivity"]

        tokenizer, model = return_gpu_model()
        
        messages = [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{text}"}
        ]

        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)

        attention_mask = (input_ids != tokenizer.pad_token_id).long().to(model.device)
        
        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                attention_mask=attention_mask,  # Add attention mask
                max_new_tokens=512,
                eos_token_id=terminators,
                pad_token_id=tokenizer.eos_token_id,  # Set pad token ID to eos token ID
                do_sample=True,
                temperature=0.6,
                top_p=0.9
            )

        torch.cuda.empty_cache()
        result = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
        predict_value = extract_data2(result)
        
    elif name == "polyglot":
        text = ""
        system_prompt = ""
        if request_data["isObjective"] == True:
            text = polyglot_objective_template.format(upper_objective=request_data["upper_objective"], objective=request_data["input_sentence"], field = request_data["field"], team = request_data["team"])
            if eval_type == 0:
                system_prompt = polyglot_system_prompt_template["align"]
            else:
                system_prompt = polyglot_system_prompt_template["value"]
        else:
            text = polyglot_keyresult_template.format(upper_objective=request_data["upper_objective"], keyresult=request_data["input_sentence"], field = request_data["field"], team = request_data["team"])
            if eval_type == 0:
                system_prompt = polyglot_system_prompt_template["connectivity"]
            elif eval_type == 1:
                system_prompt = polyglot_system_prompt_template["measurability"]
            else:
                system_prompt = polyglot_system_prompt_template["directivity"]
        
        tokenizer, model = return_gpu_model()
        
        input_text = system_prompt + text
        inputs = tokenizer(input_text, return_tensors="pt", add_special_tokens=False, return_token_type_ids=False).to(model.device)
    
        generate_kwargs = dict(
            input_ids=inputs["input_ids"],
            max_length=1024,
            do_sample=True,  # Enable sampling
            top_p=0.92,
            top_k=50,
            temperature=0.2,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id= tokenizer.eos_token_id,
            repetition_penalty=1.2,
        )

        with torch.no_grad():
            outputs = model.generate(**generate_kwargs)

        torch.cuda.empty_cache()
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        predict_value = polyglot_score_and_reason(result)

    elif name == "gemma":    
        text = gemma_input_template.format(field=request_data["field"], team=request_data["team"], upper_objective=request_data["upper_objective"], input_sentence=request_data["input_sentence"])
        system_prompt = ""
        if request_data["isObjective"] == True:
            if eval_type == 0:
                system_prompt = gemma_system_prompt_template["align"]
            elif eval_type == 1:
                system_prompt = gemma_system_prompt_template["value"]
            else:
                system_prompt = gemma_system_prompt_template["goal"]
        else:
            if eval_type == 0:
                system_prompt = gemma_system_prompt_template["connectivity"]
            elif eval_type == 1:
                system_prompt = gemma_system_prompt_template["measurability"]
            else:
                system_prompt = gemma_system_prompt_template["directivity"]
        
            
        tokenizer, model = return_gpu_model()
        
        messages = [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{text}"}
        ]
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        
        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_new_tokens=100,
                eos_token_id=terminators,
                do_sample=True,
                temperature=0.2,
                top_p=0.9
            )
        
        torch.cuda.empty_cache()
        result = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
        predict_value = extract_predict_value(result)
        
    #requests.post('http://localhost:12000/task_completed', json={'result': predict_score})
    msg = update_okr_score_and_reason(request_data["okrNum"], eval_type, predict_value["score"], predict_value["reason"])
    return predict_value

@capp.task(ignore_result=False)
def rev_generate(request_data):
    name = return_now_name()
    result = ""
    if name == "llama":
        context = ""
        system_prompt = ""
        text = ""
        if request_data["isObjective"] == False:
            rv_d = ""
            text = llama_krRV_template.format(upper_objective=request_data["upper_objective"], input_sentence=request_data["input_sentence"], company = request_data["company"], field = request_data["field"], team = request_data["team"])
            system_prompt = llama_system_prompt_RV_template.format(rv_d=rv_d, context=context)
        else:
            rv_d = ""
            text = llama_objRV_template.format(upper_objective=request_data["upper_objective"], input_sentence=request_data["input_sentence"], company = request_data["company"], field = request_data["field"], team = request_data["team"])
            system_prompt = llama_system_prompt_RV_template.format(rv_d=rv_d, context=context)
            
    
        tokenizer, model = return_gpu_model()

        messages = [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": f"{text}"}
            ]

        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)

        attention_mask = (input_ids != tokenizer.pad_token_id).long().to(model.device)
        
        terminators = [
            tokenizer.eos_token_id,
            tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                attention_mask=attention_mask,  # Add attention mask
                max_new_tokens=512,
                eos_token_id=terminators,
                pad_token_id=tokenizer.eos_token_id,  # Set pad token ID to eos token ID
                do_sample=True,
                temperature=0.6,
                top_p=0.9
            )

        torch.cuda.empty_cache()
        result = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
    elif name == "polyglot":
        pass
    elif name == "gemma":
        pass
    
    #requests.post('http://localhost:12000/task_completed', json={'result': result})
    return {"revision": result}


@capp.task(ignore_result=False)
def change(model_name):
    return {"success": change_model(model_name)}
