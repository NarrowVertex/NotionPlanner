import notion


class Planner:
    def __init__(self):
        self.task_list = []

    def load_tasks(self):
        self.task_list = notion.get_tasks()


    # add task
    def _add_task_to_local(self, task):
        self.task_list.append(task)

    def add_task(self, task):
        task_id = notion.add_task_to_remote(task)
        task.task_id = task_id          # add task_id assigned from remote

        self._add_task_to_local(task)    # update task_list in local


    # delete task
    def _delete_task_from_local(self, task_id):
        task_list = [t for t in task_list if t.task_id != task_id]

    def delete_task(self, task_id):
        notion.delete_task_from_remote(task_id)
        self._delete_task_from_local(task_id)


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


    # get task
    def get_task_id_by_name(self, name):
        for t in self.task_list:
            if t.name == name:
                return t.task_id
            
        return None
