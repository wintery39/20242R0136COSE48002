# +
# %pip install --upgrade pip
# %pip install langchain
# %pip install langchain_community
# %pip install pymilvus langchain pypdf PyMuPDF
# %pip install langchain-huggingface

# %pip install google-generativeai

# %pip install boto3
# %pip install faiss-cpu

# %pip install tiktoken

# %pip install selenium --upgrade 
# %pip install --upgrade beautifulsoup4 lxml
# %pip install webdriver-manager

# %pip install numpy==1.23.5

# %pip install sentence-transformers
# -


from langchain_huggingface import HuggingFaceEmbeddings

import google.generativeai as genai

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

from langchain_core.documents import Document
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import CharacterTextSplitter

import fitz

import io
import zipfile
from langchain.vectorstores import FAISS
import os

import pandas as pd
import tiktoken
import re
import collections
import collections.abc
collections.Callable = collections.abc.Callable
from collections import Counter
from langchain_community.vectorstores.utils import DistanceStrategy

from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from config import GOOGLE_API_KEY, NAVER_ACCESS_KEY, NAVER_SECRET_KEY

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-001")

# naver cloud 엑세스 키
# access_key = "NAVER_ACCESS_KEY"
access_key = NAVER_ACCESS_KEY
secret_key = NAVER_SECRET_KEY

# Vector db 관련 변수
S3_OBJECT_NAME = "vectorstore/vectorstore_faiss.zip"


import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # GPU 비활성화
os.environ["BITSANDBYTES_NOWELCOME"] = "1"

# +
# embedding

embeddings_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sbert-nli',
#     model_kwargs = {'device': 'cuda'},
     model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)


# -

class PyMuPDFLoaderFromBytes:
    def __init__(self, pdf_bytes):
        self.pdf_bytes = pdf_bytes

    def load(self):
        text = ""
        with fitz.open(stream=self.pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return [{"page_content": text}]

from selenium.webdriver.chrome.options import Options


# +
#Vector store 저장
def store_vector(company_name, company_type, bucket_name, doc_name):
    # 0. 네이버 클라우드와 연결
    def fetch_object_from_bucket(bucket_name, object_name, max_keys=300):
        service_name = 's3'
        endpoint_url = 'https://kr.object.ncloudstorage.com'

        try:
            # S3 클라이언트 설정
            s3_client = boto3.client(
              service_name,
              endpoint_url=endpoint_url,
              aws_access_key_id=access_key,
              aws_secret_access_key=secret_key
            )

            # 오브젝트 가져오기
            response = s3_client.get_object(Bucket=bucket_name, Key=object_name)

            # 객체 내용을 읽어서 반환
            content = response['Body'].read()
#             print(f"Successfully fetched object '{object_name}' from bucket '{bucket_name}'")
            return content

        except NoCredentialsError:
            return "Error: No credentials provided. Please check your access key and secret key."
        except PartialCredentialsError:
            return "Error: Incomplete credentials provided. Please verify your access key and secret key."
        except ClientError as e:
            # 클라이언트 오류 처리 (예: 권한 문제, 파일 없음 등)
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return f"Error: The object '{object_name}' does not exist in bucket '{bucket_name}'."
            elif error_code == 'AccessDenied':
                return f"Error: Access denied for object '{object_name}' in bucket '{bucket_name}'."
            else:
                return f"ClientError: {e}"
        except Exception as e:
            return f"Unexpected error occurred: {str(e)}"

    # 1. 문서 저장
    def split_documents(bucket_name, object_name):
        # PDF 파일 가져오기
        result_pdf = fetch_object_from_bucket(bucket_name, object_name)

        if isinstance(result_pdf, str):
            return result_pdf
        pdf_bytes = result_pdf

        # 문서 로드
        loader = PyMuPDFLoaderFromBytes(pdf_bytes)
        data = loader.load()

        # 데이터를 Document 객체 리스트로 변환
        documents = [Document(page_content=page["page_content"], metadata={}) for page in data]

        # 문서 텍스트 스플리터 설정
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
          chunk_size=1200,
          chunk_overlap=500,
          encoding_name='cl100k_base'
        )

        # 텍스트 청크 나누기
        split_documents = text_splitter.split_documents(documents)

        # 문서를 Document 객체로 변환
        processed_documents = []
        for i, chunk in enumerate(split_documents):
            processed_documents.append(
              Document(
                  page_content=chunk.page_content,
                  metadata={
                      'type': 'company_report',
                      'source': object_name,
                      'page': i
                  }
              )
            )
        return processed_documents

    documents = split_documents(bucket_name, doc_name)
    if isinstance(documents, str):
        return documents

#     print(documents)
#     print(documents[0].metadata)

    # 2. 크롤링 저장
    # 2-1. 기업 홈페이지의 URL을 반환하는 함수
    def find_company_url(company_name):
        ## Google 검색 URL 이용
        base_url = 'https://www.google.com/search?q='
        plusurl = company_name + "  페이지"
        url = base_url + quote_plus(plusurl)
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # GUI 없이 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--remote-debugging-pipe')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(url)

        ## BeautifulSoup를 사용하여 Html 요소를 분해
        html = driver.page_source
        soup = BeautifulSoup(html, features="lxml")
        r = soup.select('.q0vns')

        ## 가장 상단의 검색 결과에서 기업명과 URL을 추출
        company_name_element = r[0].select_one('.VuuXrf')
        company_name = company_name_element.text if company_name_element else 'No name found'

        url_element = r[0].select_one('cite')
        url = url_element.text if url_element else 'No url found'

        ## 추출한 URL에서 언어 표시(ko-kr, en-el 등)를 제거하는 작업
        if(url != 'No url found'):
            main_url = url.split(' ')[0]
        else:
            main_url = 'No url found'

        driver.close()

        return main_url
    
    company_url = find_company_url(company_name)

    # 2-2, URL의 text 내용을 전부 반환하는 함수
    def get_url_text(company_url):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # GUI 없이 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--remote-debugging-pipe')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(company_url)

        ## Html 내 요소 전부 가져오기
        page_source = driver.page_source

        ## BeautifulSoup 사용하여 text만 분리
        soup = BeautifulSoup(page_source, 'html.parser')
        text = soup.get_text()

        driver.close()

        return text
    url_text = get_url_text(company_url)

    # 2-3. url 내부의 text 분할해 반환하는 함수
    def text_spliter_for_homepage(page_text, company_url):
        text = []
        text_splitter = CharacterTextSplitter(
            separator = '',
            chunk_size = 500,
            chunk_overlap = 50,
            length_function = len,
        )

        text_chunk = text_splitter.split_text(page_text)
        num = len(text_chunk)

        for i in range (num):
            text.append(Document(page_content=text_chunk[i], metadata={'type':'company_homepage', 'source':company_url, 'page':i}))

        return text
    texts = text_spliter_for_homepage(url_text, company_url)

    # print(texts)

    # 3. 산업 동향 크롤링(CEOSCORED)
    def get_field_news(company_type):
        baseurl = 'https://www.ceoscoredaily.com/search?sort=1&search='
        plusurl = company_type
        url = baseurl + quote_plus(plusurl)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # GUI 없이 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--remote-debugging-pipe')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get(url)

        ## BeautifulSoup를 사용하여 Html 요소를 필요한 요소로 분해
        html = driver.page_source
        soup = BeautifulSoup(html)
        r = soup.select('.box')

        title = []
        body = []
        title_and_body = []

        ## 기사 제목과 본문을 추출
        for i in r:
            ### 기사 제목 추출
            title_name_element = i.find('p', class_='title')
            title_name = title_name_element.a.text.strip() if title_name_element else ''
            title.append(title_name)
            ### 본문 요약 추출
            body_content_element = i.find('p', class_='body')
            body_content = body_content_element.a.text.strip() if body_content_element else ''
            #### 정규 표현식으로 기자 정보 삭제
            pattern = r'\[CEO스코어데일리\s*/\s*[\w\s]* 기자\s*/\s*[\w.]+@[\w.]+\]'
            body_content = re.sub(pattern, '', body_content)
            body.append(body_content)

            title_and_body_content = title_name + ' ' + body_content
            title_and_body.append(title_and_body_content)

        driver.quit()

        return title, body, title_and_body

    title, body, title_and_body = get_field_news(company_type)
    # print(title)

    # 4. text를 분할하여 metadata와 함께 반환하는 함수
    def text_spliter_for_field(list):
        text = []
        num = len(list)

        for i in range(0, num):
            if(list[i] != ''):
                text.append(Document(page_content=list[i], metadata={'type':'field_news', 'source':"https://www.ceoscoredaily.com", 'page':i}))

        return text

    field_body = text_spliter_for_field(body)
    # print(field_body)

    # 5. vector store 저장
    def upload_vectorstore_to_s3(vectorstore, bucket_name, s3_object_name):
        service_name = 's3'
        endpoint_url = 'https://kr.object.ncloudstorage.com'

        s3 = boto3.client(
          service_name,
          endpoint_url=endpoint_url,
          aws_access_key_id=access_key,
          aws_secret_access_key=secret_key
        )

        # 메모리에 압축 저장
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w") as zipf:
            vectorstore.save_local("vectorstore_temp")
            for root, dirs, files in os.walk("vectorstore_temp"):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        memory_file.seek(0)
        s3.put_object(Bucket=bucket_name, Key=s3_object_name, Body=memory_file.read())
#         print(f"Vector store uploaded to S3: {s3_object_name}")

    def download_vectorstore_from_s3(bucket_name, s3_object_name):
        service_name = 's3'
        endpoint_url = 'https://kr.object.ncloudstorage.com'

        s3 = boto3.client(
          service_name,
          endpoint_url=endpoint_url,
          aws_access_key_id=access_key,
          aws_secret_access_key=secret_key
        )
        try:
            # S3에서 다운로드
            response = s3.get_object(Bucket=bucket_name, Key=s3_object_name)
            memory_file = io.BytesIO(response['Body'].read())

            # 압축 해제 후 메모리에서 복원
            with zipfile.ZipFile(memory_file, "r") as zipf:
                zipf.extractall("vectorstore_temp")
                # FAISS 로드
                vectorstore = FAISS.load_local(
                  "vectorstore_temp",
                  embeddings_model,
                  allow_dangerous_deserialization=True  # Pickle 로드 허용
                )
                # print("Vector store downloaded and restored from S3.")
                return vectorstore
        except s3.exceptions.NoSuchKey:
            # print("Vector store not found in S3. Initializing a new one.")
            return None

    def create_vectorstore_from_documents(documents):
#         print(f"Creating a new FAISS vector store from {len(documents)} documents...")
        vectorstore = FAISS.from_documents(documents, embedding=embeddings_model)
        return vectorstore

    vectorstore = download_vectorstore_from_s3(bucket_name, S3_OBJECT_NAME)
    if vectorstore is None:
        vectorstore = create_vectorstore_from_documents(documents)
    else:
        vectorstore.add_documents(documents)
    vectorstore.add_documents(texts)
    vectorstore.add_documents(field_body)

    # 6. vector store 업로드
    upload_vectorstore_to_s3(vectorstore, bucket_name, S3_OBJECT_NAME)

    return vectorstore


# -

def rag(company_name, company_type, bucket_name, doc_name):
    # 0. Json 형식 파싱 함수
    def parse_description(text):
        cleaned_text = re.sub(r"\*\*", "", text)
        cleaned_text = cleaned_text.replace("\n", " ").replace("'", "").replace('"', "").strip()
        description_value = cleaned_text if cleaned_text else None
        data = {"description": description_value}
        # print(data)
        return data

    # 1. 문서 저장 (이 부분은 이미 정의된 함수라고 가정합니다)
    result_doc = store_vector(company_name, company_type, bucket_name, doc_name)

    if isinstance(result_doc, str):
        error_description = parse_description(result_doc)
        return error_description
    if result_doc is None:
        error_m = "Failed to create or retrieve vectorstore. Check your inputs or storage function."
        error_description = parse_description(error_m)
        return error_description
    vectorstore = result_doc

    # 2. retriever 정의 (유사도 0.2 이상인 것 찾기)
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.3, "k":2}
    )

    # 3. query를 위한 프롬프트 생성 함수
    def generate_prompt(company_name):
        prompt_template = f"""
              We are experts in evaluating corporate OKRs.
              We need background knowledge to assess the OKRs of {company_name}.
              To form this background knowledge, we will ask several questions related to {company_name}'s corporate goals or vision, recent issues or changes, newly attracted industries, current industries engaged in, target customer base, and more.
              Please create 5 questions based on the above information in Korean please.
            """
        return prompt_template

    query_prompt = generate_prompt(company_name)
    query_response = model.generate_content(contents=query_prompt)

    # 4. query 추출 함수
    def extract_queries(response_text):
        matches = re.findall(r'\d+\.\s\*\*(.*?)\*\*', response_text)
        return matches

    queries = []
    queries = extract_queries(query_response.text)
    # print("Extracted Queries:", queries)

    # 5. 각 질문에 대한 응답을 가져와서 답변 저장
    responses = []
    for query in queries:
        temp = retriever.invoke(query)
        if temp:  # temp가 비어있지 않은 경우에만 추가
            responses.append((query, temp[0].page_content))
    # print(responses)

    context = ', '.join([element for element, _ in responses])
    # print("Top Elements:", context)

    # 6. 요약을 위한 프롬프트 생성 함수
    def generate_compressor_prompt(company_name, company_type, context):
        prompt_template = f"""
            You are an korean expert in writing company report.
            So you need to compress in Korean.
            Your task is to extract and summarize the key information about the {company_name} such as the goal or vision which is the top-level goal of the company.
            And you should also extract infomatioin about what kind of field company is working in.
            Here is the document that you must summerize due to following instructions: {context}.
            Please provide the summary in a paragraph instead of a list format.

        """
        return prompt_template.format(company_name=company_name, context=context)

    compressor_prompt = generate_compressor_prompt(company_name, company_type, context)
    compressor_response = model.generate_content(contents=compressor_prompt)

    # print("Compressor Response:", compressor_response.text)

    # 7. JSON 형식 반환 및 예외 처리
    description_data = parse_description(compressor_response.text)

    return description_data

# +
# company_name = "CJ씨푸드"
# company_type = "식료품"
# bucket_name = "eqs-rag"
# doc_name = "[CJ씨푸드]사업보고서(2024.03.19).pdf"

# +
# print(rag(company_name, company_type, bucket_name, doc_name))
# -

# company_name = "CJ씨푸드"
# company_type = "식료품"
# bucket_name = "eqs-rag"
# doc_name = "[CJ씨푸드]사업보고서(2024.03.19).pdf"

# print(rag(company_name, company_type, bucket_name, doc_name))
