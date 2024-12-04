# +
import psycopg2
import pandas as pd
# PostgreSQL 연결 정보
db_host = 'localhost'  
db_name = 'eqsdb'
db_port = '5432'  
db_user = 'testuser'
db_password = '1234'

# PostgreSQL 연결
conn = psycopg2.connect(
    host=db_host,
    database=db_name,
    port=db_port,
    user=db_user,
    password=db_password
)

# 커서 생성
cur = conn.cursor()


# 엑셀 파일을 읽어오는 코드
df = pd.read_csv('240819_dataset_augmented_lreason_wg.csv')
df = df[["type", "input_sentence", "upper_objective", "company", "field", "team", "company_description"]]


conn.commit()

cur.execute("""
  create table company (
	id		serial 				primary key,
	name 	varchar(63),
	field 		varchar(63),
    description     varchar(2047),
    filename    varchar(127),
    CONSTRAINT unique_company UNIQUE (name, field)
);""")
conn.commit()




#objective
cur.execute("""create table okr (
	id serial primary key,
	is_objective	boolean,
	input_sentence		varchar(255),
    upper_objective      varchar(255),
    team 			varchar(63),
    guideline               varchar(2047),
    revision                varchar(255),
    revision_description    varchar(2047),
    company_id  int,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	foreign key (company_id) references company(id));""")
conn.commit()


cur.execute("""create table prediction (
    id serial primary key,
    type    varchar(16),
    score   int,
    description varchar(2047),
    okr_id  int,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    foreign key (okr_id) references okr(id),
    constraint unique_okr_type UNIQUE (okr_id, type));""")

conn.commit()

insert_company_query = """
INSERT INTO company (name, field, description)
VALUES (%s, %s, %s)
ON CONFLICT (name, field) DO NOTHING
RETURNING id;
"""
cur.execute("""
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

conn.commit()

cur.execute("""
    CREATE TRIGGER trigger_set_updated_at
    BEFORE UPDATE ON prediction
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
""")
    
conn.commit()

# company_ids = []
# for index, row in df.iterrows():
#     cur.execute(insert_company_query, (row['company'], row['field'], row['team'], row['company_description']))
#     company_id = cur.fetchone()  # 삽입된 company_id 값을 가져오기
#     if company_id:  # 삽입된 회사가 있으면 ID를 리스트에 추가
#         company_ids.append(company_id[0])
#     else:
#         # 중복된 회사가 있을 경우, 이미 있는 회사의 id를 가져오기
#         cur.execute("""
#         SELECT id FROM company WHERE name = %s AND field = %s AND team = %s
#         """, (row['company'], row['field'], row['team']))
#         company_id = cur.fetchone()[0]
#         company_ids.append(company_id)

# # 2. okr 테이블에 데이터 삽입
# insert_okr_query = """
# INSERT INTO okr (
#     is_objective,
#     input_sentence,
#     upper_objective,
#     company_id
# ) VALUES (%s, %s, %s, %s);
# """

# # company_id 값들을 사용하여 okr 데이터 삽입
# for index, row in df.iterrows():
#     is_objective = row["type"] == "Objective"
#     company_id = company_ids[index]  # 이전에 삽입된 company의 id를 가져오기
#     cur.execute(insert_okr_query, (
#         is_objective,
#         row['input_sentence'],
#         row['upper_objective'],
#         company_id  # foreign key
#     ))

# # 커밋하여 변경 사항 저장
# conn.commit()

# 커서 및 연결 종료
cur.close()
conn.close()





