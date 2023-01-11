import logging
import time
import inspect
from functools import partial, wraps

from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from api.models import User
import mock

reverse = partial(reverse, args=["v1"])


def for_all_methods(decorator):
    def wrapper(cls):
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("test_"):
                setattr(cls, name, decorator(method))
        return cls

    return wrapper


def log_runtime(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        start = time.time()
        res = fn(*args, **kwargs)
        end = time.time()
        print(f"{fn.__name__} -- {'%.4f' % (end-start)}")
        return res

    return decorated


class APITestCaseMixin:
    client_class = APIClient
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.patcher_celery_task = mock.patch(
            "celery.app.task.Task.delay", return_value=1
        )
        self.patcher_celery_task.start()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        super().tearDown()
        self.patcher_celery_task.stop()
        logging.disable(logging.NOTSET)


class LoggedInMixin:
    auth_user_id = 1

    def setUp(self):
        super().setUp()
        token, _ = Token.objects.get_or_create(user_id=self.auth_user_id)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        self.user = User.objects.get(pk=self.auth_user_id)
        self.profile = self.user.profile
