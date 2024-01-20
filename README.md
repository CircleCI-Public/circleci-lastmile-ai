# circleci-lastmile-ai

## Pre-requisites
* OpenAI API Key
* LastMile AIConfig editor installed
* CircleCI Account

## Quickstart

1. `git clone git@github.com:CircleCI-Public/circleci-lastmile-ai.git`
2. `pip install -r requirements.txt`
3. `OPENAI_API_KEY=<YOUR_API_KEY> python app.py "Recommend some books, I love mystery novels."`

## Getting started

Our application will use an AI model to help a user get book recommendations. Our application uses OpenAI's function calling support to allow for structured operations like searching for books or getting details for a specific book.

We'll set up a CI pipeline to run some tests to validate our function calls and to help regression test changes to our prompt.

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

### Set up CircleCI

TODO: Work with Jacob on what our current fast path for this is

## Running and adding tests

We can write assertions about our application as standard pytest tests. In our application there are a few different types of tests to consider

### Testing our DB lookup functions

These are standard unit tests to validate our functions to query the book DB.

### Function calling tests

We pass our function schemas to OpenAI and the model decides which function to call. We want to write tests to verify the model is selecting the expected functions.

Consider asking our application about `Harper Lee`, here the model decides to use the `search` function
```bash
python app.py "Harper Lee"
```

> User query: Harper Lee
Function call response: arguments='{\n  "name": "Harper Lee"\n}' name='search', type: <class 'aiconfig.schema.FunctionCallData'>
Calling function search with args {
  "name": "Harper Lee"
}

### Output tests

Our application is supposed to help users with book recommendations, but we can experience issues with some queries giving non book information.

Taking the Harper Lee example, we get back biographical information about Lee. This information is accurate, but doesn't really help with the user request.

```bash
python app.py "Harper Lee"
```

>Harper Lee was an American author best known for her novel "To Kill a Mockingbird," which was published in 1960. The novel explores themes of racial injustice and the loss of innocence through the eyes of its young protagonist, Scout Finch. "To Kill a Mockingbird" became an instant classic and won the Pulitzer Prize for Fiction in 1961.

We can change the model settings system prompt to restrict the responses to providing book recommendations instead of general information.

