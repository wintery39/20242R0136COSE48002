from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
import time
from sqlalchemy.ext.asyncio import AsyncSession
from crud import create_eval_okr, findById, update_revision_okr
from asyncio import get_event_loop
from ai.kr import krEV, krRV
from ai.obj import objEV, objRV

celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(name="execute_ai")
def execute_ai_okr(okr_info):
    async def process_loop():
        objective_types = ["align", "value"]
        keyresult_types = ["connectivity", "measurability", "directivity"]
        
        result=dict()
            
        if okr_info["is_objective"] == True:
            for idx, eval_type in enumerate(objective_types):
                result = objEV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", False, False, idx)
                if result["score"] is not None and result["description"] is not None:
                    await create_eval_okr(okr_info["okr_id"], eval_type, result["score"], result["description"])
            
            result = objRV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", result["description"], False, False)
        else:
            for idx, eval_type in enumerate(keyresult_types):
                result = krEV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", False, False, idx)
                print(result["score"])
                print(result["description"])
                if result["score"] is not None and result["description"] is not None:
                    await create_eval_okr(okr_info["okr_id"], eval_type, result["score"], result["description"])
            
            result = krRV(okr_info["input_sentence"], okr_info["upper_objective"], "", "", result["description"], False, False)
        
        if result["revision"] is not None and result["description"] is not None:
            await update_revision_okr(okr_info["okr_id"], result["revision"], result["description"])


    loop = get_event_loop()
    loop.run_until_complete(process_loop())
    return True
