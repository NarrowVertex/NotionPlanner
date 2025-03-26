from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory, HumanMessage, AIMessage

from dotenv import load_dotenv
import os


class MemoriableAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        openai_deployment = os.getenv("OPENAI_DEPLOYMENT", "gpt-4")  # Default to "gpt-4"
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if not openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment variables")
        
        # Initialize functions
        self.chat_history = InMemoryChatMessageHistory()

        query_prompt = ChatPromptTemplate.from_messages([
            ("system", """
             You are a plan manager. 
             Your task is to provide comprehensive responses to user queries. 
             Given the following commands, do your approciate action and provide a response.
             
             Commands:
               1. Show all plans
                 /show
               2. Add a plan
                 /add <plan_name>
               3. Remove a plan
                 /remove <plan_name>
               4. Edit a plan
                 /edit <plan_name> <new_plan_name>
             
             Example:
               Human: 
                 show me all the tasks
               AI: 
                 Alright! Here are all the tasks:
                 ```
                 /show
                 ```
               
               Human:
                 Add a new task
               AI:
                 Certainly! What is the name of the task?
               Human:
                 Workout
               AI:
                 I'll add a task "Workout".
                 ```
                 /add Workout
                 ```
             
             Chat History: """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Current Question: {human_query}"),
            ("system", "Final Response:")
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
        self.query_chain = query_prompt | model | output_parser

    def response(self, human_query):
        response = self.query_chain.invoke({
            "chat_history": self.chat_history.messages,
            "human_query": human_query
        })

        self.chat_history.add_message(HumanMessage(human_query))
        self.chat_history.add_message(AIMessage(response))
        return response
    

if __name__ == "__main__":
    agent = MemoriableAgent()
    while True:
        query = input("Human: ")
        response = agent.response(query)
        print("AI:", response)
        print()