from app.application.use_cases.get_version import GetVersionUseCase


def test_get_version_returns_injected_version() -> None:
    use_case = GetVersionUseCase(version="1.2.3")

    assert use_case.execute() == "1.2.3"
