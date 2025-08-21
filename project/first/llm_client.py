import openai
import os
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LLMClient:
    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        # Ensure openai.api_key is set for compatibility with openai>=1.0.0
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided via argument or OPENAI_API_KEY env variable.")
        openai.api_key = self.api_key
        self.model = model
        self.max_retries = 3

    def generate_review(self, prompt: str) -> Optional[str]:
        """Generate code review with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1000
                )
                # For openai>=1.0.0, response.choices[0].message.content
                return response.choices[0].message.content

            except Exception as e:
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Max retries exceeded")
                    return None

    def analyze_changeset(self, file_path: str, diff: str, context: str = "") -> str:
        """Analyze a file changeset and provide suggestions"""
        # TODO: Create a formatted prompt string that includes file_path, diff, and context
        prompt = f"""
Code Review Request

Please review the following code changes for the file: {file_path}

### Code Changes (Diff):
```diff
{diff}
Additional Context:
{context if context else "No additional context provided."}
Review Requirements:
Provide a detailed code review with the following sections:

Summary of Changes: Briefly describe what the changes do.
Potential Issues: Identify any bugs, inefficiencies, or risks in the changes.
Suggestions for Improvement: Recommend specific improvements or best practices.
Overall Quality Assessment: Provide an overall evaluation of the code changes (e.g., quality, maintainability, adherence to best practices).

Ensure the review is concise, actionable, and focused on improving code quality.
"""
        # The prompt should ask for a code review with specific sections:
        # 1. Summary of changes
        # 2. Potential issues
        # 3. Suggestions for improvement
        # 4. Overall quality assessment
        
        # TODO: Call self.generate_review() with your formatted prompt
        review_result = self.generate_review(prompt)
        
        # TODO: Return the review result or "Failed to generate review" if the result is None
        return review_result if review_result is not None else "Failed to generate review"

if __name__ == "__main__":
    client = LLMClient()
    # TODO: Call the analyze_changeset method with a sample file path, diff, and context
    sample_file_path = "src/example.py"
    sample_diff = """
@@ -1,5 +1,7 @@
def calculate_sum(a, b):

return a + b


result = a + b
print(f"Sum: {{result}}")
return result
"""
    sample_context = "This change adds logging to the calculate_sum function for debugging purposes."
    result = client.analyze_changeset(sample_file_path, sample_diff, sample_context)
    # Then print the result
    print(result)
