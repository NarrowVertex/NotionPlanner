import shlex
from requests.exceptions import HTTPError

from command import CommandHandler
from command import register_commands


class CommandManager:
    def __init__(self):
        self.command_handler = CommandHandler()

        self.handler_map = {}

        self._register()

    # 필요한 커맨드 등록
    # 등록은 CommandRegistry에서
    def _register(self):
        # Register command handlers here
        command_list = register_commands(self.command_handler)
        for command in command_list:
            self.handler_map[command.opcode] = command.handle
            print(f"Registered command: {command.opcode}")
    
    # 외부에서 커맨드 실행 요청 시 사용
    # 커맨드 실행 시 CommandHandler의 execute 메소드 호출
    # 커맨드 실행 후 결과값을 리턴
    def execute_command(self, command: str):
        # Decode the command if needed
        opcode, operands = self._decode(command)

        if opcode is None:
            print("Invalid command format.")
            return
        
        # Execute the command
        response = self._execute(opcode, operands)
        return response
    
    # 커맨드 디코딩
    # 커맨드의 opcode와 operand를 분리
    # 커맨드의 opcode는 '/'로 시작
    def _decode(self, command:str):
        # Split command by spaces
        parts = shlex.split(command)
        
        # Check if the command is empty or not
        if not parts:
            return None, None
        
        # Check if the first part starts with '/'
        if not parts[0].startswith('/'):
            return None, None

        # First part is opcode, rest are args
        opcode = parts[0].lstrip('/')
        operands = parts[1:] if len(parts) > 1 else []
        
        return opcode, operands
    
    # 커맨드 실행
    # opcode에 해당하는 핸들러가 존재하면 핸들러의 execute 메소드 호출
    def _execute(self, opcode, operands):
        if opcode in self.handler_map:
            try:
                response = self.handler_map[opcode](operands)
            except HTTPError as e:      # HTTPError from requests in notion_api.py
                # Handle HTTP errors
                response = f"Error executing command '/{opcode}'\n{str(e)}"
            
            return response
        else:
            return f"Command {opcode} not recognized."