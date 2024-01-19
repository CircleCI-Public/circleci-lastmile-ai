import json
from functools import partial
from typing import Any

import pandas as pd
import pytest
from aiconfig import AIConfigRuntime
from aiconfig.eval.api import (
    TestSuiteWithInputsSettings,
    common,
    metrics,
    run_test_suite_with_inputs,
)

from app import generate_response_from_data, get_app_response
from book_db import get, list_by_genre, search

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
            {"arguments": '{\n  "name": "harry potter"\n}', "name": "list"},
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
async def test_generate_correctness_1():
    aiconfig = AIConfigRuntime.load("book_db_function_calling.aiconfig.json")
    response1 = await generate_response_from_data(
        aiconfig,
        "how widely-read is 'To Kill a Mockingbird'?",
        '{"id":"a1","name":"To Kill a Mockingbird","genre":"historical","description":"Compassionate, dramatic, and deeply moving, \\"To Kill A Mockingbird\\" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature."}',
    )
    print(f"{response1=}")
    assert "18 million" in response1.lower()


@pytest.mark.asyncio
async def test_generate_correctness_2():
    aiconfig = AIConfigRuntime.load("book_db_function_calling.aiconfig.json")
    response2 = await generate_response_from_data(
        aiconfig,
        "whats in our historical collection?",
        '{"id":"a1","name":"To Kill a Mockingbird","genre":"historical","description":"Compassionate, dramatic, and deeply moving, \\"To Kill A Mockingbird\\" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature."}\n{"id":"a2","name":"All the Light We Cannot See","genre":"historical","description":"In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister, enchanted by a crude radio they find that brings them news and stories from places they have never seen or imagined. Werner becomes an expert at building and fixing these crucial new instruments and is enlisted to use his talent to track down the resistance. Deftly interweaving the lives of Marie-Laure and Werner, Doerr illuminates the ways, against all odds, people try to be good to one another."}\n{"id":"a3","name":"Where the Crawdads Sing","genre":"historical","description":"For years, rumors of the “Marsh Girl” haunted Barkley Cove, a quiet fishing village. Kya Clark is barefoot and wild; unfit for polite society. So in late 1969, when the popular Chase Andrews is found dead, locals immediately suspect her.\\n\\nBut Kya is not what they say. A born naturalist with just one day of school, she takes life\'s lessons from the land, learning the real ways of the world from the dishonest signals of fireflies. But while she has the skills to live in solitude forever, the time comes when she yearns to be touched and loved. Drawn to two young men from town, who are each intrigued by her wild beauty, Kya opens herself to a new and startling world—until the unthinkable happens."}',
    )
    for historical_book_name in [
        "All the Light We Cannot See",
        "To Kill a Mockingbird",
        "Where the Crawdads Sing",
    ]:
        assert historical_book_name in response2


@pytest.mark.asyncio
async def test_e2e_correctness_1():
    response1 = await get_app_response("how widely-read is 'To Kill a Mockingbird'?")
    print(f"{response1=}")
    assert "18 million" in response1.lower()


@pytest.mark.asyncio
async def test_e2e_correctness_2():
    # This corresponds to what we expect for upstream input "whats in our historical collection?"
    response2 = await get_app_response("whats in our historical collection?")
    for historical_book_name in [
        "All the Light We Cannot See",
        "To Kill a Mockingbird",
        "Where the Crawdads Sing",
    ]:
        assert historical_book_name in response2
