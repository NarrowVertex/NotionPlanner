from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from dotenv import load_dotenv
import os

# from agent import RAG
from RAG import RAG


class PlannerAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        openai_deployment = os.getenv("OPENAI_DEPLOYMENT", "gpt-4")  # Default to "gpt-4"
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if not openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment variables")
        
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

        # Initialize functions
        self.chat_history = InMemoryChatMessageHistory()

        front_prompt = """
        You are a front agent.
        Your task is as follows:
        1. Receive a query from the user.
        2. If the query is not about a task, respond to the user directly.
           If the query is about a task, entrust the task to the core agent. 
        4. After the core agnet has completed the task, you will receive the result.
        5. Given the result, respond to the user.

        Here are some rules about who to react to:
        - If you want to react to the user, say '/human' as prefix
        - If you want to react to the core agent, say '/core' as prefix

        Example:

        User: Hey, I'd like to want to know about 'apple'.
        
        You: /human
        Apple is a popular fruit known for its crisp texture and sweet flavor. 
        It comes in various varieties, including red, green, and yellow, and is rich in vitamins, especially vitamin C. 
        Apples are often eaten raw, but they can also be used in cooking and baking, such as in pies or sauces. 
        Additionally, apples are known for their health benefits, including improving heart health and aiding digestion. 
        If you have any specific questions about apples, feel free to ask!

        
        User: Make a task named 'Afternoon work' from 5 pm to 5:30 pm.
        
        You: /core
        Create a task named 'Afternoon work' from 5 pm to 5:30 pm

        
        User: Make a task named 'Afternoon work' from 5 pm to 5:30 pm.
        
        You: /core
        Create a task named 'Afternoon work' from 5 pm to 5:30 pm
        
        Core:
        (Response to query executed commands)

        You: /human
        (Response about the user's query referenced with core's executed commands response.) 
        """

        # prompt
        front_prompt_template = ChatPromptTemplate.from_messages([
            ("system", front_prompt),
            ("human", "the user's query: {human_query}")
        ])

        front_prompt_core_responsed_template = ChatPromptTemplate.from_messages([
            ("system", front_prompt),
            ("human", "the user's query: {human_query}"),
            ("system", "the front agent's query: {front_query}"),
            ("system", "the core agent's response: {core_response}")
        ])

        core_prompt = """
        You are a core agent.
        Your task is as follows:
        1. Receive a query from the front agent.
        2. With the front agent's query, you will receive a command guideline.
        3. Based on the front agent's query and the command guideline, generate a command.
        
        Example:
        the front agent's query: Create a task named 'Afternoon work' from 5 pm to 5:30 pm
        the command guideline: {{"name": "add_task", "description": "Add a task to the task list", "parameters": {{"name": {{"type": "string", "description": "The name of the task"}}, "date": {{"type": "string", "description": "The date of the task in either format:\n- Single datetime: 'YYYY-MM-DD HH:MM'\n- Start and end datetime: 'YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM'"}}, "group": {{"type": "string", "description": "The group of the task"}}}}, "opcode": "add", "usage": "/add <name> <date> <group>", "example": ["/add task_name '2025-12-31 23:59' '2026-01-01 00:01' group_name", "/add task_name '2025-12-31 23:59' 'None' group_name", "/add task_name '2025-12-31 23:59' group_name"]}}
        the core agent's response: /add 'Afternoon work' '2025-12-31 17:00' '2025-12-31 17:30' 'None'

        the front agent's query: Show me the task list
        the command guideline: {{"name": "show_tasks", "description": "Show all tasks in the task list", "parameters": {{}}, "opcode": "show", "usage": "/show", "example": ["/show"]}}
        the core agent's response: /show
        """

        core_prompt_template = ChatPromptTemplate.from_messages([
            ("system", core_prompt),
            ("system", "the front agent's query: {front_query}"),
            ("system", "the command guideline: {command_guideline}"),
            ("system", "the core agent's response: ")
        ])

        # Initialize OpenAI model
        model = ChatOpenAI(
            model=openai_deployment,
            openai_api_key=openai_api_key,
            temperature=0.5,
            max_tokens=500,
            timeout=30,
            max_retries=3
        )

        # Define output parser
        output_parser = StrOutputParser()

        # Combine the pipeline
        self.front_chain = front_prompt_template | model | output_parser
        self.front_chain_core_responsed = front_prompt_core_responsed_template | model | output_parser
        self.core_chain = core_prompt_template | model | output_parser

        self.rag = RAG("command_vector_store", "agent/vector_store/command")

    def response(self, human_query):
        front_agent_response = self.front_chain.invoke({
            "human_query": human_query
        })
        print("Front agent response: ", front_agent_response)

        if front_agent_response.startswith("/human"):
            print("[Human]")
            # Extract response for human query
            human_response = front_agent_response.split("/human")[1].strip()
            response = human_response

        elif front_agent_response.startswith("/core"):
            print("[Core]")
            
            # Extract command guideline from the response
            core_query = front_agent_response.split("/core")[1].strip()
            print("Core query: ", core_query)

            command_guideline = self.rag.search(core_query)
            print("Command guideline: ", command_guideline)

            core_agent_response = self.core_chain.invoke({
                "front_query": human_query,
                "command_guideline": command_guideline
            })
            print("Core agent response: ", core_agent_response)
            
            response = core_agent_response

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