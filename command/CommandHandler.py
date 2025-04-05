from notion import Planner


class CommandHandler:
    def __init__(self):
        self.planner = Planner()

    # all
    def handle_task_show(self):
        return self.planner.show_tasks()

    def handle_task_add(self, task):
        return self.planner.add_task(task)

    def handle_task_delete(self, task_id):
        return self.planner.delete_task(task_id)

    def handle_task_edit(self, task_id, new_task):
        return self.planner.edit_task(task_id, new_task)
    
    # user-only
    def handle_show_command_spec(self, command_opcode):
        import json
        from command import CommandManager
        command_manager = CommandManager()
        command_spec = command_manager.command_spec_map[command_opcode]
        # Convert to dict and format with indentation
        formatted_spec = json.dumps(command_spec, indent=2)
        return formatted_spec
    