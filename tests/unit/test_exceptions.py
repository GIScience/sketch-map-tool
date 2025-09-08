import flask_babel
import pytest
from approvaltests import verify

from sketch_map_tool.exceptions import ValidationError
from sketch_map_tool.routes import app
from tests.namer import PytestNamer


@pytest.mark.parametrize(
    "lang",
    ["de", "en"],
)
def test_validation_error(lang):
    flask_babel.Babel(app)
    with app.test_request_context():
        with flask_babel.force_locale(lang):
            with pytest.raises(ValidationError) as error:
                raise ValidationError(
                    (
                        "{TYPE} is not a valid value for the request parameter 'type'. "
                        "Allowed values are: {REQUEST_TYPES}"
                    ),
                    {"TYPE": "foo", "REQUEST_TYPES": "bar"},
                )
            verify(error.value.translate(), namer=PytestNamer())
