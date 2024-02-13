import json
import traceback
from typing import Any

import pandas as pd
import pytest
from aiconfig.eval.api import (
    TestSuiteWithInputsSettings,
    metrics,
    run_test_suite_with_inputs,
)

from app import get_app_response
from book_db import get, list_by_genre, search

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)

JSON = dict[str, Any]


@metrics.metric(
    description="1 (pass) if function call is correct, else 0",
    best_value=1,
    worst_value=0,
)
def is_correct_function(datum: str, expected: JSON) -> int:
    print(f"{datum=}", f"{expected=}")
    try:
        output_loaded = json.loads(datum)["value"][0]["function"]
        output_loaded["arguments"] = json.loads(output_loaded["arguments"])

        # Round trip to normalize whitespace and order
        output_loaded_normalized = json.dumps(output_loaded, sort_keys=True)

        expected["arguments"] = json.loads(expected["arguments"])
        expected_normalized = json.dumps(expected, sort_keys=True)
        return int(output_loaded_normalized == expected_normalized)
    except Exception:
        print("Exception:", traceback.format_exc())
        return 0


@metrics.metric(
    description="Portion of expected book names in the string",
    best_value=1.0,
    worst_value=0.0,
)
def book_recall(datum: str, expected: list[str]) -> float:
    present = len([book for book in expected if book in datum])
    return 1.0 * present / len(expected)


@pytest.mark.asyncio
async def test_function_accuracy():
    test_pairs: list[tuple[dict[str, str], JSON]] = [
        (
            {"user_query": "ID isbn123"},
            #
            {"arguments": '{\n  "id": "isbn123"\n}', "name": "get"},
        ),
        (
            {"user_query": "To kill a mockingbird"},
            #
            {"arguments": '{\n  "name": "To kill a mockingbird"\n}', "name": "search"},
        ),
        (
            {
                "user_query": "I really like Agatha Christie. I wonder what else we have like her."
            },
            {"arguments": '{\n  "genre": "mystery"\n}', "name": "list"},
        ),
    ]
    test_suite = [
        (input, is_correct_function(expected)) for input, expected in test_pairs
    ]
    ts_settings = TestSuiteWithInputsSettings(
        prompt_name="user_query_to_function_call",
        aiconfig_path="./book_db_function_calling.aiconfig.json",
    )

    df_result = await run_test_suite_with_inputs(
        test_suite=test_suite,
        settings=ts_settings,
    )

    thresholds = {
        "is_correct_function": 0.9,
    }
    means = df_result.groupby("metric_name").value.mean().to_dict()  # type: ignore[pandas]

    for metric_name, mean in means.items():
        assert mean > thresholds[metric_name], f"Low {metric_name} accuracy: {mean}"

    print(f"Correct function accuracy: {means['is_correct_function']}")


def test_book_db_api():
    query_result_1 = search("harry potter")
    assert query_result_1 == []

    query_result_2 = get("a2")
    assert query_result_2 is not None
    assert query_result_2.name == "All the Light We Cannot See"

    query_result_3 = [book.name for book in list_by_genre("dystopian")]

    assert query_result_3 == ["1984"]


@pytest.mark.asyncio
async def test_threshold_reasoning_string_match():
    test_suite = [
        (
            {
                "user_query": "how widely-read is 'To Kill a Mockingbird'?",
                "function_output_as_text": '{"id":"a1","name":"To Kill a Mockingbird","genre":"historical","description":"Compassionate, dramatic, and deeply moving, \\"To Kill A Mockingbird\\" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature."}',
            },
            metrics.substring_match("18 million", case_sensitive=False),
        ),
        (
            {
                "user_query": "in 'All the Light We Cannot See', how many living people are most likely in the werner's family?",
                "function_output_as_text": '{"id":"a2","name":"All the Light We Cannot See","genre":"historical","description":"In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister, enchanted by a crude radio they find that brings them news and stories from places they have never seen or imagined. Werner becomes an expert at building and fixing these crucial new instruments and is enlisted to use his talent to track down the resistance. Deftly interweaving the lives of Marie-Laure and Werner, Doerr illuminates the ways, against all odds, people try to be good to one another."}',
            },
            metrics.substring_match("2"),
        ),
    ]
    ts_settings = TestSuiteWithInputsSettings(
        prompt_name="function_output_to_text_response",
        aiconfig_path="./book_db_function_calling.aiconfig.json",
    )

    df_result = await run_test_suite_with_inputs(
        test_suite=test_suite,
        settings=ts_settings,
    )

    thresholds = {
        "substring_match": 0.40,
    }
    means = df_result.groupby("metric_name").value.mean().to_dict()  # type: ignore[pandas]

    for metric_name, mean in means.items():
        assert mean > thresholds[metric_name], f"Low {metric_name} accuracy: {mean}"

    print(f"substring match accuracy: {means['substring_match']}")


@pytest.mark.asyncio
async def test_threshold_book_recall():
    test_pairs = [
        (
            {
                "user_query": "whats in our historical collection?",
                "function_output_as_text": '{"id":"a1","name":"To Kill a Mockingbird","genre":"historical","description":"Compassionate, dramatic, and deeply moving, \\"To Kill A Mockingbird\\" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature."}\n{"id":"a2","name":"All the Light We Cannot See","genre":"historical","description":"In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister, enchanted by a crude radio they find that brings them news and stories from places they have never seen or imagined. Werner becomes an expert at building and fixing these crucial new instruments and is enlisted to use his talent to track down the resistance. Deftly interweaving the lives of Marie-Laure and Werner, Doerr illuminates the ways, against all odds, people try to be good to one another."}\n{"id":"a3","name":"Where the Crawdads Sing","genre":"historical","description":"For years, rumors of the “Marsh Girl” haunted Barkley Cove, a quiet fishing village. Kya Clark is barefoot and wild; unfit for polite society. So in late 1969, when the popular Chase Andrews is found dead, locals immediately suspect her.\\n\\nBut Kya is not what they say. A born naturalist with just one day of school, she takes life\'s lessons from the land, learning the real ways of the world from the dishonest signals of fireflies. But while she has the skills to live in solitude forever, the time comes when she yearns to be touched and loved. Drawn to two young men from town, who are each intrigued by her wild beauty, Kya opens herself to a new and startling world—until the unthinkable happens."}',
            },
            [
                "All the Light We Cannot See",
                "To Kill a Mockingbird",
                "Where the Crawdads Sing",
            ],
        ),
        (
            {
                "user_query": "list history, book names. Only southern americana. Exclude all other tokens.",
                "function_output_as_text": '{"id":"a1","name":"To Kill a Mockingbird","genre":"historical","description":"Compassionate, dramatic, and deeply moving, \\"To Kill A Mockingbird\\" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature."}\n{"id":"a2","name":"All the Light We Cannot See","genre":"historical","description":"In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister, enchanted by a crude radio they find that brings them news and stories from places they have never seen or imagined. Werner becomes an expert at building and fixing these crucial new instruments and is enlisted to use his talent to track down the resistance. Deftly interweaving the lives of Marie-Laure and Werner, Doerr illuminates the ways, against all odds, people try to be good to one another."}\n{"id":"a3","name":"Where the Crawdads Sing","genre":"historical","description":"For years, rumors of the “Marsh Girl” haunted Barkley Cove, a quiet fishing village. Kya Clark is barefoot and wild; unfit for polite society. So in late 1969, when the popular Chase Andrews is found dead, locals immediately suspect her.\\n\\nBut Kya is not what they say. A born naturalist with just one day of school, she takes life\'s lessons from the land, learning the real ways of the world from the dishonest signals of fireflies. But while she has the skills to live in solitude forever, the time comes when she yearns to be touched and loved. Drawn to two young men from town, who are each intrigued by her wild beauty, Kya opens herself to a new and startling world—until the unthinkable happens."}',
            },
            [
                "To Kill a Mockingbird",
                "Where the Crawdads Sing",
            ],
        ),
    ]
    test_suite = [(input, book_recall(expected)) for input, expected in test_pairs]
    ts_settings = TestSuiteWithInputsSettings(
        prompt_name="function_output_to_text_response",
        aiconfig_path="./book_db_function_calling.aiconfig.json",
    )

    df_result = await run_test_suite_with_inputs(
        test_suite=test_suite,
        settings=ts_settings,
    )

    thresholds = {
        "book_recall": 0.75,
    }
    means = df_result.groupby("metric_name").value.mean().to_dict()  # type: ignore[pandas]

    for metric_name, mean in means.items():
        assert mean > thresholds[metric_name], f"Low {metric_name}: {mean}"

    print(f"Mean book recall: {means['book_recall']}")


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
