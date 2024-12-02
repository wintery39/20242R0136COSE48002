from langchain.prompts import PromptTemplate

objEV_task_description = """
당신은 세계적으로 인정받는 OKR(Objectives and Key Results) 전문 컨설턴트입니다. 당신의 임무는 주어진 Objective를 철저히 분석하고 평가하여, 조직의 목표 달성을 위한 최적의 OKR 수립을 돕는 것입니다.

평가 대상
input_sentence: {input_sentence}
upper_objective: {upper_objective}
company: {company}
field: {field}
team: {team}

각 기준에 대해 다음 정보를 제공하세요.
- description: 점수에 대한 구체적인 근거를 설명합니다.
- score: 1-5점 (1: 매우 낮음, 5: 매우 높음)

평가 지침.
1. 주어진 회사, 업종, 가이드라인, 팀 정보를 고려하여 맥락에 맞는 평가를 제공하세요.
2. 객관적이고 전문적인 관점에서 평가하되, 확신에 찬 톤으로 의견을 제시하세요.
3. 각 평가 요소를 개별적으로 분석하세요.
4. 산업 특성을 고려하여 평가에 반영하세요.
"""

obj_background_template = """
company: {company}
field: {field}
team: {team}
"""

objEV_suffix = """
<입력>
"guideline": {guideline}
"input_sentence": {input_sentence}
"upper_objective": {upper_objective}
"description":
"score":

출력 형식은 key가 description와 score 2개인 json형식입니다. json이라는 문구나 백틱 같은 특수문자는 사용하지 마십시오.
"""

# 예시 형식 지정, input_variables에 해당하는 변수만 바뀔거고 { } 자리에 들어간다는 의미.
objEV_example_prompt = PromptTemplate(
    input_variables=[
        "guideline",
        "input_sentence",
        "upper_objective",
        "description",
        "score",
    ],
    template="""
  "guideline": {guideline}
  "input_sentence": {input_sentence}
  "upper_objective": {upper_objective}
  "description": {description}
  "score": {score}
  """,
)

# 평가요소의 의미 설명
objEV_align_description = """
당신은 OKR(Objectives and Key Results) 평가 전문가입니다. 주어진 Objective(input_sentence)가 Upper_Objective와 얼마나 align되어 있는지 평가해야 합니다. 다음 평가 기준에 따라 단계적으로 사고하세요.

1. 점수별 기준 검토
   1점 기준 =
   - Objective가 Upper_Objective와 완전히 무관한가요?
   2점 기준 =
   - Objective가 Upper Objective의 Align이 아예 무관하다고 보기 어렵지만, Align의 정도를 판단하기 위해서 여러 가정들을 거쳐야 하나요?
   3점 기준 =
   - Objective가 Upper Objective와 전략적으로는 연결되어 있지만, 초점이 다소 불분명한가요?
   4점 기준 =
   - Objective가 Upper Objective와 명확한 연관성이 있으나, 일부 개선이 필요한가요?
   5점 기준 =
   - Objective가 Upper Objective와의 전체 혹은 일부와 전략적 연결이 매우 뚜렷한가요? 또는 최상위 조직의 경우, 미션/비전/전략 방향이 균형있게 반영되어있나요?

2. 산업 및 조직 특성 고려
   - 주어진 회사, 업종, 팀 정보를 고려할 때, 이 objective의 Upper objective와의 연관성은 어떻게 평가되나요?

3. 종합 평가
   위의 분석을 바탕으로, 1-5점 척도에서 어떤 점수가 가장 적절한가요? 그 이유는 무엇인가요?

위의 단계별 사고 과정을 거친 후, 종합적으로 평가하여 다음 두 가지 결과를 제시하세요.

1. description: 평가 기준에 따른 구체적인 평가 (위의 사고 과정을 반영하여 작성)
2. score: 최종 평가 점수 (1-5점)

주의사항.
- 평가는 객관적이고 전문적이어야 하며, 주어진 회사, 업종, 팀 정보를 고려하여 맥락에 맞는 평가를 제공하세요.
- 확신에 찬 톤으로 답변하되, 합리적이고 구체적인 근거를 제시하세요.
- 산업과 조직의 특성을 고려하여 평가에 반영하세요.

{prefix_guideline}
{prefix_example}

이제 주어진 input_sentence에 대해 위의 단계를 따라 사고하고, 요청된 형식으로 결과를 제시하세요.
"""

# fewshot
objEV_align_examples = [
    {
        "guideline": "해당 고객층 확보는 어떻게 공비서 프로그램의 초기 전략인 '모든 매출은 고객에게서 나온다'에 기여할까요? (예: 고객층을 네일샵 초보 창업자로 설정하면, 이들은 공비서 프로그램을 통해 매장 운영 노하우를 배우고 비즈니스 성장을 도모하며 매출 증대를 이끌어 낼 수 있습니다.), 해당 마케팅 전략은 어떻게 공비서 프로그램의 초기 전략인 '고객 확대'에 기여하며, 고객 만족으로 이어질 수 있을까요? (예: 네일샵 관련 커뮤니티 및 SNS 채널을 활용한 마케팅 전략은 타겟 고객에게 효과적으로 공비서 프로그램을 알릴 수 있으며, 프로그램 사용 후기를 공유하여 신뢰도를 높이고 고객 만족으로 이어질 수 있습니다.), 차별화된 기능 또는 서비스는 어떻게 고객 확대 목표에 기여하고, 공비서 프로그램의 경쟁력을 강화할 수 있을까요? (예: 고객 관리 시스템과 연동된 마케팅 자동화 기능은 원장님들의 마케팅 효율성을 높여주고, 고객 만족도를 향상시켜 고객 유지율을 높이고 새로운 고객 확보에도 기여할 수 있습니다.)",
        "input_sentence": "신규 고객 유치 (매출 300% 달성 목표)",
        "upper_objective": "공비서 초기 전략은 모든 매출은 고객에게서 나온다 임. 그래서, 고객만족을 위한 사용성 개선과 더불어 고객의 확장 전략에 집중. 이 OKR은 고객 확대에 집중하는 것임",
        "description": "고객확대 전략에 얼라인한 신규고객유치에 집중하는 것을 최우선순위로 잡는다",
        "score": "4.5",
    }
]

# 평가요소의 의미 설명
objEV_value_description = """
당신은 OKR(Objectives and Key Results) 평가 전문가입니다. 주어진 Objective(input_sentence)가 얼마나 고객에게 제공하는 가치를 언급하고 있는지 평가해야 합니다. 다음 평가 기준에 따라 단계적으로 사고하세요.

1. 점수별 기준 검토
   1점 기준 =
   - Objective가 고객 가치와 완전히 무관한가요?
   2점 기준 =
   - Objective에 고객에 관한 문제나 상황은 있지만, 제공하고자 하는 가치가 나타나지 않나요?
   3점 기준 =
   - Objective에서 고객에게 제공하고자 하는 가치는 분명하지만, 전략적으로 고객의 필요와의 일치 여부가 다소 모호한가요?
   4점 기준 =
   - Objective에서 고객에게 제공하고자 하는 가치가 현재 고객의 필요와 대체로 일치하지만, 일부 측면에서 명확성이나 구체성이 부족한가요?
   5점 기준 =
   - Objective의 고객에게 제공하고자 하는 가치 혹은 고객이 겪는 문제에 대한 해결이 현재 고객에게 필요한 것과 일치하고, 이를 명확하게 표현하고 있나요?
2. 산업 및 조직 특성 고려
   - 주어진 회사, 업종, 팀 정보를 고려할 때, 이 objective의 고객 가치 지향성은 어떻게 평가되나요?
3. 종합 평가
   위의 분석을 바탕으로, 1-5점 척도에서 어떤 점수가 가장 적절한가요? 그 이유는 무엇인가요?

위의 단계별 사고 과정을 거친 후, 종합적으로 평가하여 다음 두 가지 결과를 제시하세요.

1. description: 평가 기준에 따른 구체적인 평가 (위의 사고 과정을 반영하여 작성)
2. score: 최종 평가 점수 (1-5점)

주의사항.
- 평가는 객관적이고 전문적이어야 하며, 주어진 회사, 업종, 팀 정보를 고려하여 맥락에 맞는 평가를 제공하세요.
- 확신에 찬 톤으로 답변하되, 합리적이고 구체적인 근거를 제시하세요.
- 산업과 조직의 특성을 고려하여 평가에 반영하세요.

{prefix_guideline}
{prefix_example}

이제 주어진 input_sentence에 대해 위의 단계를 따라 사고하고, 요청된 형식으로 결과를 제시하세요.
"""

# fewshot
objEV_value_examples = [
    {
        "guideline": "이 기능적인 개선은 원장님과 손님의 어떤 불편함을 해결하여 어떤 가치를 제공할 수 있을까요? (예: 예약 시스템 개선은 원장님들의 예약 관리 부담을 줄이고, 손님들은 원하는 시간에 쉽게 예약을 할 수 있어 편리성을 높일 수 있습니다.), 이 기술적인 개선은 원장님과 손님의 어떤 불안감을 해소하여 어떤 가치를 제공할 수 있을까요? (예: 데이터 백업 시스템 구축은 프로그램 오류 발생 시 데이터 손실에 대한 원장님들의 불안감을 해소하고, 손님들의 정보 유출에 대한 우려를 줄여 안전한 서비스 이용 환경을 제공합니다.), 이 새로운 기능은 원장님과 손님에게 어떤 새로운 가치를 제공할 수 있을까요? (예: 고객 관리 기능 추가는 원장님들이 고객과의 소통을 강화하고, 손님들에게 맞춤형 서비스를 제공할 수 있도록 지원하여 만족도를 높일 수 있습니다.)",
        "input_sentence": "서비스 품질 및 사용성 제고 (서비스 편의성, 직관성, 안정성 개선)",
        "upper_objective": "공비서는 뷰티서비스를 제공하는 원장님과 샵을 이용하는 손님의 불편을 IT 기술로 해결하여, 원장님들의 비즈니스 성장을 촉진한다. 이를 위해서 IT기술을 발전시켜 서비스 사용성을 높여간다.",
        "description": "고객에게 제공하고자 하는 가치인 편의성/직관성/안정성은 분명하지만, 구체적인 고객 니즈가 모호하다",
        "score": "3",
    }
]

objEV_align_examples_1 = [
    {
        "guideline": "추가 필요!!",
        "input_sentence": "APP 다운로드 5만 달성 (500% 성장)",
        "upper_objective": "신규 고객 유치 (매출 300% 달성 목표)",
        "description": "신규 고객 확대를 통해, 매장 이용 소비자까지 app다운로드와가 늘어남",
        "score": "4.5",
    },
    {
        "guideline": "추가 필요!!",
        "input_sentence": "내부 시스템 및 인프라 재정비(DB 안정화, APP 경량화, 서비스 확장성을 위한 Back Office 정비)",
        "upper_objective": "서비스 품질 및 사용성 제고(서비스 편의성, 직관성, 안정성 개선)",
        "description": "DB 안정화, APP 경량화, 백오피스 구축하면, 어떤 품질/사용성과 연관 되는지 불명확",
        "score": "3",
    },
]

objEV_align_examples_2 = [
    {
        "guideline": "추가 필요!!",
        "input_sentence": "APP 다운로드 5만 달성 (500% 성장)",
        "upper_objective": "신규 고객 유치 (매출 300% 달성 목표)",
        "description": "신규 고객 확대를 통해, 매장 이용 소비자까지 app다운로드와가 늘어남",
        "score": "4.5",
    }
]

objEV_align_examples_3 = [
    {
        "guideline": "추가 필요!!",
        "input_sentence": "APP 다운로드 5만 달성 (500% 성장)",
        "upper_objective": "신규 고객 유치 (매출 300% 달성 목표)",
        "description": "신규 고객 확대를 통해, 매장 이용 소비자까지 app다운로드와가 늘어남",
        "score": "4.5",
    }
]

objEV_value_examples_1 = [
    {
        "guideline": "추가 필요!!",
        "input_sentence": "APP 다운로드 5만 달성 (500% 성장)",
        "upper_objective": "신규 고객 유치 (매출 300% 달성 목표)",
        "description": "신규 고객 확대를 통해, 매장 이용 소비자까지 app다운로드와가 늘어남",
        "score": "4.5",
    },
    {
        "guideline": "추가 필요!!",
        "input_sentence": "내부 시스템 및 인프라 재정비(DB 안정화, APP 경량화, 서비스 확장성을 위한 Back Office 정비)",
        "upper_objective": "서비스 품질 및 사용성 제고(서비스 편의성, 직관성, 안정성 개선)",
        "description": "DB 안정화, APP 경량화, 백오피스 구축하면, 어떤 품질/사용성과 연관 되는지 불명확",
        "score": "3",
    },
]

objEV_value_examples_2 = [
    {
        "guideline": "추가 필요!!",
        "input_sentence": "APP 다운로드 5만 달성 (500% 성장)",
        "upper_objective": "신규 고객 유치 (매출 300% 달성 목표)",
        "description": "신규 고객 확대를 통해, 매장 이용 소비자까지 app다운로드와가 늘어남",
        "score": "4.5",
    }
]

objEV_value_examples_3 = [
    {
        "guideline": "추가 필요!!",
        "input_sentence": "APP 다운로드 5만 달성 (500% 성장)",
        "upper_objective": "신규 고객 유치 (매출 300% 달성 목표)",
        "description": "신규 고객 확대를 통해, 매장 이용 소비자까지 app다운로드와가 늘어남",
        "score": "4.5",
    }
]
