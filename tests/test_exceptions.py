from medkit.exceptions import (
    APIError,
    CircuitOpenError,
    ConfigurationError,
    MedKitError,
    TimeoutError,
)


def test_exception_hierarchy():
    assert issubclass(APIError, MedKitError)
    assert issubclass(TimeoutError, MedKitError)
    assert issubclass(ConfigurationError, MedKitError)
    assert issubclass(CircuitOpenError, MedKitError)


def test_api_error_context():
    err = APIError(
        "Something went wrong",
        status_code=500,
        response_body="Internal Error",
        provider="openfda",
        request_id="123",
    )
    assert err.status_code == 500
    assert err.response_body == "Internal Error"
    assert err.provider == "openfda"
    assert err.request_id == "123"
    assert str(err) == "Something went wrong"
