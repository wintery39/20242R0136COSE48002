from fastapi import FastAPI, Depends, Request, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult
from tasks import celery_app, execute_ai_okr
from crud import get_okr_join_company, get_ai_okr_result, findById, upload_dataframe, get_okr_join_company_prediction, get_companys
from database import get_db
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np
from io import BytesIO

app = FastAPI()

class Ai(BaseModel):
    okr_ids: List[int]


@app.get("/{page}")
async def getokr(page: int, db: AsyncSession = Depends(get_db), company_name:str | None = None, new_sorting: bool = True, page_size: int = 10):
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    offset = (page-1)*page_size
    response = await get_okr_join_company(db, offset, page_size, company_name, new_sorting)
    return response

@app.get("/prediction/{page}")
async def getokr_with_prediciton(page: int, db: AsyncSession = Depends(get_db), company_name:str | None = None, new_sorting: bool = True, page_size: int = 10):
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    offset = (page-1)*page_size
    response = await get_okr_join_company_prediction(db, offset, page_size, company_name, new_sorting)
    return response

@app.get("/company/{page}")
async def getcompany(page: int, db: AsyncSession = Depends(get_db), company_name: str | None = None, page_size: int = 10):
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    offset = (page-1)*page_size
    response = await get_companys(db, offset, company_name, page_size)
    return response

@app.get("/ai/{id}")
async def get_ai_okr(id: int, db: AsyncSession = Depends(get_db)):
    response = await get_ai_okr_result(db, id)
    if response is None:
        return "Error"
    return response

@app.post("/ai/")
async def post_ai_eval(data: Ai, db: AsyncSession = Depends(get_db)):
    output = []
    for okr_id in data.okr_ids:
        info = await findById(db, okr_id)
        temp_dict = dict()
        if info == None:
            temp_dict["output_id"] = "Error"
        else:
            temp_dict["output_id"] = execute_ai_okr.delay(info).id
        

        temp_dict['okr_id'] = okr_id
        output.append(temp_dict)
    
    return output

@app.post("/upload/")
async def upload_excel(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # 파일 확장자 확인
    if file.filename.endswith(('.xlsx')):
        # 파일을 메모리에 로드
        contents = await file.read()
        # BytesIO 객체를 사용하여 Pandas로 읽기
        df = pd.read_excel(BytesIO(contents))
        expected_keys = {"type", "input_sentence", "upper_objective", "company", "field", "team", "company_description", "homepage_url", "urls"}
        
        actual_keys = set(df.columns)

        if actual_keys == expected_keys:
            df = df.replace({np.nan: None})
            _ = await upload_dataframe(db, df)
        else:
            return {"error": "Invalid file format. Please check keys."}
        
        
        return {"message":"success"}
        
    else:
        return {"error": "Invalid file format. Please upload an Excel file."}


@app.get("/tasks/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)