class InputError(ValueError):
    def __init__(self, code, detail, status=422):
        super().__init__(detail)
        self.code, self.status = code, status
