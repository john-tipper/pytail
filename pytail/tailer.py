import asyncio


class FileTailer:
    the_file: str
    _do_stop = False

    def __init__(self, file_name: str):
        self.the_file = file_name

    def stop(self):
        self._do_stop = True

    async def tail(self, start_pos=0, sleep_sec=1):
        """Yield each line from a file as they are written.
        `sleep_sec` is the time to sleep after empty reads."""
        line = ""
        with open(self.the_file, "r") as fp:
            fp.seek(start_pos)
            while not self._do_stop:
                tmp = fp.readline()
                if tmp is not None and tmp != "":
                    line += tmp
                    if line.endswith("\n"):
                        yield fp.tell(), line.strip()
                        line = ""
                elif sleep_sec:
                    await asyncio.sleep(sleep_sec)
