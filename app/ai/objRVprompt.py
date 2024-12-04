from langchain.prompts import PromptTemplate

obj_background_template = """
company: {company}
field: {field}
team: {team}
"""

objRV_task_description = """
당신은 obj(Objectives and Key Results) 평가 전문가입니다. 주어진 Objective 문장을 다음 기준에 따른 분석을 통해 개선하세요.

al 측정가능성, 그리고 결과 지향성을 모두 개선하여 완성된 하나의 문장을 제시하세요.
연관성 개선. 상위 목표와의 연결고리 강화, 직접적인 기여도 명확화, 핵심 가치 반영
측정 가능성 개선. 구체적인 수치 목표 설정, 명확한 측정 지표 추가, 시간 제약 명시
결과 지향성 개선. 활동 중심 문구를 결과 중심으로 변환, 최종 영향이나 가치를 명확히 표현, 달성 기준 구체화

위의 단계별 사고 과정을 거친 후, 종합적으로 판단하여 다음 두 가지 결과를 제시하세요

  1. "description": "구체적인 수정 이유 (위의 사고 과정을 반영하여 작성)",
  2. "revision": 최종 수정 문장

{prefix_guideline}
{prefix_example}
"""

# "guideline" : "우리맛 연구팀의 레시피 개발을 통해 고객이 요리에 대한 접근성을 얼마나 높였는가? 우리맛 연구팀의 콘텐츠를 통해 고객의 요리에 대한 흥미와 참여를 얼마나 높였는가? 우리맛 연구팀의 노력을 통해 고객이 하루에 한 끼는 요리를 하고 싶게 만드는 데 얼마나 성공했는가?",

objRV_examples = [
    {
        "guideline": "추가 필요",
        "input_sentence": "일상 요리들의 조리 과정을 50% 줄일 수 있는 제품+요리법을 연구, 개발한다.",
        "upper_objective": "고객이 하루에 한 끼는 요리를 하고 싶게 한다.",
        "EV_description": "조리를 쉽고 빠르게 할 수 있는 것은 고객이 하루에 한끼 정도는 요리를 할 수 있게 만드는 요소입니다. 현재대비 50% 정도로 요리 과정이 간소화되어야 하는데, 현재가 어느정도인지 나타나지 않아서 50%로 줄어드는 것을 측정하기 어렵다. 조리과정 50% 감소라는 것은 결과이나, 조리과정이 현재 어느정도에서 얼마나 달라지는지로 표현되어야 더 좋은 결과다",
        "revision": "일상 요리 조리 평균 시간을 50분에서 25분으로 줄인다.",
        "description": "구체적인 판단의 근거를 제시함",
    }
]

objRV_example_prompt = PromptTemplate(
    input_variables=[
        "guideline",
        "input_sentence",
        "upper_objective",
        "EV_description",
        "description",
        "revision",
    ],
    template="""
  <예시 입력>
  "guideline" : {guideline}
  "input_sentence": {input_sentence}
  "upper_objective": {upper_objective}
  "EV_description": {EV_description}
  
  <예시 출력>
  
  "revision" : {revision}
  "description" : {description}
  
  """,
)

objRV_suffix = """
<실제 입력>
"guideline": {guideline}
"input_sentence": {input_sentence}
"upper_objective": {upper_objective}
"EV_description": {EV_description}

<실제 출력>

"description":
"revision":


출력 형식은 key가 description과 revision 2개인 json 형식입니다. json이라는 문구나 백틱 같은 특수문자는 사용하지 마십시오.
"""

objRV_examples_1 = [
    {
        "guideline": "추가 필요",
        "input_sentence": "일상 요리들의 조리 과정을 50% 줄일 수 있는 제품+요리법을 연구, 개발한다.",
        "upper_objective": "고객이 하루에 한 끼는 요리를 하고 싶게 한다.",
        "EV_description": "조리를 쉽고 빠르게 할 수 있는 것은 고객이 하루에 한끼 정도는 요리를 할 수 있게 만드는 요소입니다.",
        "description": "추가 필요",
        "revision": "추가 필요",
    }
]

objRV_examples_2 = [
    {
        "guideline": "추가 필요",
        "input_sentence": "일상 요리들의 조리 과정을 50% 줄일 수 있는 제품+요리법을 연구, 개발한다.",
        "upper_objective": "고객이 하루에 한 끼는 요리를 하고 싶게 한다.",
        "EV_description": "조리를 쉽고 빠르게 할 수 있는 것은 고객이 하루에 한끼 정도는 요리를 할 수 있게 만드는 요소입니다.",
        "description": "추가 필요",
        "revision": "추가 필요",
    }
]

objRV_examples_3 = [
    {
        "guideline": "추가 필요",
        "input_sentence": "일상 요리들의 조리 과정을 50% 줄일 수 있는 제품+요리법을 연구, 개발한다.",
        "upper_objective": "고객이 하루에 한 끼는 요리를 하고 싶게 한다.",
        "EV_description": "조리를 쉽고 빠르게 할 수 있는 것은 고객이 하루에 한끼 정도는 요리를 할 수 있게 만드는 요소입니다.",
        "description": "추가 필요",
        "revision": "추가 필요",
    }
]