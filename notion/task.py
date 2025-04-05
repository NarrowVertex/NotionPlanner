from datetime import datetime


class Task:
    def __init__(self, task_id, name, date, group):
        self.task_id = task_id
        self.name = name

        if isinstance(date, str):
            date = {
                'start': date,
                'end': None
            }
        
        date['start'] = None if date['start'] == "None" else date['start']
        date['end'] = None if date['end'] == "None" else date['end']

        self.date = {
            'start': date.get('start', None) if isinstance(date.get('start'), datetime) else datetime.fromisoformat(date.get('start')) if date.get('start') else None,
            'end': date.get('end', None) if isinstance(date.get('end'), datetime) else datetime.fromisoformat(date.get('end')) if date.get('end') else None
        }

        if self.date['start']:
            self.date['start'] = self.date['start'].astimezone()
        if self.date['end']:
            self.date['end'] = self.date['end'].astimezone()

        self.group = group
        self.description = None

    def __str__(self):
        date_string = f"{self.date['start'].strftime('%Y-%m-%d %H:%M')}" if self.date['start'] else ''
        if self.date['end']:
            date_string += f" ~ {self.date['end'].strftime('%Y-%m-%d %H:%M')}"
        
        # not to confuse with the group name empty
        group_string = f"{self.group}" if self.group else ''

        string = f"[{self.task_id}][{self.name}][{date_string}][{group_string}]"
        return string