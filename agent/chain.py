from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
from abc import ABC, abstractmethod
from typing import override

# from RAG import RAG
from agent import RAG


load_dotenv()

openai_deployment = os.getenv("OPENAI_DEPLOYMENT", "gpt-4")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("Missing OPENAI_API_KEY in environment variables")

# Initialize OpenAI model
model = ChatOpenAI(
    model=openai_deployment,
    openai_api_key=openai_api_key,
    temperature=0.2,
    max_tokens=500,
    timeout=30,
    max_retries=3
)

# Define output parser
output_parser = StrOutputParser()


class Chain(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def invoke(self, inputs: dict) -> str:
        pass
    
    def retry_chain_invoke(self, chain, inputs: dict, validation_fn: callable, max_retries: int = 3):
        """
        Invoke a chain with retries if validation fails
        
        Args:
            chain: The chain to invoke
            inputs: Dictionary of inputs for the chain
            validation_fn: Function that validates the response
            max_retries: Maximum number of retry attempts
        
        Returns:
            Valid response or raises ValueError after max retries
        """
        for attempt in range(max_retries):
            response = chain.invoke(inputs)
            if validation_fn(response):
                return response
            print(f"Validation failed, attempt {attempt + 1} of {max_retries}")
            print("Failed response: ", response)
        
        raise ValueError(f"Failed to get valid response after {max_retries} attempts")



class PlannerChain(Chain):
    def __init__(self):
        super().__init__()

        interface_prompt = """
        You are a interface agent.
        Your task is as follows:
        1. Receive a query from the user.
        2. If the query is not about a task, respond to the user directly.
           If the query is about a task, entrust the task to the core agent. 
        4. After the core agnet has completed the task, you will receive the result.
        5. Given the result, respond to the user.

        Here are some rules about who to react to:
        - If you want to react to the user, say '/human' as prefix
        - If you want to react to the core agent, say '/core' as prefix

        And there are additional rules about how to react:
        - If your prefix is '/human', you respond to the user with his language.
        - If your prefix is '/core', you respond to the core agent with English ONLY.

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
        interface_prompt_template = ChatPromptTemplate.from_messages([
            ("system", interface_prompt),
            ("human", "the user's query: {human_query}")
        ])
        interface_output_correction = lambda x: x.replace('$', '/')             # 계속 $와 /를 혼동하므로 교정 함수 추가
        self.interface_chain = interface_prompt_template | model | output_parser | interface_output_correction

        interpreter_prompt = """
        You are a interpreter agent.
        At first, you'll receive a query from the interface agent.
        And your task is to create a query, which will be a input for RAG and a core agent.
        RAG will find a command guideline for the query.
        Then the core agent get both the command guideline and your query.
        If the core agent find that there are unmatched command guideline and your query, it will ask you to change the query.
        And you need to change the query and send it to the core agent again.

        You need to respond to the core agent with English ONLY except for the task info lik name, date, and group.
        """
        interpreter_prompt_template = ChatPromptTemplate.from_messages([
            ("system", interpreter_prompt),
            ("system", "the interface agent's query: {interface_query}"),
            MessagesPlaceholder(variable_name="history"),
            ("system", "your response: ")
        ])
        self.interpreter_chain = interpreter_prompt_template | model | output_parser

        core_prompt = """
        You are a core agent.
        Your task is as follows:
        1. Receive a query from the interpreter agent.
        2. With the interpreter agent's query, you will receive a command guideline.
        3. Based on the interpreter agent's query and the command guideline, generate a command.
        4. If the command guildeline is unmatched with the interpreter agent's query, ask the interpreter agent to change the query.

        Example:
        the interpreter agent's query: Create a task named 'Afternoon work' from 5 pm to 5:30 pm
        the command guideline: {{"name": "add_task", "description": "Add a task to the task list", "parameters": {{"name": {{"type": "string", "description": "The name of the task"}}, "date": {{"type": "string", "description": "The date of the task in either format:\n- Single datetime: 'YYYY-MM-DD HH:MM'\n- Start and end datetime: 'YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM'"}}, "group": {{"type": "string", "description": "The group of the task"}}}}, "opcode": "add", "usage": "/add <name> <date> <group>", "example": ["/add task_name '2025-12-31 23:59' '2026-01-01 00:01' group_name", "/add task_name '2025-12-31 23:59' 'None' group_name", "/add task_name '2025-12-31 23:59' group_name"]}}
        the core agent's response: /add 'Afternoon work' '2025-12-31 17:00' '2025-12-31 17:30' 'None'

        the interpreter agent's query: Show me the task list
        the command guideline: {{"name": "show_tasks", "description": "Show all tasks in the task list", "parameters": {{}}, "opcode": "show", "usage": "/show", "example": ["/show"]}}
        the core agent's response: /show

        P.S.
        When you add the date in the parameters, you need to add the date in the format of 'YYYY-MM-DD HH:MM'.
        And the date would be covered by ''.
        If there are multiple dates, you need to add the date in the format of 'YYYY-MM-DD HH:MM' 'YYYY-MM-DD HH:MM'.
        """
        core_prompt_template = ChatPromptTemplate.from_messages([
            ("system", core_prompt),
            ("system", "the interpreter agent's query: {interpreter_query}"),
            ("system", "the command guideline: {command_guideline}"),
            ("system", "the core agent's response: ")
        ])
        self.core_chain = core_prompt_template | model | output_parser

        self.rag = RAG("command_vector_store", "agent/vector_store/command", k=2)

    
    # input: human_query
    # output: total response
    @override
    def invoke(self, inputs: dict) -> str:
        human_query = inputs

        interface_agent_response = self.interface_response(human_query)
        print("interface agent response: ", interface_agent_response)

        # "/human"
        if interface_agent_response.startswith("/human"):
            print("[Human]")

            human_response = interface_agent_response.split("/human")[1].strip()
            return human_response
        
        # "/core"
        print("[Core]")
        
        # not directly to the core agents, but to the interpreter agent
        interpreter_query = interface_agent_response.split("/core")[1].strip()
        print("interpreter query: ", interpreter_query)

        core_agent_response = self.communicate(interpreter_query)

        return core_agent_response
    
    
    def interface_response(self, human_query):
        interface_agent_query = {
            "human_query": human_query
        }
        interface_agent_response = self.retry_chain_invoke(
            self.interface_chain,
            interface_agent_query,
            lambda x: x.startswith("/human") or x.startswith("/core")
        )
        return interface_agent_response
    
    def interpreter_response(self, interface_query, history: InMemoryChatMessageHistory):
        interpreter_agent_query = {
            "interface_query": interface_query,
            "history": history.messages
        }
        interpreter_agent_response = self.interpreter_chain.invoke(interpreter_agent_query)
        return interpreter_agent_response
    
    def core_response(self, interpreter_query, command_guideline):
        core_agent_query = {
            "interpreter_query": interpreter_query,
            "command_guideline": command_guideline
        }
        core_agent_response = self.core_chain.invoke(core_agent_query)
        return core_agent_response
    

    def communicate(self, interface_query, max_communication=3):
        # for the agents
        chat_history = InMemoryChatMessageHistory()

        for i in range(max_communication):
            # interpreter
            interpreter_response = self.interpreter_response(interface_query, chat_history)
            chat_history.add_user_message(f"interpreter agent: {interpreter_response}")
            print(f"Interpreter agent: {interpreter_response}")

            # ragn & core
            command_guideline = self.rag.search(interpreter_response)
            core_agent_response = self.core_response(interpreter_response, command_guideline)

            # success to create the command
            if core_agent_response.startswith("/"):
                return core_agent_response
            
            # fail to create the command
            chat_history.add_ai_message(f"core agent: {core_agent_response}")
            print(f"Core agent: {core_agent_response}")

        # after all try are failed, raise Exception

