import time


def execute_time(func):
    def wrapper(*args, **kwargs):
        s = time.perf_counter()
        res = func(*args, **kwargs)
        elapsed = time.perf_counter() - s
        print("\033[1m" + f"{func.__name__} Concurrent executed in {elapsed:0.2f} seconds." + "\033[0m")
        return res

    return wrapper
