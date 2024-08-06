from typing import Callable

from PyQt6.QtCore import QObject, pyqtSignal

from controller.commands.command import Command
from controller.error_handler import ErrorHandler


class CommandHandler(QObject):
    undo_stack_edited = pyqtSignal(int)
    redo_stack_edited = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.undo_cmds = []
        self.redo_cmds = []
        self.error_handler = ErrorHandler()

    def execute(self, cmd: Command):
        self.redo_cmds.clear()
        self.redo_stack_edited.emit(0)

        success_message = "Command executed."
        temp = cmd.redo()
        if temp:
            success_message = temp
        self.undo_cmds.append(cmd)
        self.undo_stack_edited.emit(len(self.undo_cmds))

        return success_message

    def undo_latest(self) -> str | None:
        if not self.undo_cmds:
            return

        cmd: Command = self.undo_cmds.pop()
        self.undo_stack_edited.emit(len(self.undo_cmds))
        success_message = self.safe_execute(lambda: cmd.undo())
        self.redo_cmds.append(cmd)
        self.redo_stack_edited.emit(len(self.redo_cmds))

        return success_message

    def redo_latest(self) -> str | None:
        if not self.redo_cmds:
            return

        cmd: Command = self.redo_cmds.pop()
        self.redo_stack_edited.emit(len(self.redo_cmds))
        success_message = self.safe_execute(lambda: cmd.redo())
        self.undo_cmds.append(cmd)
        self.undo_stack_edited.emit(len(self.undo_cmds))

        return success_message

    def safe_execute(self, callable: Callable) -> str | None:
        try:
            msg = callable()
            return msg
        except Exception as e:
            self.error_handler.handle_error(e)
