import openai
import os
import time

def setup_openai_client():
    """Set up the OpenAI client with API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = api_key
    return "gpt-4o"

def generate_review_with_retry(prompt, max_retries=3):
    """
    Generate a code review with retry logic and exponential backoff.
    
    Args:
        prompt (str): The prompt describing the code to review
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str or None: The generated review text, or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except openai.error.AuthenticationError:
            print(f"Attempt {attempt + 1}/{max_retries}: Authentication error - Invalid API key")
        except openai.error.RateLimitError:
            print(f"Attempt {attempt + 1}/{max_retries}: Rate limit exceeded")
        except openai.error.OpenAIError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: OpenAI API error - {str(e)}")
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Unexpected error - {str(e)}")
            
        if attempt < max_retries - 1:  # Don't sleep on the last attempt
            sleep_time = 2 ** attempt
            print(f"Waiting {sleep_time} seconds before retrying...")
            time.sleep(sleep_time)
    
    print(f"All {max_retries} retry attempts failed")
    return None

def test_retry():
    """Test the retry logic with a simple code snippet"""
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
    
    # Test with valid API key
    print("Testing with valid API key...")
    review = generate_review_with_retry(prompt)
    if review:
        print("\nGenerated Review:")
        print("-----------------")
        print(review)
    else:
        print("Failed to generate review after retries")
    
    # Test with invalid API key to trigger retries
    print("\nTesting retry logic with invalid API key...")
    original_key = openai.api_key
    openai.api_key = "invalid_key"
    
    # Start timing
    start_time = time.time()
    error_review = generate_review_with_retry(prompt, max_retries=3)
    end_time = time.time()
    
    # Check if appropriate time passed (should be at least 3 seconds for 2 retries with backoff)
    elapsed_time = end_time - start_time
    if error_review is None and elapsed_time >= 3:
        print(f"Retry logic works correctly! Elapsed time: {elapsed_time:.2f} seconds")
    elif error_review is None:
        print(f"Retries completed but timing is suspicious. Elapsed time: {elapsed_time:.2f} seconds")
    else:
        print("Retry logic failed - function returned a result when it should have returned None")
    
    # Restore the original API key
    openai.api_key = original_key

if __name__ == "__main__":
    test_retry()
