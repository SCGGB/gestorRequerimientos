class GetVersionUseCase:
    def __init__(self, version: str) -> None:
        self._version = version

    def execute(self) -> str:
        return self._version
