import io
import json
import os
import sys
from flask import Flask, request, jsonify, send_file, render_template

# Ensure workspace dir is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main

app = Flask(__name__)

# Ensure templates directory is configured correctly
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


@app.route('/')
def index():
    """Serve the main builder interface."""
    return render_template('index.html')


@app.route('/api/clean', methods=['POST'])
def clean_resume():
    """Clean the raw resume text format."""
    payload = request.get_json() or {}
    raw_text = payload.get('text', '')
    
    # Run the same cleaner as CLI
    cleaned = main.clean_text(raw_text)
    return jsonify({
        'success': True,
        'cleaned_text': cleaned
    })


@app.route('/api/generate', methods=['POST'])
def generate_portfolio():
    """Call Gemini to extract structured portfolio data from resume text."""
    payload = request.get_json() or {}
    text = payload.get('text', '').strip()
    is_demo = payload.get('demo', False)

    if is_demo:
        # Return mock demo data
        demo_data = main.validate_and_complete(main.SAMPLE_DATA)
        return jsonify({
            'success': True,
            'data': demo_data
        })

    if not text:
        return jsonify({
            'success': False,
            'error': 'Resume text is required'
        }), 400

    if len(text) < main.MIN_RESUME_LENGTH:
        return jsonify({
            'success': False,
            'error': f'Resume is too short ({len(text)} characters). Please enter at least {main.MIN_RESUME_LENGTH} characters.'
        }), 400

    try:
        # Load API keys and configurations
        main.load_env()
        api_key = main.get_api_key()
        model_name = os.getenv("GEMINI_MODEL", "").strip() or main.DEFAULT_MODEL
        
        prompt = main.build_prompt(text)
        raw_response = main.call_gemini(prompt, api_key, model_name)
        extracted = main.extract_json(raw_response)
        completed_data = main.validate_and_complete(extracted)
        
        return jsonify({
            'success': True,
            'data': completed_data
        })
    except main.ProjectError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@app.route('/api/preview', methods=['POST'])
def preview_portfolio():
    """Render and return the portfolio HTML for live iframe preview."""
    payload = request.get_json() or {}
    data = payload.get('data', {})
    theme = payload.get('theme', 'minimal')
    
    # Set default values for rendering
    data = main.validate_and_complete(data)
    
    template_name = f'theme_{theme}.html'
    try:
        rendered_html = render_template(template_name, **data)
        return rendered_html
    except Exception as e:
        return f"<h3>Error rendering theme: {str(e)}</h3>", 500


@app.route('/api/download', methods=['POST'])
def download_portfolio():
    """Generate and trigger a file download of the styled portfolio."""
    payload = request.get_json() or {}
    data = payload.get('data', {})
    theme = payload.get('theme', 'minimal')
    
    # Normalise input data
    data = main.validate_and_complete(data)
    
    template_name = f'theme_{theme}.html'
    try:
        rendered_html = render_template(template_name, **data)
        
        # Write to dynamic buffer for download
        buffer = io.BytesIO()
        buffer.write(rendered_html.encode('utf-8'))
        buffer.seek(0)
        
        # Prepare friendly file name
        safe_name = "".join(c for c in data.get('name', 'portfolio') if c.isalnum() or c in (' ', '_', '-')).strip()
        filename = f"{safe_name.lower().replace(' ', '_')}_portfolio.html"
        
        return send_file(
            buffer,
            mimetype='text/html',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate download: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Start the server on port 5000 (standard for local dev)
    print("-----------------------------------------------------------------")
    print(" Starting Resume Portfolio Generator Web Studio on port 5000...")
    print(" Open http://localhost:5000 in your browser to build your portfolio.")
    print("-----------------------------------------------------------------")
    app.run(debug=True, port=5000)
