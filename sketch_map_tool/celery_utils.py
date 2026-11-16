from typing import Any, assert_never

from billiard.exceptions import TimeLimitExceeded
from celery.result import AsyncResult, GroupResult

from sketch_map_tool import celery_app
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import (
    TimeLimitExceededError,
    TranslatableError,
    UUIDNotFoundError,
)
from sketch_map_tool.helpers import N_


def extract_errors(
    async_result: AsyncResult | GroupResult,
    type_,
) -> list[str]:
    """Extract known/custom exceptions propagated by a Celery task or group.

    raises: Re-raises exception if error is not a custom exception.
    """
    if isinstance(async_result, AsyncResult):
        results = [async_result]
    elif isinstance(async_result, GroupResult):
        results = async_result.results
    else:
        assert_never()
    errors = []
    for r in results:  # type: ignore
        if r.ready():
            try:
                r.get(propagate=True)
            except TranslatableError as error:
                errors.append(error.translate())
            except TimeLimitExceeded as error:
                try:
                    raise TimeLimitExceededError(
                        N_(
                            "We couldn’t process your submission because it took too "
                            "long. Please try again later. If the problem persists, "
                            "reach out to us: sketch-map-tool@heigit.org"
                        )
                    ) from error
                except TimeLimitExceededError as error_:
                    errors.append(error_.translate())
    return errors


def get_async_result(uuid: str, type_: REQUEST_TYPES) -> AsyncResult | GroupResult:
    """Get Celery `AsyncResult` or restore `GroupResult` for given Celery UUID."""
    if type_ == "sketch-map":
        async_result = celery_app.AsyncResult(uuid)
    elif type_ in ("vector-results", "raster-results"):
        async_result = celery_app.GroupResult.restore(uuid)
    else:
        raise TypeError()

    if async_result is None:
        raise UUIDNotFoundError(
            N_("There are no tasks for UUID {UUID}"),
            {"UUID": uuid},
        )
    else:
        return async_result


def is_error(r: Any) -> bool:
    return isinstance(r, BaseException)


def get_result(async_result: AsyncResult | GroupResult, type_: REQUEST_TYPES) -> Any:
    if isinstance(async_result, AsyncResult):
        return async_result.get(propagate=True)

    results = async_result.get(propagate=False)

    match type_:
        case "raster-results":
            return [r[:-2] for r in results if not is_error(r)]
        case "vector-results":
            return [r[-2] for r in results if not is_error(r)]
