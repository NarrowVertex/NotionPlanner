from typing import Literal, Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.graph import END

from langgraph.prebuilt import create_react_agent

from dotenv import load_dotenv
import os

from langchain.agents import Tool
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from datetime import datetime, timedelta
import json


def get_tool_agent(planner, task_cls):
    load_dotenv()

    # 메모리 저장소 설정
    memory = MemorySaver()

    # planner = Planner()
    # planner = ConfirmablePlanner()

    # 대화 및 요약을 위한 모델 초기화
    model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # planner 도구
    class ShowTasksSchema(BaseModel):
        pass

    def show_tasks():
        return planner.show_tasks()

    class ShowTasksAfterNowSchema(BaseModel):
        pass

    def show_tasks_after_now():
        return planner.show_tasks_after_now()

    class CreateTaskSchema(BaseModel):
        name: str = Field(..., description="Task name")
        start_date: str = Field(..., description="""The start datetime of the task, format: 'YYYY-MM-DD HH:MM'""")
        end_date: str = Field(None, description="The end datetime of the task, format: 'YYYY-MM-DD HH:MM'. If not provided, the task is considered to have no end date.")
        group: str = Field(..., description="Task group, e.g., '일상', '이벤트'")

    def create_task(name, start_date, end_date, group):
        if end_date:
            date = {"start": start_date, "end": end_date}
        else:
            date = {"start": start_date, "end": None}

        task = task_cls(task_id=None, name=name, date=date, group=group)
        return planner.add_task(task)

    # def create_task(name, date, group):
    #     try:
    #         date_count = date.count(":")
    #         if date_count == 1:
    #             date = {"start": date, "end": None}
    #         elif date_count == 2:
    #             part = date.split(" ")
    #             start = f"{part[0]} {part[1]}"
    #             end = f"{part[2]} {part[3]}"
    #             date = {"start": start, "end": end}
    #         else:
    #             raise ValueError("Invalid date format. Use 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM'.")
    #     except ValueError as e:
    #         raise ValueError(f"Error parsing date: {e}")

    #     task = Task(task_id=None, name=name, date=date, group=group)
    #     return planner.add_task(task)


    class DeleteTaskSchema(BaseModel):
        task_id: str = Field(..., description="The ID of the task to delete")

    def delete_task(task_id):
        return planner.delete_task(task_id)

    class DeleteTasksSchema(BaseModel):
        task_ids: Annotated[List[str], """A list of task IDs to delete. Example: '["task_id_1", "task_id_2"]'"""]

    def delete_tasks(task_ids):
        return planner.delete_tasks(task_ids)

    class EditTaskSchema(BaseModel):
        task_id: str = Field(..., description="The ID of the task to edit")
        name: str = Field("No name", description="New task name")
        date: str = Field("2000-01-01 00:00", description="New date of the task, either format:\n- Single datetime: 'YYYY-MM-DD HH:MM'\n- Start and end datetime: 'YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM'")
        group: str = Field("no group", description="New task group, e.g., '일상', '이벤트'")

    def edit_task(task_id, name, date, group):
        new_task = task_cls(task_id=task_id, name=name, date=date, group=group)
        return planner.edit_task(task_id, new_task)

    class EditTasksSchema(BaseModel):
        tasks: str = Field(..., description="""A JSON string representing a list of tasks to edit. Each task should be a list with the format: [task_id, name, date, group].
                            task_id: The ID of the task to edit
                            name: New task name
                            date: New date of the task, either format:
                            - Single datetime: 'YYYY-MM-DD HH:MM'
                            - Start and end datetime: 'YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM'
                            group: New task group, e.g., '일상', '이벤트'
                        
                        Example: '[["task_id_1", "New Task 1", "2023-10-01 12:00", "일상"], ["task_id_2", "New Task 2", "2023-10-02 14:00", "이벤트"]]'""")
        
    def edit_tasks(tasks):
        try:
            str_task_list = json.loads(tasks)

            if not isinstance(str_task_list, list):
                raise ValueError("Tasks should be a list of task.")
            
            tasks = {}
            for str_task in str_task_list:
                if not isinstance(str_task, list):
                    raise ValueError("Each task should be a list.")
                
                task_id = str_task[0]
                name = str_task[1]
                date = str_task[2]
                group = str_task[3]
                task = task_cls(task_id=task_id, name=name, date=date, group=group)
                tasks[task_id] = task
            
            return planner.edit_tasks(tasks)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid format: {e}")


    # 기타 도구
    class GetNowDatetimeSchema(BaseModel):
        pass

    def get_now_datetime():
        return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %A')

    class CalculateDatetimeWithNumberOfDaysSchema(BaseModel):
        date: str = Field(..., description="The date to calculate from, in the format 'YYYY-MM-DD HH:MM'.")
        number_of_days: int = Field(..., description="The number of days to add or subtract. Use negative values to subtract days.")

    def calculate_datetime_with_number_of_days(date: str, number_of_days: int):
        try:
            # Parse the input date
            dt = datetime.strptime(date, '%Y-%m-%d %H:%M')
            # Add or subtract the number of days
            new_dt = dt + timedelta(days=number_of_days)
            # Return the new date in the desired format
            return new_dt.strftime('%Y-%m-%d %H:%M %A')
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")

    class GetAllDatesBetweenSchema(BaseModel):
        start_date: str = Field(..., description="The start date in the format 'YYYY-MM-DD HH:MM'.")
        end_date: str = Field(..., description="The end date in the format 'YYYY-MM-DD HH:MM'.")

    def get_all_dates_between(start_date: str, end_date: str) -> List[str]:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
            
            if start_dt > end_dt:
                raise ValueError("Start date must be before or equal to end date.")
            
            date_list = []
            current_dt = start_dt
            while current_dt <= end_dt:
                date_list.append(current_dt.strftime('%Y-%m-%d %H:%M %A'))
                current_dt += timedelta(days=1)
            
            return date_list
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")

    tools = [
        StructuredTool.from_function(
            func=show_tasks,
            name="ShowTasks",
            description="Show all the tasks.",
            args_schema=ShowTasksSchema
        ),
        
        StructuredTool.from_function(
            func=show_tasks_after_now,
            name="ShowTasksAfterNow",
            description="Show tasks that are scheduled after the current time.",
            args_schema=ShowTasksAfterNowSchema
        ),
        StructuredTool.from_function(
            func=create_task,
            name="CreateTask",
            description="Create/Add a new task in Notion.",
            args_schema=CreateTaskSchema
        ),
        StructuredTool.from_function(
            func=delete_task,
            name="DeleteTask",
            description="Delete a task from Notion. Input: Notion page ID.",
            args_schema=DeleteTaskSchema
        ),
        StructuredTool.from_function(
            func=delete_tasks,
            name="DeleteTasks",
            description="Delete multiple tasks from Notion. Input: JSON string of task IDs.",
            args_schema=DeleteTasksSchema
        ),
        StructuredTool.from_function(
            func=edit_task,
            name="EditTask",
            description="Update a task's title in Notion. Input: page ID and new title.",
            args_schema=EditTaskSchema
        ),
        StructuredTool.from_function(
            func=edit_tasks,
            name="EditTasks",
            description="Update multiple tasks in Notion. Input: JSON string of task details.",
            args_schema=EditTasksSchema
        ),
        StructuredTool.from_function(
            func=get_now_datetime,
            name="GetNowDatetime",
            description="Get the current date and time in the format 'YYYY-MM-DD HH:MM EEEE'.",
            args_schema=GetNowDatetimeSchema
        ),
        StructuredTool.from_function(
            func=calculate_datetime_with_number_of_days,
            name="CalculateDatetimeWithNumberOfDays",
            description="Calculate a new date by adding or subtracting a number of days from a given date.",
            args_schema=CalculateDatetimeWithNumberOfDaysSchema
        ),
        StructuredTool.from_function(
            func=get_all_dates_between,
            name="GetAllDatesBetween",
            description="Get all dates between two given dates, inclusive.",
            args_schema=GetAllDatesBetweenSchema
        ),
    ]

    tool_agent_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. "
                "Your task is calling a tool as user requested. "
                "Answer in Korean.",
            ),
            ("human", "{messages}"),
        ]
    )

    tool_agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=tool_agent_prompt,
        checkpointer=memory
    )

    return tool_agent