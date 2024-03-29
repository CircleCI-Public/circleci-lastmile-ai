import asyncio
import sys
from typing import List

from aiconfig import AIConfigRuntime
from aiconfig.callback import CallbackManager

from book_db import Book, call_function
from logger import get_logger

from dotenv import load_dotenv

load_dotenv()

LOGGER = get_logger()


async def main(argv: list[str]) -> int:
    try:
        user_query = argv[1]
        text_response = await get_app_response(user_query)
        print("\n\nResponse:\n\n==========\n\n")
        print(text_response)
        print("\n\n==========\n\n")
        return 0
    except IndexError:
        LOGGER.error("Error: Please provide a query as a command line argument")
        return 1
    except Exception as e:
        LOGGER.error(f"Error: {e}")
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

    LOGGER.info(
        f"Calling second AIConfig prompt with params:\n\n{params_for_get_text_response}"
    )
    return await aiconfig.run_and_get_output_text(
        "function_output_to_text_response", params_for_get_text_response
    )


async def get_app_response(user_query: str) -> str:
    LOGGER.debug(f"User query:\n{user_query}")
    aiconfig = AIConfigRuntime.load("book_db_function_calling.aiconfig.json")
    _configure_aiconfig_callbacks(aiconfig)
    user_input_params = dict(user_query=user_query)

    LOGGER.info(f"Calling first AIConfig prompt with params:\n\n{user_input_params}")
    run_output = await aiconfig.run("user_query_to_function_call", user_input_params)
    LOGGER.info(f"First prompt output:\n\n{run_output}")
    tool_call_data = run_output[0].data.value
    LOGGER.debug(f"\nTool call data:\n\n{tool_call_data}")
    function_call_response = tool_call_data[0].function

    name, args = function_call_response.name, function_call_response.arguments

    LOGGER.info(f"Got function name:\n\n{name}")
    LOGGER.info(f"Function args:\n\n{args}")
    function_output = call_function(name, args)
    LOGGER.info(f"Called function. Function output:\n\n{function_output}")

    serialized_book_data = _serialize_book_data_to_text(function_output)
    return await generate_response_from_data(aiconfig, user_query, serialized_book_data)


def _configure_aiconfig_callbacks(aiconfig: AIConfigRuntime) -> None:
    """
    Set the AIConfig callback manager to write all
    event debug information to aiconfig.log.
    """

    async def _logging_callback(event):
        with open("aiconfig.log", "a") as f:
            f.write(f"{event}\n")

    # Initialize your AIConfig CallbackManager with callbacks
    # you want to run on every event (on_run_start, on_run_complete, etc.)
    aiconfig.callback_manager = CallbackManager([_logging_callback])


if __name__ == "__main__":
    retcode: int = asyncio.run(main(sys.argv))
    sys.exit(retcode)
