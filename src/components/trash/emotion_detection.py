# # emotion-detction.py
# from dotenv import load_dotenv
# import os
# from google import genai
# from google.genai import types

# load_dotenv()

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# def send_gemini(system_instruction, contents, emotions):
#     # Emotions param could later tweak tone or style
#     # config = types.GenerateContentConfig(
#     #     system_instruction=system_instruction,
#     #     temperature=0.5,
#     #     candidate_count=1
#     # )

#     response = client.models.generate_content(
#         model="gemini-2.5-pro",
#         config=types.GenerateContentConfig(system_instruction=system_instruction),
#         contents=contents,
#     )
#     return response.text
#     # return response