import {
  AIConfigRuntime,
  ExecuteResult,
  OutputDataWithToolCallsValue,
} from "aiconfig";
import { Chat } from "openai/resources";

const BOOKS_DB = [
  {
    id: "a1",
    name: "To Kill a Mockingbird",
    genre: "historical",
    description:
      'Compassionate, dramatic, and deeply moving, "To Kill A Mockingbird" takes readers to the roots of human behavior - to innocence and experience, kindness and cruelty, love and hatred, humor and pathos. Now with over 18 million copies in print and translated into forty languages, this regional story by a young Alabama woman claims universal appeal. Harper Lee always considered her book to be a simple love story. Today it is regarded as a masterpiece of American literature.',
  },
  {
    id: "a2",
    name: "All the Light We Cannot See",
    genre: "historical",
    description:
      "In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister, enchanted by a crude radio they find that brings them news and stories from places they have never seen or imagined. Werner becomes an expert at building and fixing these crucial new instruments and is enlisted to use his talent to track down the resistance. Deftly interweaving the lives of Marie-Laure and Werner, Doerr illuminates the ways, against all odds, people try to be good to one another.",
  },
  {
    id: "a3",
    name: "Where the Crawdads Sing",
    genre: "historical",
    description: `For years, rumors of the “Marsh Girl” haunted Barkley Cove, a quiet fishing village. Kya Clark is barefoot and wild; unfit for polite society. So in late 1969, when the popular Chase Andrews is found dead, locals immediately suspect her.\n\n\d
But Kya is not what they say. A born naturalist with just one day of school, she takes life\'s lessons from the land, learning the real ways of the world from the dishonest signals of fireflies. But while she has the skills to live in solitude forever, the time comes when she yearns to be touched and loved. Drawn to two young men from town, who are each intrigued by her wild beauty, Kya opens herself to a new and startling world—until the unthinkable happens.`,
  },
];

// Functions to interact with DB:

// The 'list' function returns a list of books in a specified genre.
function list(genre: string) {
  return BOOKS_DB.filter((book) => book.genre === genre);
}

// The 'search' function returns a list of books that match the provided name.
function search(name: string) {
  return BOOKS_DB.filter((book) => book.name === name);
}

// The 'get' function returns detailed information about a book based on its ID.
// Note: This function accepts only IDs, not names. Use the 'search' function to find a book's ID.
function get(id: string) {
  return BOOKS_DB.find((book) => book.id === id);
}

// Use helper function to executes the function specified by the LLM's output for 'function_call'.
// It handles 'list', 'search', or 'get' functions, and raises an Exception for unknown functions.
function callFunction(functionCall: string, args: string) {
  switch (functionCall) {
    case "list":
      var arg = JSON.parse(args).genre;
      return list(arg);
    case "search":
      var arg = JSON.parse(args).name;
      return search(arg);
    case "get":
      var arg = JSON.parse(args).id;
      return get(arg);
    default:
      throw new Error(`Unknown function: ${functionCall}`);
  }
}

async function main() {
  let user_input = process.argv[2];
  console.log("User input: ", user_input);
  const config = AIConfigRuntime.load("book_db_function_calling.aiconfig.json");

  const params = { the_query: user_input };

  // Run recommend_book prompt with gpt-3.5 and determine right function to call based on user question
  const completion = await config.run("get_book_info", params);

  const output = (
    Array.isArray(completion) ? completion[0] : completion
  ) as ExecuteResult;

  const completionMessage = output.data as OutputDataWithToolCallsValue;
  const functionCall = completionMessage.value[0].function;

  console.log("inferred function call: ", functionCall);

  const value = callFunction(functionCall!.name, functionCall!.arguments);
  console.log("Function call result: ", value);
}

main();
