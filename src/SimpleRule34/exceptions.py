class RequestMoreThanAvailableException(Exception):
    def __init__(self, msg, r_c, a_c):
        self.msg = msg
        self.args = (r_c, a_c)

    def __str__(self):
        return self.msg


class ApiException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
