import pytest

from app import DEFAULT_FORM, create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_form():
    return dict(DEFAULT_FORM)
