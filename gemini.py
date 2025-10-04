# Currently in progress. Using Google Gemini as a basis, but having troubles with installation.
# Below code is basically Google's code (asides from the question). I will try to get this up and running ASAP. - Joe
# Basic AI implementation, uses Gemini 2.5 Flash model to answer a prompt.

from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client() # If you're wondering, the API key is directly set as PC user variable right now. Remind me to share later.


response = client.models.generate_content(
    model="gemini-2.5-flash", contents="How much time do we have left?"
)
print(response.text)