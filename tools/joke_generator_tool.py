# tools/joke_generator_tool.py
import os
import google.generativeai as genai

def get_meta():
    return {
        'name': 'joke_generator_tool',
        'description': 'Generates a random joke using the Google Gemini API.',
        'input_schema': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }

def run(tool_input):
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return {
            'status': 'error',
            'message': 'GOOGLE_API_KEY environment variable not set. Please set the API key to use this tool.'
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Generate a joke using Gemini
        response = model.generate_content("Tell me a short, family-friendly joke.")
        joke_text = response.text

        return {
            'status': 'success',
            'joke': joke_text
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to generate joke: {str(e)}'
        }
