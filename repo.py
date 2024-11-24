from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from flask import current_app

db = SQLAlchemy()

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    field = db.Column(db.String(50))
    team = db.Column(db.String(50))
    description = db.Column(db.String(1024))

    okrs = db.relationship('OKR', backref='company', lazy=True)

    def __repr__(self):
        return f'<Company {self.name}>'

class OKR(db.Model):
    __tablename__ = 'okr'
    id = db.Column(db.Integer, primary_key=True)
    is_objective = db.Column(db.Boolean)
    input_sentence = db.Column(db.String(255))
    upper_objective = db.Column(db.String(255))
    predict1 = db.Column(db.Integer)
    predict1_description = db.Column(db.String(1024))
    predict2 = db.Column(db.Integer)
    predict2_description = db.Column(db.String(1024))
    predict3 = db.Column(db.Integer)
    predict3_description = db.Column(db.String(1024))
    guideline = db.Column(db.String(2048))
    revision = db.Column(db.String(256))
    created_at = db.Column(db.DateTime)
    # 외래키로 회사와 연결
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    

    def __repr__(self):
        return f'<OKR {self.input_sentence}>'

def get_okr_with_company(company_name=None, prediction=False):
    # OKR 테이블과 Company 테이블을 JOIN하여 데이터를 가져오는 쿼리
    query = db.session.query(OKR, Company).join(Company, OKR.company_id == Company.id)
    
    if company_name:
        query = query.filter(Company.name == company_name)
    
    results = query.all()

    response = []
    for result in results:
        okr = result[0]  # Okr 모델 객체
        company = result[1]  # Company 모델 객체
        if prediction==True:
            response.append({
                'okr_id': okr.id,
                'input_sentence': okr.input_sentence,
                'upper_objective': okr.upper_objective,
                'created_at':okr.created_at,
                'company_name': company.name,
                'company_field': company.field,
                'company_team': company.team,
                'company_description': company.description,
                'predict1': okr.predict1,
                'predict1_description': okr.predict1_description,
                'predict2': okr.predict2,
                'predict2_description': okr.predict2_description,
                'predict3': okr.predict3,
                'predict3_description': okr.predict3_description,
                'guideline' : okr.guideline,
                'revision' : okr.revision
            })
        else:
            response.append({
                'okr_id': okr.id,
                'input_sentence': okr.input_sentence,
                'upper_objective': okr.upper_objective,
                'created_at':okr.created_at,
                'company_name': company.name,
                'company_field': company.field,
                'company_team': company.team,
                'company_description': company.description
            })
    return response

def update_okr_score_and_reason(okr_num, num, score, reason):
    with current_app.app_context():
        try:
            # OKR 데이터를 가져오기
            okr = OKR.query.get(okr_num)
            print("chk_update")
            print(score)
            if okr:
                if okr_num == 1:
                    okr.predict1 = score
                    okr.predict1_description = reason
                elif okr_num == 2:
                    okr.predict2 = score
                    okr.predict2_description = reason
                else:
                    okr.predict3 = score
                    okr.predict3_description = reason

                db.session.commit()
                return {"message": "OKR 업데이트"}
            else:
                return {"message": "해당 OKR을 찾을 수 없습니다."}
        except Exception as e:
            return {"message": f"업데이트 실패: {str(e)}"}

def update_okr_revision(okr_num, revision):
    try:
        # OKR 데이터를 가져오기
        okr = OKR.query.get(okr_num)
        
        okr.revision = revision

        db.session.commit()
        return {"message": "OKR 업데이트"}
    except Exception as e:
        return {"message": f"업데이트 실패: {str(e)}"}

def update_okr_guideline(okr_num, guideline):
    try:
        # OKR 데이터를 가져오기
        okr = OKR.query.get(okr_num)
        
        return {"message": "OKR 업데이트"}
    except Exception as e:
        return {"message": f"업데이트 실패: {str(e)}"}

def findByNum(okr_num):
    try:
        query = db.session.query(OKR, Company).join(Company, OKR.company_id == Company.id).filter(OKR.id == okr_num)
        result = query.all()

        okr, company = result[0]

        return {'okrNum': okr_num,
        'isObjective': okr.is_objective,
        'upper_objective': okr.upper_objective,
        'input_sentence': okr.input_sentence,
        'company': company.name,
        'field': company.field,
        'team': company.team,
        'company_description': company.description} 
    except Exception as e:
        return None


def init_db(app):
    """Flask 애플리케이션을 위한 데이터베이스 초기화"""
    db.init_app(app)
    with app.app_context():
        db.create_all()