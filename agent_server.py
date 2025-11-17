from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json
import os
from agent_files.multi_step_paper_review import ReviewSession

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

        os.environ["CLAUDE_API_KEY"] = api_key

        if not api_key:
            print("ERROR: No API key provided")
            return jsonify({'error': 'API key is required'}), 400

        if not draft:
            print("ERROR: No draft text provided")
            return jsonify({'error': 'Draft text is required'}), 400

        review_session = ReviewSession()
        review_session.text = draft

        review_session.create_context()

        print(review_session.context)

        context_list_for_return = []
        ii = 0
        for item in review_session.current_response.context:
            context_list_for_return = context_list_for_return + [{"id": ii,
                                                                  "text": item}]
            ii = ii + 1

        result = {'success': True, 'items': context_list_for_return}

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

    return jsonify(result)


@app.route('/api/process-selected', methods=['POST'])
def process_selected():
    """
    API endpoint that receives selected context items and processes them with Claude
    """
    try:
        data = request.get_json()

        api_key = data.get('apiKey')
        selected_items = data.get('selectedItems', [])
        original_draft = data.get('originalDraft', '')

        if not api_key:
            # Try to get from environment if not provided
            api_key = os.environ.get('CLAUDE_API_KEY')

        if not api_key:
            print("ERROR: No API key provided")
            return jsonify({'error': 'API key is required'}), 400

        if not selected_items:
            print("ERROR: No selected items provided")
            return jsonify({'error': 'Selected items are required'}), 400

        # Print out the received data
        print("\n" + "=" * 80)
        print("RECEIVED SELECTED CONTEXT ITEMS:")
        print("=" * 80)
        print(f"\nNumber of selected items: {len(selected_items)}")
        print(f"\nOriginal draft length: {len(original_draft)} characters")
        print("\nSelected Items:")
        print("-" * 80)

        for idx, item in enumerate(selected_items, 1):
            print(f"\n[Item {idx}]")
            print(f"ID: {item.get('id')}")
            print(f"Text: {item.get('text')}")
            print("-" * 80)

        print("\n" + "=" * 80)
        print("END OF SELECTED ITEMS")
        print("=" * 80 + "\n")

        # TODO: Add your Claude API call here to process the selected items
        # For now, just return a success response

        result = {
            'success': True,
            'message': f'Received {len(selected_items)} selected items',
            'items_count': len(selected_items)
        }

        return jsonify(result)

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