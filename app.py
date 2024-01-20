import asyncio
import sys
from typing import List

from aiconfig import AIConfigRuntime

from book_db import Book, call_function


async def main(argv: list[str]) -> int:
    try:
        user_query = argv[1]
        text_response = await get_app_response(user_query)
        print("\n\nResponse:\n")
        print(text_response)
        return 0
    except IndexError:
        print("Error: Please provide a query as a command line argument")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def _serialize_book_data_to_text(book_data: Book | List[Book] | None) -> str:
    def _serialize_one_book_to_text(book: Book) -> str:
        return book.model_dump_json()

    match book_data:
        case list(books):
            return "\n".join([_serialize_one_book_to_text(book) for book in books])
        case Book():
            return _serialize_one_book_to_text(book_data)
        case None:
            return "No books found"


async def generate_response_from_data(
    aiconfig: AIConfigRuntime, user_query: str, serialized_book_data: str
) -> str:
    params_for_get_text_response = dict(
        user_query=user_query, function_output_as_text=serialized_book_data
    )

    print("Params for get_text_response:", params_for_get_text_response)
    return await aiconfig.run_and_get_output_text(  # type: ignore[fixme]
        "function_output_to_text_response", params_for_get_text_response
    )


async def get_app_response(user_query: str) -> str:
    print(f"User query: {user_query}")
    aiconfig = AIConfigRuntime.load("book_db_function_calling.aiconfig.json")
    user_input_params = dict(user_query=user_query)

    run_output = await aiconfig.run("user_query_to_function_call", user_input_params)  # type: ignore[union-attr]
    print(f"Run output: {run_output}")
    tool_call_data = run_output[0].data.value  # type: ignore
    print(f"Tool call data: {tool_call_data}")
    function_call_response = tool_call_data[0].function  # type: ignore

    print(
        f"Function call response: {function_call_response}, type: {type(function_call_response)}"
    )

    name, args = function_call_response.name, function_call_response.arguments  # type: ignore
    function_output = call_function(name, args)  # type: ignore
    print(f"Function output: {function_output}")

    serialized_book_data = _serialize_book_data_to_text(function_output)
    return await generate_response_from_data(aiconfig, user_query, serialized_book_data)


if __name__ == "__main__":
    retcode: int = asyncio.run(main(sys.argv))
    sys.exit(retcode)
