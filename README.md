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






