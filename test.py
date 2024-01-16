from functools import partial
import json
from typing import Any
import pandas as pd


from aiconfig.eval.api import (
    run_test_suite_with_inputs,
    TestSuiteWithInputsSettings,
)

from aiconfig.eval.api import metrics, common
import pytest

from book_db import get, list_by_genre, search
from app import get_app_response

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)

JSON = dict[str, Any]


async def _correct_fn(datum: str, expected: JSON) -> bool:
    output_loaded = json.loads(datum)["value"][0]["function"]
    output_loaded["arguments"] = json.loads(output_loaded["arguments"])

    # Round trip to normalize whitespace and order
    output_loaded_normalized = json.dumps(output_loaded, sort_keys=True)

    expected["arguments"] = json.loads(expected["arguments"])
    expected_normalized = json.dumps(expected, sort_keys=True)
    return output_loaded_normalized == expected_normalized


def correct_function(expected: JSON):
    return metrics.Metric(
        evaluation_fn=partial(_correct_fn, expected=expected),
        metric_metadata=common.EvaluationMetricMetadata(
            name="correct_function",
            description="True (pass) if function call is correct",
            best_value=True,
            worst_value=False,
            extra_metadata=dict(expected=expected),
        ),
    )


@pytest.mark.asyncio
async def test_function_accuracy():
    test_pairs: list[tuple[str, JSON]] = [
        (
            "ID isbn123",
            #
            {"arguments": '{\n  "id": "isbn123"\n}', "name": "get"},
        ),
        (
            "harry potter",
            #
            {"arguments": '{\n  "name": "harry potter"\n}', "name": "search"},
        ),
        (
            "I really like Agatha Christie. I wonder what else we have like her.",
            {"arguments": '{\n  "genre": "mystery"\n}', "name": "list"},
        ),
    ]
    test_suite = [(input, correct_function(expected)) for input, expected in test_pairs]
    ts_settings = TestSuiteWithInputsSettings(
        prompt_name="user_query_to_function_call",
        aiconfig_path="./book_db_function_calling.aiconfig.json",
    )

    df_result = await run_test_suite_with_inputs(
        test_suite=test_suite,
        settings=ts_settings,
    )

    accuracy = (
        df_result.query("metric_name=='correct_function'").value.fillna(False).mean()  # type: ignore[pandas]
    )

    is_acceptable_accuracy = accuracy > 0.9

    print(
        "Result dataframe:\n",
        df_result.set_index(["input", "aiconfig_output", "metric_name"]).value.unstack(  # type: ignore[pandas]
            "metric_name"
        ),
    )

    print(f"Correct function accuracy: {accuracy}")

    assert is_acceptable_accuracy, f"Low accuracy: {accuracy}"


def test_book_db_api():
    query_result_1 = search("harry potter")
    assert query_result_1 == []

    query_result_2 = get("a2")
    assert query_result_2 is not None
    assert query_result_2.name == "All the Light We Cannot See"

    query_result_3 = [book.name for book in list_by_genre("dystopian")]

    assert query_result_3 == ["1984"]


@pytest.mark.asyncio
async def test_e2e_correctness_1():
    response1 = await get_app_response("how widely-read is 'To Kill a Mockingbird'?")
    print(f"{response1=}")
    assert "18 million" in response1.lower()


@pytest.mark.asyncio
async def test_e2e_correctness_2():
    response2 = await get_app_response("whats in our historical collection?")
    for historical_book_name in [
        "All the Light We Cannot See",
        "To Kill a Mockingbird",
        "Where the Crawdads Sing",
    ]:
        assert historical_book_name in response2
