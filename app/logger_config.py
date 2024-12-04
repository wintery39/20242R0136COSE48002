import logging

# 로거 설정
logger = logging.getLogger("my_app")  # 공통 로거 이름
logger.setLevel(logging.INFO)

# 핸들러 설정 (StreamHandler로 콘솔 출력)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
handler.setFormatter(formatter)

# 핸들러를 로거에 추가
if not logger.handlers:
    logger.addHandler(handler)

# 로거 내보내기
__all__ = ["logger"]