from functools import wraps


def ignore_raw(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        if kwargs.get("raw"):
            # skip if triggered by loaddata
            return
        return fn(*args, **kwargs)

    return decorated
