from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
from abc import ABC, abstractmethod
from typing import override


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
    
    def retry_chain_invoke(self, inputs: dict, validation_fn: callable, max_retries: int = 3):
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
            response = self.invoke(inputs)
            if validation_fn(response):
                return response
            print(f"Validation failed, attempt {attempt + 1} of {max_retries}")
            print("Failed response: ", response)
        
        raise ValueError(f"Failed to get valid response after {max_retries} attempts")



class FrontChain(Chain):
    def __init__(self):
        super().__init__()

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

        # 계속 $와 /를 혼동하므로 교정 함수 추가
        front_output_correction = lambda x: x.replace('$', '/')

        self.front_chain = front_prompt_template | model | output_parser | front_output_correction
        self.front_chain_core_responsed = front_prompt_core_responsed_template | model | output_parser
    
    @override
    def invoke(self, inputs: dict) -> str:
        return self.front_chain.invoke(inputs)


class CoreChain(Chain):
    def __init__(self):
        super().__init__()

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

        P.S.
        When you add the date in the parameters, you need to add the date in the format of 'YYYY-MM-DD HH:MM'.
        And the date would be covered by ''.
        If there are multiple dates, you need to add the date in the format of 'YYYY-MM-DD HH:MM' 'YYYY-MM-DD HH:MM'.
        """

        core_prompt_template = ChatPromptTemplate.from_messages([
            ("system", core_prompt),
            ("system", "the front agent's query: {front_query}"),
            ("system", "the command guideline: {command_guideline}"),
            ("system", "the core agent's response: ")
        ])

        self.core_chain = core_prompt_template | model | output_parser

    @override
    def invoke(self, inputs: dict) -> str:
        return self.core_chain.invoke(inputs)