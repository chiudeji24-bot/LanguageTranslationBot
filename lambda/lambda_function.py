import boto3

def lambda_handler(event, context):
    try:
        # Ensure event is a dictionary
        if not isinstance(event, dict):
            raise ValueError("Invalid event format")

        # Extract sessionState, intent, and slots with None checks
        session_state = event.get('sessionState') if event else None
        if not session_state:
            raise ValueError("Missing sessionState in event")

        intent = session_state.get('intent', {})
        slots = intent.get('slots', {})
        text_slot = None
        language_slot = None

        # Extract text and language slots safely
        if slots.get('text') and slots['text'].get('value'):
            text_slot = slots['text']['value'].get('interpretedValue')
        if slots.get('language') and slots['language'].get('value'):
            language_slot = slots['language']['value'].get('interpretedValue')

        # Initialize response structure
        lex_response = {
            "sessionState": {
                "dialogAction": {},
                "intent": {
                    "name": "TranslationIntent",
                    "slots": slots
                }
            },
            "messages": []
        }

        # If language is missing, elicit language slot
        if not language_slot:
            lex_response["sessionState"]["dialogAction"] = {
                "type": "ElicitSlot",
                "slotToElicit": "language"
            }
            lex_response["messages"] = [
                {
                    "contentType": "PlainText",
                    "content": "In which language would you like to translate the text?"
                }
            ]
            return lex_response

        # If text is missing, elicit text slot
        if not text_slot:
            lex_response["sessionState"]["dialogAction"] = {
                "type": "ElicitSlot",
                "slotToElicit": "text"
            }
            lex_response["messages"] = [
                {
                    "contentType": "PlainText",
                    "content": "Please input the text you want to translate"
                }
            ]
            return lex_response

        # Validate input text
        if not text_slot.strip():
            raise ValueError("Input text is empty.")

        # Map language to code
        language_codes = {
            'French': 'fr',
            'German': 'de',
            'Chinese': 'zh',
            'Japanese': 'ja',
            'Norwegian': 'no',
            'Spanish': 'es'
        }

        if language_slot not in language_codes:
            raise ValueError(f"Unsupported language: {language_slot}")

        target_language_code = language_codes[language_slot]

        # Initialize Amazon Translate client
        translate_client = boto3.client('translate')

        # Call Amazon Translate
        response = translate_client.translate_text(
            Text=text_slot,
            SourceLanguageCode='auto',
            TargetLanguageCode=target_language_code
        )

        translated_text = response.get('TranslatedText', 'Translation failed')

        # Return successful translation
        lex_response["sessionState"]["dialogAction"] = {
            "type": "Close"
        }
        lex_response["sessionState"]["intent"]["state"] = "Fulfilled"
        lex_response["messages"] = [
            {
                "contentType": "PlainText",
                "content": translated_text
            }
        ]
        return lex_response

    except Exception as error:
        error_message = f"Lambda execution error: {str(error)}"
        print(error_message)
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "TranslationIntent",
                    "state": "Failed"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": error_message
                }
            ]
        }