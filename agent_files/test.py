from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json
import os
import base64

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173'])


@app.route('/api/analyze', methods=['POST'])
def analyze_paper():
    """
    API endpoint that receives draft text and images and returns analysis
    """
    try:
        data = request.get_json()

        api_key = data.get('apiKey')
        draft = data.get('draft')
        images = data.get('images', [])

        if not api_key:
            # Try to get from environment if not provided
            api_key = os.environ.get('CLAUDE_API_KEY')

        if not api_key:
            print("ERROR: No API key provided")
            return jsonify({'error': 'API key is required'}), 400

        if not draft:
            print("ERROR: No draft text provided")
            return jsonify({'error': 'Draft text is required'}), 400

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Build the message content
        content = []

        # Add the draft text with instructions
        content.append({
            "type": "text",
            "text": f"""You are a research paper reviewer. Analyze the following draft and provide constructive feedback:

Draft Text:
{draft}

Please provide your feedback as a structured JSON list. Each item should have:
- category: one of ["Overall", "Strength", "Weakness", "Suggestion", "Clarity", "Organization", "Figure"]
- text: a brief title/summary (max 100 characters)
- details: detailed explanation

Return ONLY valid JSON in this exact format:
{{
  "items": [
    {{
      "category": "Overall",
      "text": "Brief assessment title",
      "details": "Detailed explanation here"
    }},
    {{
      "category": "Strength",
      "text": "What's good about the paper",
      "details": "Why this is a strength"
    }}
  ]
}}

Include items for:
- Overall assessment (1 item)
- Strengths (3-5 items)
- Weaknesses (3-5 items)
- Specific suggestions (3-5 items)
- Clarity and organization comments (2-3 items)
- Figure comments if images provided (1 item per image)

CRITICAL: Return ONLY the JSON object, no other text."""
        })

        # Add images if provided
        for img in images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.get('type', 'image/jpeg'),
                    "data": img.get('data')
                }
            })

        print(f"Analyzing draft with {len(images)} images...")

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        # Extract the response text
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            feedback_data = json.loads(cleaned_text)

            # Add IDs to items if not present
            if "items" in feedback_data:
                for i, item in enumerate(feedback_data["items"]):
                    if "id" not in item:
                        item["id"] = i + 1

            result = {
                "success": True,
                "items": feedback_data.get("items", []),
                "model": message.model,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return as plain text
            print(f"Warning: Could not parse JSON response: {e}")
            result = {
                "success": True,
                "items": [{
                    "id": 1,
                    "category": "Error",
                    "text": "Failed to parse structured response",
                    "details": response_text
                }],
                "model": message.model,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        return jsonify(result)

    except anthropic.APIError as e:
        print(f"ERROR: Anthropic API error - {str(e)}")
        return jsonify({'error': f'API error: {str(e)}'}), 500
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode error - {str(e)}")
        return jsonify({'error': f'Failed to parse request: {str(e)}'}), 400
    except Exception as e:
        print(f"ERROR: Unexpected error - {str(e)}")
        print(f"ERROR Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Python agent server is running'})


if __name__ == '__main__':
    print("🐍 Python Agent Server starting...")
    print("✅ Server running on http://localhost:5001")
    print("✅ Ready to accept requests from http://localhost:5173")
    app.run(host='0.0.0.0', port=5001, debug=True)