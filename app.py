import asyncio
import json
import sys
from typing import List

from aiconfig import AIConfigRuntime
from pydantic import BaseModel


class Book(BaseModel):
    id: str
    name: str
    genre: str
    description: str


BOOKS_DB: List[Book] = [
    Book(
        id="a1",
        name="To Kill a Mockingbird",
        genre="historical",
        description='Compassionate, dramatic, and deeply moving, "To Kill A Mockingbird" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature.',
    ),
    Book(
        id="a2",
        name="All the Light We Cannot See",
        genre="historical",
        description="In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister, enchanted by a crude radio they find that brings them news and stories from places they have never seen or imagined. Werner becomes an expert at building and fixing these crucial new instruments and is enlisted to use his talent to track down the resistance. Deftly interweaving the lives of Marie-Laure and Werner, Doerr illuminates the ways, against all odds, people try to be good to one another.",
    ),
    Book(
        id="a3",
        name="Where the Crawdads Sing",
        genre="historical",
        description="For years, rumors of the “Marsh Girl” haunted Barkley Cove, a quiet fishing village. Kya Clark is barefoot and wild; unfit for polite society. So in late 1969, when the popular Chase Andrews is found dead, locals immediately suspect her.\n\nBut Kya is not what they say. A born naturalist with just one day of school, she takes life's lessons from the land, learning the real ways of the world from the dishonest signals of fireflies. But while she has the skills to live in solitude forever, the time comes when she yearns to be touched and loved. Drawn to two young men from town, who are each intrigued by her wild beauty, Kya opens herself to a new and startling world—until the unthinkable happens.",
    ),
    Book(
        id="a4",
        name="1984",
        genre="dystopian",
        description="Among the seminal texts of the 20th century, Nineteen Eighty-Four is a rare work that grows more haunting as its futuristic purgatory becomes more real. Published in 1949, the book offers political satirist George Orwell's nightmarish vision of a totalitarian, bureaucratic world and one poor stiff's attempt to find individuality. The brilliance of the novel is Orwell's prescience of modern life—the ubiquity of television, the distortion of the language—and his ability to construct such a thorough version of hell.",
    ),
]


def list_by_genre(genre: str) -> List[Book]:
    return [book for book in BOOKS_DB if book.genre == genre]


def search(name: str) -> List[Book]:
    return [book for book in BOOKS_DB if book.name == name]


def get(id: str) -> Book | None:
    for book in BOOKS_DB:
        if book.id == id:
            return book
    return None


def call_function(name: str, args: str) -> Book | None | List[Book]:
    print(f"Calling function {name} with args {args}")
    args_dict = json.loads(args)
    match name:
        case "list":
            return list_by_genre(args_dict["genre"])
        case "search":
            return search(args_dict["name"])
        case "get":
            return get(args_dict["id"])
        case _:
            raise ValueError(f"Unknown function: {name}")


def _serialize_book_data_to_text(book_data: Book | List[Book]) -> str:
    def _serialize_one_book_to_text(book: Book) -> str:
        return book.model_dump_json()

    match book_data:
        case list(books):
            return "\n".join([_serialize_one_book_to_text(book) for book in books])
        case Book():
            return _serialize_one_book_to_text(book_data)


async def main(argv: list[str]) -> int:
    try:
        user_query = sys.argv[1]
        text_response = await _get_app_response(user_query)
        print("\n\nResponse:\n")
        print(text_response)
        return 0
    except IndexError:
        print("Error: Please provide a query as a command line argument")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


async def _get_app_response(user_query: str) -> str:
    print(f"User query: {user_query}")
    aiconfig = AIConfigRuntime.load("book_db_function_calling.aiconfig.json")
    user_input_params = dict(the_query=user_query)
    function_call_response = (
        (await aiconfig.run("user_query_to_function_call", user_input_params))[0]
        .data.value[0]
        .function
    )
    print(
        f"Function call response: {function_call_response}, type: {type(function_call_response)}"
    )
    function_output = call_function(
        function_call_response.name, function_call_response.arguments
    )
    print(f"Function output: {function_output}")

    function_output_as_text = _serialize_book_data_to_text(function_output)
    qa_input = f"Question: {user_query}\n\nData: {function_output_as_text}\n\n"
    # print(f"Function output as text: {function_output_as_text}")
    function_output_params = dict(qa_input=qa_input)
    return await aiconfig.run_and_get_output_text(
        "function_output_to_text_response", function_output_params
    )


if __name__ == "__main__":
    retcode: int = asyncio.run(main(sys.argv))
    sys.exit(retcode)
