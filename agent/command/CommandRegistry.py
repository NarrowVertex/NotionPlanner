from commands.Command import CommandTaskAdd

def register():
    command_list = []
    command_list.append(CommandTaskAdd())

    return command_list