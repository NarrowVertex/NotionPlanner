from notion import Planner


class CommandHandler:
    def __init__(self):
        self.planner = Planner()

    def handle_task_show(self):
        return self.planner.show_tasks()

    def handle_task_add(self, task):
        return self.planner.add_task(task)

    def handle_task_delete(self, task_id):
        return self.planner.delete_task(task_id)

    def handle_task_edit(self, task_id, new_task):
        return self.planner.edit_task(task_id, new_task)
    