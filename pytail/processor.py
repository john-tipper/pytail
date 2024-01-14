from abc import ABC, abstractmethod


class LogProcessor(ABC):
    @abstractmethod
    def process_line(self, line: str):
        pass


class PrintLogProcessor(LogProcessor):
    def process_line(self, line: str):
        print(line)
