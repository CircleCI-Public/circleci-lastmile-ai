# circleci-lastmile-ai

## Pre-requisites

- OpenAI API Key
- CircleCI Account

## Quickstart

1. Fork this repository and clone locally
2. `pip install -r requirements.txt`
3. `OPENAI_API_KEY=<YOUR_API_KEY> python app.py "Recommend some books, I love mystery novels."`
4. `git push`

## Getting started

The application will use an AI model (OpenAI's GPT3.5, AKA ChatGPT) to help a user get book recommendations. The application uses OpenAI's function calling support to allow for structured operations like searching for books or getting details for a specific book.

Here's how it works:

1. Convert the user query into a function call via GPT3.5
2. Run the function against the book DB
3. Combine the function output with the original query
4. Send that combined text to the model again
5. Show that output to the user

You will set up a CI pipeline to run some tests to validate this functionality calls and to help regression test changes to our prompt.

### Environment setup

We recommend creating a virtual environment to store your dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
# pip here runs inside the venv
pip install -r requirements.txt
```

The install command will include the AIConfig SDK and editor, which you will allow you to run the app and edit its configuration (including the prompt).

You will also need to provide an OpenAI API key by setting the `OPENAI_API_KEY` environment variable in order to use the AIConfig SDK.

### Run the application

The command-line application accepts questions about books and provides recommendations to the user based on a database of existing books.

Let's get some recommendations for mystery fans.

`OPENAI_API_KEY=<YOUR API KEY> python app.py "Recommend 2 books, I love mystery novels."`

### Set up the CI pipeline

Sign up for a circleci account at: https://circleci.com/signup/ and authorize the CircleCI Github application to access your account.

You can securely store your OpenAI key in a CircleCI Context

1. Go to `Organization Settings`
2. Click `Contexts`
3. Click `Create Context`
4. On the context form enter: `cci-last-mile-example` for the name
5. Edit the `cci-last-mile-example` context

- Click `Add Environment Variable`
- Enter: `OPENAI_API_KEY` as the name
- Paste your OpenAI API key as the value
- Click `Add Environment Variable`

Now we'll set up our project to build on CircleCI

1. From the project dashboard find your forked repository and click "Setup Project"
2. When prompted for a branch enter `main` and click `Setup project`

You should see a pipeline start to run in the CircleCI UI.

From your terminal, create and push a branch:

```bash
git checkout -b circleci-tests
git push origin circleci-test
```

Go to the CircleCI UI for the project, to view the pipeline.

You should see a failing test case for `test_function_accuracy` in the CircleCI UI.

You'll fix this failing test using the AIConfig editor and test module, then verify the fix in your CI pipeline.

### Running Tests Locally

The AIConfig test module supports running tests using `pytest` (`pip install pytest`).

In this application there are a few different types of tests to consider:

- Unit tests for our query logic to find books.
- Function Calling tests to validate that OpenAI infers the expected functions. For example, if we ask about Harper Lee, we'd expect the `search` function to be used.
- Natural language text generation tests (see example below).
- End-to-end tests. Analogous to traditional integration/end-to-end tests, but a little different for an AI application.

You can run all the tests with the following command:
`OPENAI_API_KEY=<YOUR_API_KEY> pytest test_app.py`

You should see the same test,`test_function_accuracy`, failure.

#### Query Logic Unit Tests

Ordinary unit tests for rule-based code. For every input/expected output pair, we call a function and assert its output is correct.

### Function Calling Tests

In this case, you can see that we are expecting the model to select the `search` function, which queries by book name, for the `To kill a mockingbird` query. But the model is choosing the `get`, which tries to look up a book by it's ISBN id, function instead.

We can fix this by editing the prompt using the AIConfig editor: `aiconfig edit --aiconfig-path book_db_function_calling.aiconfig.json`

We want to update the function description for `search` to be more specific. In the editor, update the description for the function to: `search queries books by their name and returns a list of book names and their ids`

You will also need to change the `get` function description to tell the model it should only accept ids: `get returns a book's detailed information based on the id of the book. Note that this does not accept names, and only IDs, which you can get by using search.`.

We also need to change the parameters for the `get` call to accept a property called `id`

Finally, we need to update `book_db.py` to use the `id` instead of the `book` parameter.

You can rerun the test: `OPENAI_API_KEY=<YOUR_API_KEY> pytest test_app.py` and they should pass.

You can commit the change and push to CircleCI

```bash
git add test_app.py
git commit -m "Fix failing test."
git push
```

#### Tests for Natural Language Text Generation

Even if we ran the correct function and got the correct data, sometimes the model doesn't extract, summarize, and/or infer the answer intelligently. For example,

Query:

> "search 'All the Light We Cannot See' book name. How many living immediate family members does Werner most likely have?"

Data:

> "In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister..."

Response:

> The given data does not provide any information about the number of living family members Werner has.

Please see test_threshold_book_recall() in `test_app.py` for a full example test for natural language generation given input data.

### End-to-end tests

You can also test AI apps e2e. For example, we expect the query "How widely-read is 'To Kill a Mockingbird'?" to include "18 million copies sold" which we know is in the book DB. This is done similarly to the natural language generation test, but instead of looking at the book DB data explicitly, it directly tests that a particular user query is answered correctly, in more of a black-box fashion.

## Metrics-Driven Model Testing

When we unit test our book DB API, it makes sense to guarantee that every call works exactly as expected.

However -- as you may have noticed by now -- we loosen things up a little for the other tests. This is due to the nature of testing AI models: since they are much less transparent and consistent than rule-based procedures, it is not necessarily practical to require that every test cases passes all the time.

Instead, we can compute metrics over our test data and then define assertions based on fixed thresholds. For example, we consider 90% accuracy as passing in function selection. Since function calling is somewhat similar to a classifier, it makes sense to evaluate it that way.