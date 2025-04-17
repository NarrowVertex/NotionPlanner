from langchain_core.chat_history import InMemoryChatMessageHistory

# from agent import RAG
# from agent import FrontChain, CoreChain
from RAG import RAG
from chain import FrontChain, CoreChain


class PlannerAgent:
    def __init__(self):
        """ TODO
        두개의 pipeline으로 운영
        1. front pipeline: 사용자의 질문을 받아서 답변을 생성하는 pipeline
        2. core pipeline: 사용자의 질문을 받아서 명령어를 생성하는 pipeline
        
        front pipeline
        - 사용자와 직접 대화하는 파이프라인
        - core pipeline한테 명령어 생성을 요구하고, 그 결과를 받아서 사용자한테 대답함
        
        core pipeline
        - front pipeline한테 받은 명령어 생성을 요구받아 명령어를 생성하고, 그 결과를 front pipeline한테 전달함
        - 단계별로 명령어를 생성하고 실행하여, 목표 결과까지 도달하는 것이 목표
        - 명령어를 생성하고 실행하고 결과를 받고, 다시 명령어를 생성하는 루프에서 최종 목표에 도달하면 최종 결과를 front pipeline한테 전달함
        """

        """ TODO
        front agent와 core agent와의 상호 대화를 통해서
        core agent에서 front agent에게 command guideline으로 얻은 명령어가 적절치 않은 경우에
        다른 명령어를 요구하고 front agent가 다시 query를 생성해서 command guideline을 생성하여 다시 전달할 수 있도록 구성해야 함
        """

        # Initialize functions
        self.chat_history = InMemoryChatMessageHistory()

        self.front_chain = FrontChain()
        self.core_chain = CoreChain()

        self.rag = RAG("command_vector_store", "agent/vector_store/command")


    def response(self, human_query):
        front_agent_query = {
            "human_query": human_query
        }
        front_agent_response = self.front_chain.retry_chain_invoke(
            front_agent_query,
            lambda x: x.startswith("/human") or x.startswith("/core")
        )
        print("Front agent response: ", front_agent_response)

        # "/human"
        if front_agent_response.startswith("/human"):
            print("[Human]")

            human_response = front_agent_response.split("/human")[1].strip()
            return human_response
        
        # "/core"
        print("[Core]")
        
        core_query = front_agent_response.split("/core")[1].strip()
        print("Core query: ", core_query)

        command_guideline = self.rag.search(core_query)
        print("Command guideline: ", command_guideline)
        
        core_agent_query = {
            "front_query": core_query,
            "command_guideline": command_guideline
        }
        
        core_agent_response = self.core_chain.invoke(core_agent_query)
        print("Core agent response: ", core_agent_response)
        return core_agent_response
    
    

if __name__ == "__main__":
    agent = PlannerAgent()
    while True:
        query = input("Human: ")
        response = agent.response(query)
        print("AI:", response)
        print()

    """
    agent = PlannerAgent()
    print(agent.rag.search("add task"))
    """