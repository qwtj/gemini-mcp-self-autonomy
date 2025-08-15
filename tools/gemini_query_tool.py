# tools/gemini_query_tool.py
import os
import google.generativeai as genai

def get_meta():
    return {
        'name': 'gemini_query_tool',
        'description': 'A tool that queries the Google Gemini API using an environment variable for the API key.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'question': {
                    'type': 'string',
                    'description': 'The question to ask the Gemini API.'
                }
            },
            'required': ['question']
        }
    }

def run(tool_input):
    api_key = os.environ.get('GOOGLE_API_KEY')

    if not api_key:
        return {
            'status': 'error',
            'message': 'GOOGLE_API_KEY environment variable not found. Please set it to use this tool.'
        }

    try:
        genai.configure(api_key=api_key)

        # For more advanced usage, you might want to allow model selection via input
        model = genai.GenerativeModel('gemini-2.0-flash')

        question = tool_input.get('question')
        if not question:
            return {'status': 'error', 'message': 'Missing required input: question.'}

        response = model.generate_content(question)

        if response.candidates:
            # Assuming we want the text from the first part of the first candidate
            # For more complex responses, you might need to iterate through parts
            if response.candidates[0].content.parts:
                return {
                    'status': 'success',
                    'response': response.candidates[0].content.parts[0].text
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Gemini response had no text parts.',
                    'full_response': str(response)
                }
        else:
            return {
                'status': 'error',
                'message': 'Gemini API returned no candidates.',
                'full_response': str(response)
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'An error occurred while querying Gemini API: {str(e)}'
        }
