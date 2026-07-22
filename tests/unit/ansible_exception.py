class AnsibleException(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class AnsibleExitJson(AnsibleException):
    pass


class AnsibleFailJson(AnsibleException):
    pass
