from command import CommandManager


def main():
    command_manager = CommandManager()

    while True:
        command = input("Enter command: ")
        if command.lower() == 'exit':
            break

        response = command_manager.execute_command(command)
        if response:
            print(response)
