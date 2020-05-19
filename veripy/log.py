from functools import wraps

def log(msg=''):
    def decorate(func):
        @wraps(func)
        def caller(*args, **kwargs):
            print(f'Entering: {func.__name__}', msg)
            return func(*args, **kwargs)
        return caller
    return decorate