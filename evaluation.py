#!/usr/bin/env python
# coding: utf-8
# %%
from flask import Flask, request, jsonify
from flask_restx import Resource, Namespace, fields, reqparse
import torch
from tasks import eval_generate


# %%
llama_kr_template = """
상위목표 = {upper_objective}
세부목표 = {input_sentence}
업종 = {field}.
팀명 = {team}.
###답변
점수 :"""


llama_obj_template = """
상위목표 = {upper_objective}
목표 = {input_sentence}
업종 = {field}.
팀명 = {team}.
###답변
점수 :"""


###
llama_system_prompt_template = """
###질문
{evaluate_d} 점수는 몇 점이고 그 이유는 무엇입니까?
###맥락
{context}
##답변 형식
```
점수 :<{score_type}에 대한 점수><|sep|>이유 :<해당 점수를 준 이유>
```
"""
###
evaluate_d = ""
context = ""



### Flask 관련 코드
EV = Namespace(name='EV', description='EV')

EV_fields = EV.model('EV', {
    'okrNum' : fields.Integer(required=True, description="The okrNum", example=3),
    'isObjective' : fields.Boolean(required=False, description='The objective', example=False),
    #'score_type': fields.String(required=True, description='The score type', example='연관성'),
    'upper_objective': fields.String(required=True, description='The upper objective', example='고객이 하루에 한 끼는 요리를 하고 싶게 한다.'),
    'input_sentence' : fields.String(required=True, description='The input sentence', example='일상 요리들의 조리 과정을 50% 줄일 수 있는 제품+요리법을 연구, 개발한다.'),
    'company' : fields.String(required=True, description='The company', example='회사명'),
    'field' : fields.String(required=True, description='The field', example='식품'),
    'team' : fields.String(required=True, description='The team', example='조직명')
    #'evaluate_d' : fields.String(required=True, description='The evaluate description', example='상위목표와 세부목표의 연관성'),
    #'context' : fields.String(required=True, description='The context', example='당신은 상위목표와 세부목표의 연관성 평가 전문가입니다. 상위목표, 세부목표, 업종, 팀명을 기반으로 상위목표와 세부목표의 연관성을 1에서 5점 중 하나로 평가하고 출력하세요. 평가를 준 이유에 대해서도 출력하세요.'),
})

evaluate_o = ["상위 목표와 목표의 연관성", "고객 가치", "목표 지향"]
evaluate_k = ["상위표와 세부목표의 연관성", "측정 가능성", "결과 지향성"]

@EV.route('')
class EVResource(Resource):
    @EV.expect(EV_fields)
    def post(self):
        request_data = request.json
        modeloutput = dict()
        if request_data["isObjective"] == True:
            for i in range(3):
                modeloutput[evaluate_o[i]] = eval_generate.delay(request_data, i)      
            
        else:
            for i in range(3):
                modeloutput[evaluate_k[i]] = eval_generate.delay(request_data, i)            
        

        outputs_id = {key: value.id for key, value in modeloutput.items()}
        return outputs_id

        
