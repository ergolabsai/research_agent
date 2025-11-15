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

Please provide:
1. Overall assessment of the draft
2. Strengths of the paper
3. Areas that need improvement
4. Specific suggestions for revision
5. Comments on clarity and organization

If images are provided, also comment on:
- How well the images support the text
- Whether the images are clear and well-labeled
- Suggestions for improving the figures"""
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
        
        result = {
            "success": True,
            "analysis": response_text,
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
