import asyncio
import re
import sys
from typing import Dict

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer

from pytail.processor import LogProcessor, PrintLogProcessor
from pytail.tailer import FileTailer

import signal


class LogFileWatcher(RegexMatchingEventHandler):
    tailer_by_watched_files: Dict[str, FileTailer] = dict()
    processor_by_regex = dict()
    loop = None
    _stop = False

    def __init__(self, matchers: [(str, LogProcessor)]):
        super().__init__(
            regexes=[re_handler[0] for re_handler in matchers], ignore_directories=True
        )
        self.processor_by_regex = {re.compile(r): h for (r, h) in matchers}
        signal.signal(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self, num, frame):
        self._stop = True

    async def tail(self, tailer, processor: LogProcessor):
        async for pos, line in tailer.tail():
            processor.process_line(line)

    def maybe_create_processor(self, file_path: str):
        if file_path not in self.tailer_by_watched_files:
            # find first regex that matches this path, that gives the processor to direct changes towards
            processor = next(
                filter(
                    lambda r_v: r_v[0].match(file_path), self.processor_by_regex.items()
                )
            )[1]
            tailer = FileTailer(file_path)
            self.tailer_by_watched_files[file_path] = tailer
            # start tailing file
            asyncio.ensure_future(self.tail(tailer, processor), loop=self.loop)

    def on_created(self, event):
        self.maybe_create_processor(event.src_path)

    def on_deleted(self, event):
        if event.src_path in self.tailer_by_watched_files:
            tailer_to_stop = self.tailer_by_watched_files[event.src_path]
            tailer_to_stop.stop()
            del self.tailer_by_watched_files[event.src_path]

    def on_modified(self, event):
        self.maybe_create_processor(event.src_path)

    async def _start_watcher(self):
        observer = Observer()
        observer.schedule(self, path, recursive=True)
        observer.start()
        try:
            while observer.is_alive() and not self._stop:
                await asyncio.sleep(1)
        finally:
            observer.stop()
            observer.join()

    async def _watch(self):
        self.loop = asyncio.get_running_loop()
        await self._start_watcher()

    def watch(self):
        asyncio.run(self._watch())


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    watcher = LogFileWatcher(matchers=[(r".*txt", PrintLogProcessor())])
    watcher.watch()
