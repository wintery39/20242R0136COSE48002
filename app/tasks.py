from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
import time
from sqlalchemy.ext.asyncio import AsyncSession
from crud import create_eval_okr, findById, update_revision_okr, update_guideline_okr, update_description_company, update_guideline_okr
from asyncio import get_event_loop
from ai.kr import krEV_selfC, krRV
from ai.obj import objEV, objRV
from logger_config import logger
from guideline_output_fixed import key_result_query, objective_query
from rag_finalized import rag

celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(name="execute_ai")
def execute_ai_okr(okr_info):
    async def process_loop():
        objective_types = ["align", "value"]
        keyresult_types = ["connectivity", "measurability", "directivity"]
        
        EV_description = ""
        result=dict()
        logger.info(f"OKR ID: {okr_info['okr_id']}에 대한 AI 작업 실행, Objective 여부: {okr_info['is_objective']}")
        try:
            if okr_info["is_objective"] == True:
                logger.info(f"Objective로 처리 중, 입력 문장: {okr_info['input_sentence']}")
                guideline = objective_query(okr_info['company_name'], okr_info['company_field'], okr_info['upper_objective'], okr_info["company_description"]) #company_name, department_name, objective, context
                
                if guideline["Guideline"] is not None:
                    await update_guideline_okr(okr_info['okr_id'], guideline["Guideline"])

                for idx, eval_type in enumerate(objective_types):
                    if guideline["Guideline"] is None:
                        result = objEV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", False, False, idx)
                    else:
                        result = objEV(okr_info["input_sentence"], okr_info["upper_objective"], guideline["Guideline"], "", True, False, idx)

                    logger.debug(f"Objective 평가 {eval_type}: {result}")
                    
                    if result["score"] is not None and result["description"] is not None:
                        EV_description += result["description"]
                        await create_eval_okr(okr_info["okr_id"], eval_type, result["score"], result["description"])
                        logger.info(f"{eval_type} 평가 저장, 점수: {result['score']}")
                    else:
                        await create_eval_okr(okr_info["okr_id"], eval_type, -1, "Error: 오류 발생.")
                        logger.info(f"{eval_type} 평가 오류 발생")
                
                if guideline is None:
                    result = objRV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", EV_description, False, False)
                else:
                    result = objRV(okr_info["input_sentence"], okr_info["upper_objective"], guideline, "", EV_description, True, False)
                logger.debug(f"Objective 수정 결과: {result}")
            else:
                logger.info(f"Key Result로 처리 중, 입력 문장: {okr_info['input_sentence']}")
                guideline = key_result_query(okr_info['company_name'], okr_info['company_field'], okr_info['upper_objective'], okr_info["company_description"]) #company_name, department_name, objective, context
                
                if guideline["Guideline"] is not None:
                    await update_guideline_okr(okr_info['okr_id'], guideline["Guideline"])
                
                for idx, eval_type in enumerate(keyresult_types):
                    if guideline["Guideline"] is None:
                        result = krEV_selfC(okr_info["input_sentence"], okr_info["upper_objective"], "", "", False, False, idx)
                    else:
                        result = krEV_selfC(okr_info["input_sentence"], okr_info["upper_objective"], guideline["Guideline"], "", True, False, idx)
                    logger.debug(f"Key Result 평가 {eval_type}: {result}")

                    if result["score"] is not None and result["description"] is not None:
                        EV_description += result["description"]
                        await create_eval_okr(okr_info["okr_id"], eval_type, result["score"], result["description"])
                        logger.info(f"{eval_type} 평가 저장, 점수: {result['score']}")
                    else:
                        await create_eval_okr(okr_info["okr_id"], eval_type, -1, "Error: 오류 발생.")
                        logger.info(f"{eval_type} 평가 오류 발생")
                
                if guideline is None:
                    result = krRV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", EV_description, False, False)
                else:
                    result = krRV(okr_info["input_sentence"], okr_info["upper_objective"], guideline, "", EV_description, True, False)

                logger.debug(f"Key Result 수정 결과: {result}")
            
            if result["revision"] is not None and result["description"] is not None:
                await update_revision_okr(okr_info["okr_id"], result["revision"], result["description"])
                logger.info(f"OKR ID: {okr_info['okr_id']}에 대한 수정 사항 업데이트, 수정: {result['revision']}")
            else:
                await update_revision_okr(okr_info["okr_id"], "Error: revision 생성 오류", "Error: revision 생성 오류")
                logger.warning(f"OKR ID: {okr_info['okr_id']}에 대해 revision 생성 안됨")
        except Exception as e:
            logger.error(f"OKR ID {okr_info['okr_id']}에 대한 AI 실행 중 오류 발생: {e}")

    loop = get_event_loop()
    logger.info("AI 작업을 위한 이벤트 루프 시작.")
    loop.run_until_complete(process_loop())
    logger.info(f"OKR ID {okr_info['okr_id']}에 대한 AI 실행 완료.")
    return True



@celery_app.task(name="execute_rag")
def execute_rag_company(company_info):
    
    result = rag(company_info["company_name"], company_info["company_field"], "eqs-rag", company_info["company_filename"]) #company_name, company_type, bucket_name, doc_name
    
    if result["description"] is None:
        logger.error(f"company_id : {company_info['company_id']} 평가 오류 발생")
        return False

    logger.info(f"company_id : {company_info['company_id']} description 생성 {result['description']}")
    loop = get_event_loop()
    loop.run_until_complete(update_description_company(company_info["company_id"], result["description"]))
    logger.info(f"company_id : {company_info['company_id']}에 대한 description 저장 완료")
    return True

