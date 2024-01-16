import asyncio
import sys
from typing import List, cast

from aiconfig import AIConfigRuntime
from aiconfig.schema import FunctionCallData

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


async def get_app_response(user_query: str) -> str:
    print(f"User query: {user_query}")
    aiconfig = AIConfigRuntime.load("book_db_function_calling.aiconfig.json")
    user_input_params = dict(the_query=user_query)
    function_call_response: FunctionCallData = cast(
        FunctionCallData,
        (await aiconfig.run("user_query_to_function_call", user_input_params))[0]  # type: ignore[union-attr]
        .data.value[0]
        .function,
    )
    print(
        f"Function call response: {function_call_response}, type: {type(function_call_response)}"
    )
    function_output = call_function(
        function_call_response.name, function_call_response.arguments
    )
    print(f"Function output: {function_output}")

    function_output_as_text = _serialize_book_data_to_text(function_output)
    params_for_get_text_response = dict(
        user_query=user_query, function_output_as_text=function_output_as_text
    )
    print("Params for get_text_response:", params_for_get_text_response)
    return await aiconfig.run_and_get_output_text(  # type: ignore[fixme]
        "function_output_to_text_response", params_for_get_text_response
    )


if __name__ == "__main__":
    retcode: int = asyncio.run(main(sys.argv))
    sys.exit(retcode)
