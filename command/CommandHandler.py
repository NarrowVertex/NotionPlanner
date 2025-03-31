class CommandHandler:
    def __init__(self):
        pass

    def handle_task_show(self):
        return "Showing all tasks."

    def handle_task_add(self, task):
        return f"Task added: {task}"

    def handle_task_delete(self, task_id):
        return f"Task deleted: {task_id}"

    def handle_task_edit(self, task_id, new_task):
        return f"Task edited: {task_id} -> {new_task}"