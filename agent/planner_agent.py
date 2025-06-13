from langchain_core.chat_history import InMemoryChatMessageHistory

from agent import RAG
from agent import PlannerChain
# from RAG import RAG
# from chain import PlannerChain
from command import CommandManager

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

        self.planner_chain = PlannerChain()
        self.command_manager = CommandManager()


    def response(self, human_query):
        agent_response = self.planner_chain.invoke(human_query)
        
        if agent_response:
            print("Created command: ", agent_response)
            human_access = input("Do you want to execute the command? (y/n): ").strip().lower()
            if human_access == 'y':
                print(f"Executing command: {agent_response}")
                return self.execute_command(agent_response)
            elif human_access == 'n':
                return "Command execution cancelled."
            else:
                return "Command execution cancelled due to invalid input."
        else:
            print("Failed to create a command after multiple attempts.")
            return "Failed to create a command."
        
        return agent_response

    def execute_command(self, command):
        response = self.command_manager.execute_command(command)
        if response:
            return response
        
    

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