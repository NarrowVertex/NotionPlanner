import requests
import json

import os
from dotenv import load_dotenv

from task import Task


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
    return response.json()

def request_post(endpoint, json_data):
    url = base_url + endpoint
    response = requests.post(url, headers={**headers, 'Content-Type': 'application/json'}, json=json_data)
    return response.json()

def request_tasks():
    request_json = None
    response = request_post('/databases/' + database_id + '/query', request_json)
    return response


# functions
def get_tasks():
    response = request_tasks()
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
    url = base_url + endpoint
    response = requests.patch(url, headers=headers, json={'archived': True})
    return response.json()

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
    url = base_url + endpoint
    response = requests.patch(url, headers=headers, json=request_json)
    return response.json()

