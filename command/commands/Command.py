from abc import ABC, abstractmethod
from command import CommandHandler
from notion import Task


def register_commands(handler: CommandHandler):
    command_list = []
    command_list.append(CommandTaskAdd(handler))

    return command_list


class Command(ABC):
    def __init__(self, handler: CommandHandler, opcode):
        self.handler = handler
        self.opcode = opcode

    def check_opcode(self, opcode):
        return self.opcode == opcode

    @abstractmethod
    def handle(self, operands) -> str:
        pass


class CommandTaskAdd(Command):
    def __init__(self, handler):
        super().__init__(handler, "add")

    def handle(self, operands):
        if len(operands) == 3 or len(operands) == 4:
            task = None
            task_name = operands[0]
            if len(operands) == 3:
                task_date = operands[1]
                task_group = operands[2]
            elif len(operands) == 4:
                task_date_start = operands[1]
                task_date_end = operands[2]
                task_date = {'start': task_date_start, 'end': task_date_end}
                task_group = operands[3]
            task = Task(None, task_name, task_date, task_group)

            return self.handler.handle_task_add(task)
        else:
            return "Invalid number of arguments for task addition."
