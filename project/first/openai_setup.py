import openai
import os


def setup_openai_client():
    """
    Set up the OpenAI client with API key from environment variables.

    Returns:
        str: The name of the model to use for code review
    """
    # Get API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")

    # Set the API key for the OpenAI client
    openai.api_key = api_key

    # Set the model to use
    model = "gpt-4o"

    return model


def test_setup():
    """Test the OpenAI client setup"""
    model = setup_openai_client()
    if openai.api_key:
        print(f"OpenAI client set up successfully with model: {model}")
    else:
        print("Failed to set up OpenAI client. Check your API key.")


if __name__ == "__main__":
    test_setup()
