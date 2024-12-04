import time
from ai.parse import EV_parse_data, EV_error
from ai.llm_select import llm


# input: score 3개, des 3개
# output: 과반수 score, 병합된 des
def whowins(
    des1,
    des2,
    des3,
    score1,
    score2,
    score3,
):
    # 입력값 리스트
    dess = [des1, des2, des3]
    scores = [score1, score2, score3]

    # None이 아닌 값 필터링
    valid_data = [
        (score, des)
        for score, des in zip(scores, dess)
        if score is not None and des is not None
    ]
    valid_count = len(valid_data)

    # None 처리에 따른 분기
    if valid_count == 3:
        # None이 없을 때 기존 로직
        scores, dess = zip(*valid_data)
        unique_scores = set(scores)
        score_des_dict = {}
        for score, des in zip(scores, dess):
            if score in score_des_dict:
                score_des_dict[score].append(des)
            else:
                score_des_dict[score] = [des]

        if len(unique_scores) == 1:
            win_score = scores[0]
            win_des = llm.invoke(
                "세 문장을 조합해서 재구성해줘: " + ", ".join(score_des_dict[win_score])
            ).content
        elif len(unique_scores) == 2:
            for score in unique_scores:
                if scores.count(score) == 2:
                    win_score = score
                    win_des = llm.invoke(
                        "두 문장을 조합해서 재구성해줘: "
                        + ", ".join(score_des_dict[win_score])
                    ).content
                    break
        else:
            win_score = sorted(scores)[1]
            win_des = score_des_dict[win_score][0]

    elif valid_count == 2:
        # None이 1개일 때 점수 평균 계산
        scores, dess = zip(*valid_data)
        win_score = sum(scores) // 2  # 평균 (정수로 계산)
        win_des = llm.invoke(
            "두 문장을 조합해서 재구성해줘: " + ", ".join(dess)
        ).content

    elif valid_count == 1:
        # None이 2개일 때 나머지 값 반환
        win_score, win_des = valid_data[0]

    else:
        # None이 3개일 때 기본 오류 값 반환
        return EV_error

    # JSON 포맷 생성
    raw_string = f"""
        {{
            "description": "{win_des}",
            "score": {win_score}
        }}
        """

    res = EV_parse_data(raw_string)
    return res