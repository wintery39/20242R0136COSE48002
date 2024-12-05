from fastapi import FastAPI, Depends, Request, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult
from tasks import celery_app, execute_ai_okr, execute_rag_company
from crud import get_okr_join_company, get_ai_okr_result, findById, findCompanyById, upload_dataframe, get_okr_join_company_prediction, get_companys
from database import get_db
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np
from io import BytesIO
from logger_config import logger
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000"
]

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True, # 쿠키를 허용할지 여부
    allow_methods=["*"],    # 허용할 HTTP 메서드 (GET, POST 등)
    allow_headers=["*"],    # 허용할 HTTP 헤더
)

class Ai(BaseModel):
    okr_ids: List[int]

class Rag(BaseModel):
    company_ids: List[int]


@app.get("/{page}")
async def getokr(page: int, db: AsyncSession = Depends(get_db), company_name:str | None = None, company_field:str | None = None, new_sorting: bool = True, page_size: int = 10):
    logger.info(f"getokr 호출됨: page={page}, company_name={company_name}, company_field={company_field}, new_sorting={new_sorting}, page_size={page_size}")
    
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    offset = (page-1)*page_size
    response = await get_okr_join_company(db, offset, page_size, company_name, company_field, new_sorting)
    logger.info(f"getokr 반환값: {response}")
    return response

@app.get("/prediction/{page}")
async def getokr_with_prediciton(page: int, db: AsyncSession = Depends(get_db), company_name:str | None = None, company_field:str | None = None, new_sorting: bool = True, page_size: int = 10):
    logger.info(f"getokr_with_prediciton 호출됨: page={page}, company_name={company_name}, company_field={company_field}, new_sorting={new_sorting}, page_size={page_size}")
    if page < 1:
        logger.warning("page 값이 1보다 작습니다. 1로 설정합니다.")
        page = 1
    if page_size < 1:
        logger.warning("page_size 값이 1보다 작습니다. 기본값 10으로 설정합니다.")
        page_size = 10

    offset = (page-1)*page_size
    response = await get_okr_join_company_prediction(db, offset, page_size, company_name, company_field, new_sorting)
    logger.info(f"getokr_with_prediciton 반환값: {response}")
    return response

@app.get("/company/{page}")
async def getcompany(page: int, db: AsyncSession = Depends(get_db), company_name: str | None = None, page_size: int = 10):
    logger.info(f"getcompany 호출됨: page={page}, company_name={company_name}, page_size={page_size}")

    if page < 1:
        logger.warning("page 값이 1보다 작습니다. 1로 설정합니다.")
        page = 1
    if page_size < 1:
        logger.warning("page_size 값이 1보다 작습니다. 기본값 10으로 설정합니다.")
        page_size = 10

    offset = (page-1)*page_size
    response = await get_companys(db, offset, company_name, page_size)
    logger.info(f"getcompany 반환값: {response}")
    return response

@app.get("/ai/{id}")
async def get_ai_okr(id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"get_ai_okr 호출됨: id={id}")
    response = await get_ai_okr_result(db, id)
    
    if response is None:
        logger.error(f"get_ai_okr 실패: okr_id={id}에 대한 데이터를 찾을 수 없음.")
        return "Error"
    
    logger.info(f"get_ai_okr 반환값: {response}")
    return response

@app.post("/ai/")
async def post_ai_eval(data: Ai, db: AsyncSession = Depends(get_db)):
    logger.info(f"post_ai_eval 호출됨: okr_ids={data.okr_ids}")
    
    output = []
    for okr_id in data.okr_ids:
        info = await findById(db, okr_id)
        temp_dict = dict()
        if info == None:
            logger.warning(f"findById 실패: okr_id={okr_id}")
            temp_dict["output_id"] = "Error"
        else:
            temp_dict["output_id"] = execute_ai_okr.delay(info).id
            logger.info(f"AI 작업 시작: task_id={temp_dict['output_id']}, okr_id={okr_id}")
        

        temp_dict['okr_id'] = okr_id
        output.append(temp_dict)
    
    logger.info(f"post_ai_eval 반환값: {output}")
    return output

@app.post("/description/")
async def post_rag_company(data: Rag, db: AsyncSession = Depends(get_db)):
    logger.info(f"post_rag_company 호출됨: company_ids={data.company_ids}")
    
    output = []
    for company_id in data.company_ids:
        info = await findCompanyById(db, company_id)
        temp_dict = dict()
        if info is None:
            logger.warning(f"findCompanyById 실패: company_id={company_id}")
            temp_dict["output_id"] = "Error"
        elif info["company_filename"] is None:
            logger.warning(f"company_filename이 존재하지 않음: company_id={company_id}")
            temp_dict["output_id"] = "Error: company_filename이 없음."
        else:
            temp_dict["output_id"] = execute_rag_company.delay(info).id
            logger.info(f"RAG 작업 시작: task_id={temp_dict['output_id']}, company_id={company_id}")
        

        temp_dict['company_id'] = company_id
        output.append(temp_dict)
    
    logger.info(f"post_rag_company 반환값: {output}")
    return output

@app.post("/upload/")
async def upload_excel(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    logger.info(f"upload_excel 호출됨: filename={file.filename}")

    # 파일 확장자 확인
    if file.filename.endswith(('.xlsx')):
        # 파일을 메모리에 로드
        contents = await file.read()
        # BytesIO 객체를 사용하여 Pandas로 읽기
        df = pd.read_excel(BytesIO(contents))
        expected_keys = {"type", "input_sentence", "upper_objective", "company", "field", "team", "company_description", "filename"}
        
        actual_keys = set(df.columns)

        if actual_keys == expected_keys:
            df = df.replace({np.nan: None})
            logger.info(f"데이터프레임 업로드 시작")
            _ = await upload_dataframe(db, df)
        else:
            logger.error(f"파일 포맷 오류: actual_keys={actual_keys}, expected_keys={expected_keys}")
            return {"error": "Invalid file format. Please check keys."}
        
        logger.info("엑셀 업로드 성공")
        return {"message":"success"}
        
    else:
        logger.error("파일 확장자 오류: .xlsx 파일이 아님")
        return {"error": "Invalid file format. Please upload an Excel file."}


@app.get("/tasks/{task_id}")
def get_status(task_id: str):
    logger.info(f"get_status 호출됨: task_id={task_id}")

    task_result = AsyncResult(task_id, app=celery_app)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    logger.info(f"작업 상태 반환: {result}")
    return JSONResponse(result)