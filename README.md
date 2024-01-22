# circleci-lastmile-ai

## Pre-requisites

- OpenAI API Key
- CircleCI Account

## Quickstart

1. `git clone git@github.com:CircleCI-Public/circleci-lastmile-ai.git`
2. `pip install -r requirements.txt`
3. `OPENAI_API_KEY=<YOUR_API_KEY> python app.py "Recommend some books, I love mystery novels."`

## Getting started

Our application will use an AI model (OpenAI's GPT3.5 AKA ChatGPT) to help a user get book recommendations. Our application uses OpenAI's function calling support to allow for structured operations like searching for books or getting details for a specific book.

Here's how it works:

1. Convert the user query into a function call via GPT3.5
2. Run the function against the book DB
3. Combine the function output with the original query
4. Send that combined text to the model again
5. Show that output to the user

We'll set up a CI pipeline to run some tests to validate this functionality and to help regression test changes to our prompt.

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

### Set up CircleCI

TODO: Work with Jacob on what our current fast path for this is

## Running and adding tests

We can write assertions about our application as standard pytest tests. In our application there are a few different types of tests to consider.

### Testing our DB lookup functions

These are standard unit tests to validate our functions to query the book DB.

### Function calling tests

Essentially, we ask GPT3.5 what function should be called in order to answer the user query. It also gives us the arguments to call the function with.

We want to write tests to verify the model is selecting the expected functions (and arguments).

Consider asking our application about `Harper Lee`, here the model decides to use the `search` function

```bash
python app.py "Harper Lee"
```

> User query: Harper Lee
> Function call response: arguments='{\n "name": "Harper Lee"\n}' name='search', type: <class 'aiconfig.schema.FunctionCallData'>
> Calling function search with args {
> "name": "Harper Lee"
> }

### Final text generation

Even if we ran the correct function and got the correct data, sometimes the model doesn't extract, summarize, and/or infer the answer intelligently. For example,

Query:

> "search 'All the Light We Cannot See' book name. How many living family members does Werner most likely have?"

Data:

> "In a mining town in Germany, Werner Pfennig, an orphan, grows up with his younger sister..."

Response:

> The given data does not provide any information about the number of living family members Werner has.

We can test for this kind of problem as well.

### End-to-end tests

Our application is supposed to help users with book recommendations, but we can experience issues with some queries giving non book information.

Taking the Harper Lee example, we get back biographical information about Lee. This information is accurate, but doesn't really help with the user request.

```bash
python app.py "Harper Lee"
```

> Harper Lee was an American author best known for her novel "To Kill a Mockingbird," which was published in 1960. The novel explores themes of racial injustice and the loss of innocence through the eyes of its young protagonist, Scout Finch. "To Kill a Mockingbird" became an instant classic and won the Pulitzer Prize for Fiction in 1961.

We can change the model settings system prompt to restrict the responses to providing book recommendations instead of general information.

## Metrics-driven model testing

When we unit test our book DB API, it makes sense to guarantee that every call works exactly as expected. However, in the other tests, we loosen things up a little because of the nature of testing AI models. Since they are much less transparent and consistent than rule-based processes, it is not necessarily practical to insist that every test cases passes all the time.

Instead, in some of our tests we set thresholds. For example, we consider 90% accuracy as passing in function selection.
