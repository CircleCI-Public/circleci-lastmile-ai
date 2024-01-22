# circleci-lastmile-ai

## Pre-requisites
* OpenAI API Key
* LastMile AIConfig editor installed
* CircleCI Account

## Quickstart

1. Fork this repository and clone locally
2. `pip install -r requirements.txt`
3. `OPENAI_API_KEY=<YOUR_API_KEY> python app.py "Recommend some books, I love mystery novels."`
4. `git push`

## Getting started

The application will use an AI model to help a user get book recommendations. The application uses OpenAI's function calling support to allow for structured operations like searching for books or getting details for a specific book.

You will set up a CI pipeline to run some tests to validate our function calls and to help regression test changes to our prompt.

### Environment setup
We recommend creating a virtual environment to store your dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
# pip here runs inside the venv
pip install -r requirements.txt
```

You will also need to provide an OpenAI API key by setting the `OPENAI_API_KEY` environment variable in order to use the AIConfig Editor.

### Run the application

The command-line application accepts questions about books and provides recommendations to the user based on a database of existing books.

Let's get some recommendations for mystery fans.

`OPENAI_API_KEY=<YOUR API KEY> python app.py "Recommend some books, I love mystery novels."`

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
1. From the project dahsboard find your forked repository and click "Setup Project"
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

The AIConfig test module supports running tests using `pytest`. In this application there are a few different types of tests to consider:

* Unit tests for our query logic to find books
* Function Calling tests to validate that OpenAI calls the expected functions. For example, if we ask about Harper Lee, we'd expect the `search` function to be used.
* Output tests to check that the prompts we send to OpenAI are producing expected responses.

You can run all the tests with the following command:
`OPENAI_API_KEY=<YOUR_API_KEY> pytest test_app.py`

You should see the same test,`test_function_accuracy`, failure.

*Note:* Our function calling application is using OpenAI as a classifier to select a function based on a user query. Our tests define a threshold to allow for occasional errors by the OpenAI model in selecting a function.

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


