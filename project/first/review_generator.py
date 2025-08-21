import openai
import os


def setup_openai_client():
    """Set up the OpenAI client with API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = api_key
    return "gpt-4o"


def generate_review(prompt):
    """
    Generate a code review based on the given prompt.

    Args:
        prompt (str): The prompt describing the code to review

    Returns:
        str or None: The generated review text, or None if an error occurs
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except openai.error.AuthenticationError:
        print("Error: Invalid API key or authentication failure")
        return None
    except openai.error.RateLimitError:
        print("Error: Rate limit exceeded. Please try again later")
        return None
    except openai.error.OpenAIError as e:
        print(f"Error: An OpenAI API error occurred: {str(e)}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")
        return None


def test_review():
    """Test the review generation with a simple code snippet"""
    # Set up the OpenAI client
    setup_openai_client()

    # Sample code to review
    code_snippet = """
    def calculate_sum(numbers):
        total = 0
        for num in numbers:
            total += num
        return total
    """

    prompt = f"Review this code snippet and provide feedback:\n\n{code_snippet}"

    # Test successful API call
    print("Testing successful API call...")
    review = generate_review(prompt)
    if review:
        print("\nGenerated Review:")
        print("-----------------")
        print(review)
    else:
        print("Failed to generate review")

    # TODO: Add a test for error handling by temporarily setting an invalid API key
    # and verifying that the function returns None instead of crashing


if __name__ == "__main__":
    test_review()
