from models import Company, Okr, Prediction
from sqlalchemy import select, func, update, insert as sq_insert, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from database import get_db
from fastapi import Depends
from sqlalchemy.orm import joinedload, contains_eager
from logger_config import logger


async def findById(db: AsyncSession, id: int):
    logger.info(f"findById 호출: id={id}")
    query = select(Okr, Company).join(Company, (Company.id == Okr.company_id), isouter=True).where(id == Okr.id)
    
    result = await db.execute(query)
    try:
        okr, company = result.unique().all()[0]
    
        if okr is None:
            logger.warning(f"findById: okr_id={id}가 존재하지 않습니다.")
            return None

        data = {
            "okr_id": okr.id,
            "is_objective": okr.is_objective,
            "input_sentence": okr.input_sentence,
            "upper_objective": okr.upper_objective,
            "company_name": company.name,
            "company_field": company.field,
            "company_description": company.description,
            "guideline": okr.guideline,
            "revision": okr.revision,
            "revision_description": okr.revision_description,
            "created_at": okr.created_at
        }

        logger.info(f"findById 결과: OKR ID={okr.id}\n data={data}")
        return data
    except Exception as e:
        logger.error(f"findById 에러: {e}")
        return None

async def findCompanyById(db: AsyncSession, id: int):
    logger.info(f"findCompanyById 호출: id={id}")
    query = select(Company).filter(id == Company.id)
    
    result = await db.execute(query)
    try:
        company = result.scalars().first()
    
        if company is None:
            logger.warning(f"findCompanyById: okr_id={id}가 존재하지 않습니다.")
            return None

        data = {
            "company_id": company.id,
            "company_name": company.name,
            "company_field": company.field,
            "company_filename": company.filename
        }

        logger.info(f"findCompanyById 결과: OKR ID={company.id}\n data={data}")
        return data
    except Exception as e:
        logger.error(f"findCompanyById 에러: {e}")
        return None

async def upload_dataframe(db: AsyncSession, df):
    logger.info(f"upload_dataframe 호출, DataFrame 크기: {df.shape}")

    for index, row in df.iterrows():
        try:
            query = select(Company).where(
                Company.name == row['company'],
            )
            result = await db.execute(query)
            company = result.scalar_one_or_none()

            if not company:
                # 회사가 없으면 새로 삽입
                stmt = insert(Company).values(
                    name=row['company'],
                    field=row['field'],
                    description=row.get('company_description'),
                    filename=row.get("filename")
                ).returning(Company.id)
                result = await db.execute(stmt)
                company_id = result.scalar_one()
                logger.info(f"새로운 회사 추가: ID={company_id}")
            else:
                company_id = company.id


            okr_stmt = sq_insert(Okr).values(
                is_objective=(row["type"] == "Objective"),
                input_sentence=row['input_sentence'],
                upper_objective=row['upper_objective'],
                team=row['team'],
                company_id=company_id
            )
            await db.execute(okr_stmt)
        except Exception as e:
                logger.error(f"upload_dataframe 에러: {e}, index={index}")

    await db.commit()
    logger.info("upload_dataframe 완료")

async def get_companys(db: AsyncSession, offset, company_name, page_size):
    logger.info(f"get_companys 호출: offset={offset}, company_name={company_name}, page_size={page_size}")
    try:
        query = select(Company, func.count().over().label("total_count"))
        
        if company_name is not None:
            query = query.where(Company.name == company_name)

        
        result = await db.execute(query)
        rows = result.unique().all()

        total_page = 0    
        if rows:
            total_page = (rows[0].total_count+page_size-1) // page_size
        
        data = [
            {
                "company_id": company.id,
                "name": company.name,
                "field": company.field,
                "description": company.description
            }
            for company, _ in rows
        ]

        logger.info(f"get_companys 결과: 총 {len(data)}개 회사 반환")

        return {
            "data": data,
            "total_page": total_page
        }

    except Exception as e:
        logger.error(f"get_companys 에러: {e}")
        return None

async def get_okr_join_company_prediction(db: AsyncSession, offset, page_size, company_name = None, company_field = None, new_sorting = True):
    logger.info(f"get_okr_join_company_prediction 호출: offset={offset}, page_size={page_size}, company_name={company_name}, company_field={company_field}, new_sorting={new_sorting}")
    try:
        query = select(Okr, Company, func.count().over().label("total_count")).join(Company, (Company.id == Okr.company_id), isouter=True)
        
        if company_name is not None:
            query = query.where(Company.name == company_name)
            logger.info(f"필터 조건 추가: company_name={company_name}")
        if company_field is not None:
            query = query.where(Company.field == company_field)
            logger.info(f"필터 조건 추가: company_field={company_field}")
        query = query.options(joinedload(Okr.predictions))
        
        if new_sorting == True:
            query = query.order_by(Okr.created_at.desc()).offset(offset).limit(page_size)
        else:
            query = query.order_by(Okr.created_at.asc()).offset(offset).limit(page_size)

        query = query.where(
            or_(
                Okr.guideline != None,  # 또는 Okr.guideline.is_not(None)
                Okr.revision != None,
                Okr.predictions != None
            )
        )

        logger.debug(f"쿼리 생성 완료: {query}")
        result = await db.execute(query)
        rows = result.unique().all()
        logger.info(f"쿼리 실행 완료, 반환된 행 수: {len(rows)}")

        total_page = 0    
        if rows:
            total_page = (rows[0].total_count+page_size-1) // page_size
        
        data = [
            {
                "okr_id": okr.id,
                "is_objective": okr.is_objective, 
                "input_sentence": okr.input_sentence,
                "upper_objective": okr.upper_objective,
                "created_at": okr.created_at,
                "company_name": company.name,
                "company_field": company.field,
                "team": okr.team,
                "revision": okr.revision,
                "revision_description": okr.revision_description,
                "guideline": okr.guideline,
                "predictions": [
                    {
                        "prediction_id": pred.id,
                        "type": pred.type,
                        "score": pred.score,
                        "description": pred.description,
                    }
                    for pred in okr.predictions  # Okr.predictions 접근
                ]
            }
            for okr, company, _ in rows
        ]

        logger.info(f"데이터 처리 완료, total_page={total_page}")
        return {
            "data": data,
            "total_page": total_page
        }
    except Exception as e:
        logger.error(f"get_okr_join_company_prediction 에러: {e}")
        return None


async def get_okr_join_company(db: AsyncSession, offset, page_size, company_name = None, company_field = None, new_sorting = True):
    logger.info(f"get_okr_join_company 호출: offset={offset}, page_size={page_size}, company_name={company_name}, company_field={company_field}, new_sorting={new_sorting}")
    try:
        query = select(Okr, Company, func.count().over().label("total_count")).join(Company, (Company.id == Okr.company_id), isouter=True)
        
        if company_name is not None:
            query = query.where(Company.name == company_name)
            logger.info(f"필터 조건 추가: company_name={company_name}")
        if company_field is not None:
            query = query.where(Company.field == company_field)
            logger.info(f"필터 조건 추가: company_field={company_field}")

        if new_sorting == True:
            query = query.order_by(Okr.created_at.desc()).offset(offset).limit(page_size)
        else:
            query = query.order_by(Okr.created_at.asc()).offset(offset).limit(page_size)

        logger.debug(f"쿼리 생성 완료: {query}")
        result = await db.execute(query)
        rows = result.all()
        logger.info(f"쿼리 실행 완료, 반환된 행 수: {len(rows)}")

        total_page = 0    
        if rows:
            total_page = (rows[0].total_count+page_size-1) // page_size

        data = [
            {
                "okr_id": okr.id,
                "is_objective": okr.is_objective, 
                "input_sentence": okr.input_sentence,
                "upper_objective": okr.upper_objective,
                "created_at": okr.created_at,
                "company_name": company.name,
                "company_field": company.field,
                "team": okr.team
            }
            for okr, company, _ in rows
        ]

        logger.info(f"데이터 처리 완료, total_page={total_page}")
        return {
            "data": data,
            "total_page": total_page
        }
    except Exception as e:
        logger.error(f"get_okr_join_company 에러: {e}")
        return None


async def get_ai_okr_result(db: AsyncSession, okr_id):
    try:
        logger.info(f"get_ai_okr_result 호출: okr_id={okr_id}")

        query = select(Okr, Prediction).join(Prediction, (Prediction.okr_id == Okr.id), isouter=True).where(Okr.id == okr_id)
        logger.debug(f"쿼리 생성 완료: {query}")
        result = await db.execute(query)
        rows = result.all()
        logger.info(f"쿼리 실행 완료, 반환된 행 수: {len(rows)}")

        if rows is None:
            logger.warning(f"OKR ID={okr_id}에 대한 결과가 없습니다.")
            return None

        okr = rows[0][0]
        predict_result = []
        for _, prediction in rows:
            if prediction is None:
                predict_result.append({
                "prediction_score": None,
                "prediction_description": None,
                "prediction_type": None,
                "prediction_date": None
            })
            else:
                predict_result.append({
                    "prediction_score": prediction.score,
                    "prediction_description": prediction.description,
                    "prediction_type": prediction.type,
                    "prediction_date": prediction.updated_at.isoformat()
                })

        data = {
            "okr_id": okr.id,
            "input_sentence": okr.input_sentence,
            "upper_objective": okr.upper_objective,
            "guideline": okr.guideline,
            "revision": okr.revision,
            "revision_description": okr.revision_description,
            "predictions": predict_result,
            "team": okr.team
        }
        logger.info(f"OKR 결과 데이터 생성 완료: {data}")
        return data
    except Exception as e:
        logger.error(f"get_ai_okr_result 에러: {e}")
        return None



async def create_eval_okr(okr_id: int, type: str, score: int, description: str):
    logger.info(f"create_eval_okr 호출: okr_id={okr_id}, type={type}, score={score}, description={description}")
    try:
        async for db in get_db(): 
            stmt = insert(Prediction).values(
                okr_id=okr_id,
                score=score,
                description=description,
                type=type,
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=['okr_id', 'type'],  # `okr_id`와 `prediction_type` 컬럼이 유니크한 조건
                set_={
                    'score': score,
                    'description': description,
                }
            )
            async with db.begin():
                await db.execute(stmt)
            logger.info("Prediction 데이터 삽입 또는 업데이트 완료")
        return True
    except Exception as e:
        logger.error(f"create_eval_okr 에러: {e}")
        return False

async def update_revision_okr(okr_id: int, revision: str, description: str):
    logger.info(f"update_revision_okr 호출: okr_id={okr_id}, revision={revision}, description={description}")
    try:
        async for db in get_db():
            stmt = update(Okr).where(
                (Okr.id == okr_id)
            ).values(
                revision=revision,
                revision_description=description
            )

            async with db.begin():
                result = await db.execute(stmt)
            logger.info("OKR revision 데이터 업데이트 완료")
        return True
    except Exception as e:
        logger.error(f"update_revision_okr 에러: {e}")
        return False

async def update_guideline_okr(okr_id: int, guideline: str):
    logger.info(f"update_guideline_okr 호출: okr_id={okr_id}, guideline={guideline}")
    try:
        async for db in get_db():
            stmt = update(Okr).where(
                (Okr.id == okr_id)
            ).values(
                guideline=guideline
            )

            async with db.begin():
                result = await db.execute(stmt)
            logger.info("OKR guideline 데이터 업데이트 완료")
        return True
    except Exception as e:
        logger.error(f"update_guideline_okr 에러: {e}")
        return False

async def update_description_company(company_id: int, description: str):
    logger.info(f"update_description_company 호출: company_id={company_id}, description={description}")
    try:
        async for db in get_db():
            stmt = update(Company).where(
                (Company.id == company_id)
            ).values(
                description=description
            )

            async with db.begin():
                result = await db.execute(stmt)
            logger.info("Company description 데이터 업데이트 완료")
        return True
    except Exception as e:
        logger.error(f"update_description_company 에러: {e}")
        return False

