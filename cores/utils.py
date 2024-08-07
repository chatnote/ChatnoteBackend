import time

from langchain.callbacks import get_openai_callback


def print_execution_time(func):
    def wrapper(*args, **kwargs):
        s = time.perf_counter()
        res = func(*args, **kwargs)
        elapsed = time.perf_counter() - s
        print("\033[1m" + f"{func.__name__} Concurrent executed in {elapsed:0.2f} seconds." + "\033[0m")
        return res

    return wrapper


def print_token_summary(func):
    def wrapper(*args, **kwargs):
        with get_openai_callback() as cb:
            res = func(*args, **kwargs)
            print(f"Token summary: {func.__name__}\n{cb}")
        return res
    return wrapper


def get_host_url(request):
    scheme = request.scheme
    host_url = request.get_host()

    return f"{scheme}://{host_url}"


def split_list_and_run(overall_list: list, split_num: int, func, *args):
    overall_split_list = []
    for i in range(0, len(overall_list), split_num):
        split_list = overall_list[i:i + split_num]
        overall_split_list.append(split_list)

    for split_list in overall_split_list:
        if split_list:
            func(split_list, *args)
