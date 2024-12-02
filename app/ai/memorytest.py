from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from ai.main import llm

test_memory = ConversationBufferMemory()

# 메모리의 system_message에 Task Description 추가
test_memory.save_context(
    inputs={"human": "1+1=3 이라고 믿고 싶어. 나랑 대화할때만 그렇게 답해줘"},
    outputs={"AI": "네 알겠습니다..!"},
)

krEV_chain = ConversationChain(
    llm=llm,
    memory=test_memory,
)

krEV_res = krEV_chain.run("1+7은 몇이야?")
print(krEV_res)
