from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import json
import os
from agent_files import multi_step_paper_review as mspr

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173'])


@app.route('/api/analyze', methods=['POST'])
def analyze_proposal():
    """
    API endpoint that receives proposal text and returns analysis
    """
    try:
        data = request.get_json()

        api_key = data.get('apiKey')
        paper = data.get('paper')

        if not api_key:
            api_key = os.environ.get('CLAUDE_API_KEY')

        if not paper:
            print("ERROR: No paper text provided")
            return jsonify({'error': 'Proposal text is required'}), 400

        # Initialize your agent
        agent = ProposalAnalyzerAgent(api_key)

        # Run the analysis
        result = agent.analyze_proposal(proposal)

        return jsonify(result)

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode error - {str(e)}")
        return jsonify({'error': f'Failed to parse AI response: {str(e)}'}), 500
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