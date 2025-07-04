import requests
import json
import datetime

import os
from dotenv import load_dotenv

from notion import Task


# initialize the environment variables
load_dotenv()
api_key = os.getenv('NOTION_API_KEY')
database_id = os.getenv('NOTION_DATABASE_ID')

base_url = 'https://api.notion.com/v1'

headers = {
    'Authorization': 'Bearer ' + api_key,
    'Notion-Version': '2022-06-28'
}


# request functions
def request_get(endpoint):
    url = base_url + endpoint
    response = requests.get(url, headers=headers)
    response.raise_for_status()     # Raise an error for bad responses (4xx and 5xx)

    return response.json()

def request_post(endpoint, json_data):
    url = base_url + endpoint
    response = requests.post(url, headers={**headers, 'Content-Type': 'application/json'}, json=json_data)
    response.raise_for_status()

    return response.json()


def request_patch(endpoint, json_data):
    url = base_url + endpoint
    response = requests.patch(url, headers=headers, json=json_data)
    response.raise_for_status()
    
    return response.json()


# functions
def get_tasks():
    response = request_post('/databases/' + database_id + '/query', None)       # get all tasks from the database (max 20 tasks)
    
    tasks = []
    for item in response['results']:
        properties = item['properties']
        task_id = item['id']
        name = properties['이름']['title'][0]['plain_text'] if properties['이름']['title'] else ''
        start_date = properties.get('날짜', {}).get('date', {}).get('start', '')
        end_date = properties.get('날짜', {}).get('date', {}).get('end', '')
        date = {'start': start_date, 'end': end_date}
        group = properties.get('그룹', {}).get('select', {}).get('name', '') if properties.get('그룹', {}).get('select') else ''
        tasks.append(Task(task_id, name, date, group))
    return tasks

def get_tasks_by_group(group_name):
    filter_condition = {
        "property": "그룹",
        "select": {
            "equals": group_name
        }
    }
    request_json = {
        "filter": filter_condition
    }
    response = request_post('/databases/' + database_id + '/query', request_json)       # get all tasks from the database (max 20 tasks)
    
    tasks = []
    for item in response['results']:
        properties = item['properties']
        task_id = item['id']
        name = properties['이름']['title'][0]['plain_text'] if properties['이름']['title'] else ''
        start_date = properties.get('날짜', {}).get('date', {}).get('start', '')
        end_date = properties.get('날짜', {}).get('date', {}).get('end', '')
        date = {'start': start_date, 'end': end_date}
        group = properties.get('그룹', {}).get('select', {}).get('name', '') if properties.get('그룹', {}).get('select') else ''
        tasks.append(Task(task_id, name, date, group))
    return tasks

def get_tasks_after_now():
    now_date = datetime.datetime.now().astimezone().isoformat()
    filter_condition = {
        "property": "날짜",
        "date": {
            "on_or_after": now_date
        }
    }
    request_json = {
        "filter": filter_condition
    }
    response = request_post('/databases/' + database_id + '/query', request_json)       # get all tasks from the database (max 20 tasks)
    tasks = []
    for item in response['results']:
        properties = item['properties']
        task_id = item['id']
        name = properties['이름']['title'][0]['plain_text'] if properties['이름']['title'] else ''
        start_date = properties.get('날짜', {}).get('date', {}).get('start', '')
        end_date = properties.get('날짜', {}).get('date', {}).get('end', '')
        date = {'start': start_date, 'end': end_date}
        group = properties.get('그룹', {}).get('select', {}).get('name', '') if properties.get('그룹', {}).get('select') else ''
        tasks.append(Task(task_id, name, date, group))
    return tasks

def add_task_to_remote(task):
    name = task.name
    date = task.date
    group = task.group

    properties = {
        '이름': {
            'title': [{'text': {'content': name}}]
        },
        '날짜': {
            'date': {
                'start': date['start'].isoformat() if date['start'] else None,
                'end': date['end'].isoformat() if date['end'] else None
            }
        }
    }
    
    # 그룹이 None이면 추가하지 않음
    if group is not None:
        properties['그룹'] = {'select': {'name': group}}
    
    request_json = {
        'parent': {'database_id': database_id},
        'properties': properties
    }
    
    response = request_post('/pages', request_json)
    task_id = response['id']
    return task_id

def delete_task_from_remote(task_id):
    endpoint = f'/pages/{task_id}'
    request_json = {'archived': True}

    response = request_patch(endpoint, request_json)
    return response

def edit_task_from_remote(task_id, task):
    properties = {
        '이름': {
            'title': [{'text': {'content': task.name}}]
        },
        '날짜': {
            'date': {
                'start': task.date['start'].isoformat() if task.date['start'] else None,
                'end': task.date['end'].isoformat() if task.date['end'] else None
            }
        }
    }
    
    # 그룹이 None이면 추가하지 않음
    if task.group is not None:
        properties['그룹'] = {'select': {'name': task.group}}
    
    request_json = {
        'properties': properties
    }
    
    endpoint = f'/pages/{task_id}'
    response = request_patch(endpoint, request_json)
    return response

