# Currently in progress. Using Google Gemini as a basis, but having troubles with installation.
# Below code is basically Google's code (asides from the question).
# Code allows user to input sample posts, combining them into a single string and summarizing all of their info.
# NOTE: may need to install google and gen-ai into program if not already done

from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client() # If you're wondering, the API key is directly set as PC user variable right now. Remind me to share later.

promptlist = ""
i = 1

while i != "0":
    prompt = input("\nMake an example social media post:" ) # prompting user for input
    promptlist += prompt
    promptlist += " , "
    i = input("Would you like to submit another post? Enter 0 if no, anything else if yes. ")


summaryrequest = "Summarize the following posts: " + promptlist # creating prompt to input into Gemini
response = client.models.generate_content(
    model="gemini-2.5-flash", contents=summaryrequest # setting contents to summaryrequest for the full prompt
)

print("\nGEMINI: ",response.text,"\n")