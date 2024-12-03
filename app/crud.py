from models import Company, Okr, Prediction, Document
from sqlalchemy import select, func, update, insert as sq_insert
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from database import get_db
from fastapi import Depends
from sqlalchemy.orm import joinedload, contains_eager

async def findById(db: AsyncSession, id: int):
    query = select(Okr).filter(id == Okr.id)
    
    result = await db.execute(query)
    try:
        okr = result.scalars().first()
    except:
        return None
    
    if okr is None:
        return None

    return {
        "okr_id": okr.id,
        "is_objective": okr.is_objective,
        "input_sentence": okr.input_sentence,
        "upper_objective": okr.upper_objective,
        "guideline": okr.guideline,
        "revision": okr.revision,
        "revision_description": okr.revision_description,
        "created_at": okr.created_at
    }

async def upload_dataframe(db: AsyncSession, df):
    print(df)
    for index, row in df.iterrows():
        query = select(Company).where(
            Company.name == row['company'],
            Company.field == row['field'],
        )
        result = await db.execute(query)
        company = result.scalar_one_or_none()

        if not company:
            # 회사가 없으면 새로 삽입
            stmt = insert(Company).values(
                name=row['company'],
                field=row['field'],
                description=row.get('company_description'),
                homepage_url=row.get('homepage_url')
            ).returning(Company.id)
            result = await db.execute(stmt)
            company_id = result.scalar_one()
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

        if row.get("filenames") is not None:
            try:
                temp_list = row.get("filenames").split(',,')
                for url in temp_list:
                    document = sq_insert(Document).values(
                        company_id=company_id,
                        url=url
                    )
                    await db.execute(document)
            except:
                pass

    await db.commit()

async def get_companys(db: AsyncSession, offset, company_name, page_size):
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
            "name": company.name,
            "field": company.field,
            "description": company.description
        }
        for company, _ in rows
    ]

    return {
        "data": data,
        "total_page": total_page
    }

async def get_okr_join_company_prediction(db: AsyncSession, offset, page_size, company_name = None, new_sorting = True):
    query = select(Okr, Company, func.count().over().label("total_count")).join(Company, (Company.id == Okr.company_id), isouter=True)
    
    if company_name is not None:
        query = query.where(Company.name == company_name).options(joinedload(Okr.predictions))
    else:
        query = query.options(joinedload(Okr.predictions))
    
    if new_sorting == True:
        query = query.order_by(Okr.created_at.desc()).offset(offset).limit(page_size)
    else:
        query = query.order_by(Okr.created_at.asc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.unique().all()

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

    return {
        "data": data,
        "total_page": total_page
    }


async def get_okr_join_company(db: AsyncSession, offset, page_size, company_name = None, new_sorting = True):
    query = select(Okr, Company, func.count().over().label("total_count")).join(Company, (Company.id == Okr.company_id), isouter=True)
    
    if company_name is not None:
        query = query.where(Company.name == company_name)
    
    if new_sorting == True:
        query = query.order_by(Okr.created_at.desc()).offset(offset).limit(page_size)
    else:
        query = query.order_by(Okr.created_at.asc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

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

    return {
        "data": data,
        "total_page": total_page
    }

async def get_ai_okr_result(db: AsyncSession, okr_id):
    query = select(Okr, Prediction).join(Prediction, (Prediction.okr_id == Okr.id), isouter=True).where(Okr.id == okr_id)

    result = await db.execute(query)
    rows = result.all()
    
    if rows is None:
        return None

    print(rows)
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
    return data



async def create_eval_okr(okr_id: int, type: str, score: int, description: str):
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
        
        return True

async def update_revision_okr(okr_id: int, revision: str, description: str):
    async for db in get_db():
        stmt = update(Okr).where(
            (Okr.id == okr_id)
        ).values(
            revision=revision,
            revision_description=description
        )

        async with db.begin():
            result = await db.execute(stmt)

        return True

