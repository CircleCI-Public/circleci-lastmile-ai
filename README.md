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
Go to the CircleCI UI for the project, to view the pipeline. You should see a failing test case in the CircleCI UI.

### Running Tests

The AIConfig test module supports running tests using `pytest`. In this application there are a few different types of tests to consider:

* Unit tests for our query logic to find books
* Function Calling tests to validate that OpenAI calls the expected functions. For example, if we ask about Harper Lee, we'd expect the `search` function to be used.
* Output tests to check that the prompts we send to OpenAI are producing expected responses.

You can run all the tests with the following command:
`OPENAI_API_KEY=<YOUR_API_KEY> pytest test_app.py`