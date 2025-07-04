import threading

import notion


class Planner:
    _instance = None
    _lock = threading.Lock()  # 클래스 수준의 Lock 객체

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:   # 이중 잠금 확인
                    cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.task_list = []
        self.load_tasks()   # Load tasks from remote on initialization

        self._initialized = True


    def load_tasks(self):
        self.task_list = notion.get_tasks()

    def show_tasks(self):
        return "\n".join(str(task) for task in self.task_list)
    
    def show_tasks_by_group(self, group):
        task_list = notion.get_tasks_by_group(group)
        return "\n".join(str(task) for task in task_list) if task_list else "No tasks found in this group."

    def show_tasks_after_now(self):
        task_list = notion.get_tasks_after_now()
        return "\n".join(str(task) for task in task_list) if task_list else "No tasks found after now."

    # add task
    def _add_task_to_local(self, task):
        self.task_list.append(task)

    def add_task(self, task):
        task_id = notion.add_task_to_remote(task)
        task.task_id = task_id          # add task_id assigned from remote

        self._add_task_to_local(task)    # update task_list in local

        return f"Task[{task_id}] added successfully!"


    # delete task
    def _delete_task_from_local(self, task_id):
        self.task_list = [t for t in self.task_list if t.task_id != task_id]

    def delete_task(self, task_id):
        notion.delete_task_from_remote(task_id)
        self._delete_task_from_local(task_id)

        return f"Task[{task_id}] deleted successfully!"


    # edit task
    def _edit_task_from_local(self, task_id, task):
        for t in self.task_list:
            if t.task_id == task_id:
                t.name = task.name
                t.date = task.date
                t.group = task.group
                break

    def edit_task(self, task_id, task):
        notion.edit_task_from_remote(task_id, task)
        self._edit_task_from_local(task_id, task)

        return f"Task[{task_id}] updated successfully!"


    # get task
    def get_task_id_by_name(self, name):
        for t in self.task_list:
            if t.name == name:
                return t.task_id
            
        return None


class ConfirmablePlanner(Planner):
    def __init__(self):
        super().__init__()

    def confirm(self, action_name, action_info):
        print(f"Action[{action_name}] has been requested.")
        print(f"Action info: \n{action_info}")

        confirmation = input(f"Do you confirm this? (yes/no): ").strip().lower()
        if confirmation == 'yes' or confirmation == 'y':
            return True
        else:
            return False
        
    def add_task(self, task):
        action_info = f"Task Name: {task.name}, Date: {task.date}, Group: {task.group}"
        if self.confirm("Add Task", action_info):
            return super().add_task(task)
        return "Task addition cancelled by user."
    
    def delete_task(self, task_id):
        action_info = f"Task ID: {task_id}"
        if self.confirm("Delete Task", action_info):
            return super().delete_task(task_id)
        return "Task deletion cancelled by user."
    
    def edit_task(self, task_id, task):
        action_info = f"Task ID: {task_id}, New Name: {task.name}, New Date: {task.date}, New Group: {task.group}"
        if self.confirm("Edit Task", action_info):
            return super().edit_task(task_id, task)
        return "Task edit cancelled by user."
