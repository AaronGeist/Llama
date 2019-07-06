from concurrent import futures
from concurrent.futures import ThreadPoolExecutor


class ParallelTemplate:
    def __init__(self, workers=5):
        super().__init__()
        self.workers = workers

    def run(self, func, inputs, is_async=False):
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_items = {executor.submit(func, item): item for item in inputs}
            if is_async:
                print("finish")
                return

            results = list()
            for future in futures.as_completed(future_items):
                try:
                    item = future.result()
                    results.append(item)
                except Exception as exc:
                    print("exception: " + str(exc))
            return results
