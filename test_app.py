import asyncio
from functools import partial
import json
import pandas as pd
import sys


from aiconfig.eval.api import (
    run_test_suite_with_inputs,
    TestSuiteWithInputsSettings,
)

from aiconfig.eval.api import metrics, common
import pytest

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)


async def _correct_fn(datum: str, expected: str) -> bool:
    output_loaded = json.loads(datum)["value"][0]["function"]
    output_loaded["arguments"] = json.loads(output_loaded["arguments"])

    # Round trip to normalize whitespace and order
    output_loaded_normalized = json.dumps(output_loaded, sort_keys=True)

    expected["arguments"] = json.loads(expected["arguments"])
    expected_normalized = json.dumps(expected, sort_keys=True)
    return output_loaded_normalized == expected_normalized


def correct_function(expected: str):
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
    test_pairs = [
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
        df_result.query("metric_name=='correct_function'").value.fillna(False).mean()
    )

    is_acceptable_accuracy = accuracy > 0.9

    print(
        "Result dataframe:\n",
        df_result.set_index(["input", "aiconfig_output", "metric_name"]).value.unstack(
            "metric_name"
        ),
    )

    print(f"Correct function accuracy: {accuracy}")

    assert is_acceptable_accuracy, f"Low accuracy: {accuracy}"
