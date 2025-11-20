from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json
import os
from agent_files.multi_step_paper_review import ReviewSession

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173'])

SIMPLIFY = False
@app.route('/api/create_context', methods=['POST'])
def create_context():
    """
    API endpoint that receives draft text and images and returns analysis
    """
    try:
        data = request.get_json()

        api_key = data.get('apiKey')
        draft = data.get('draft')

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


@app.route('/api/refine_context', methods=['POST'])
def refine_context():
    """
    API endpoint that receives selected context items and processes them with Claude
    """
    try:
        data = request.get_json()

        api_key = data.get('apiKey')
        selected_items = data.get('selectedItems', [])
        draft = data.get('draft', '')

        if not api_key:
            # Try to get from environment if not provided
            api_key = os.environ.get('CLAUDE_API_KEY')

        os.environ["CLAUDE_API_KEY"] = api_key

        if not api_key:
            print("ERROR: No API key provided")
            return jsonify({'error': 'API key is required'}), 400

        if not selected_items:
            print("ERROR: No selected items provided")
            return jsonify({'error': 'Selected items are required'}), 400

        review_session = ReviewSession()
        review_session.text = draft

        new_context = [item['text'] for item in selected_items]
        new_context = '. '.join(new_context)

        review_session.regenerate_context(new_context)

        result = {
            'success': True,
            'context': review_session.context,
        }

        print(result)

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

@app.route('/api/analyze_images', methods=['POST'])
def analyze_images():
    try:
        data = request.get_json()

        api_key = data.get('apiKey')
        draft = data.get('draft')
        images = data.get('images', [])
        context = data.get('context', [])

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

        review_session.load_images(images)
        review_session.create_expected_figure_descriptions(simplify=SIMPLIFY, make_plots=True)
        review_session.context = context
        review_session.compare_expected_figure_to_figure(simplify=SIMPLIFY)

        keys = review_session.expected_images.keys()
        expected_images = [review_session.expected_images[key] for key in keys]
        expected_media_types = [review_session.expected_media_types[key] for key in keys]
        figure_differences = [review_session.figure_differences[key] for key in keys]
        figure_similarities = [review_session.figure_similarities[key] for key in keys]

        result = {'success': True, 
                  'expected_images': expected_images,
                  'expected_media_types': expected_media_types,
                  'figure_differences': figure_differences,
                  'figure_similarities': figure_similarities}
        
        print(result)

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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Python agent server is running'})


if __name__ == '__main__':
    print("🐍 Python Agent Server starting...")
    print("✅ Server running on http://localhost:5001")
    print("✅ Ready to accept requests from http://localhost:5173")
    # app.run(host='0.0.0.0', port=5001, debug=True)
    app.run(
    debug=False,  # Set to False when using VS Code debugger
    use_reloader=False,  # Must be False for debugging
    host='127.0.0.1',  # Or '0.0.0.0' if accessing from another machine
    port=5001
    )