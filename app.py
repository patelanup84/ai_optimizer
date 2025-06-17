# app.py
import os
import uuid
import time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from dotenv import load_dotenv
from flow import create_brand_monitoring_flow
from utils.database import SimpleJSONDB
from utils.pdf_generator import PDFGenerator
import threading
from datetime import datetime
import io

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Store for tracking analysis sessions
analysis_sessions = {}

# Initialize PDF generator
pdf_generator = PDFGenerator(app.root_path)

def run_analysis_async(session_id, brand_config):
    """Run brand analysis in background and store results"""
    try:
        # Update session status
        analysis_sessions[session_id] = {
            "status": "running",
            "progress": "Generating strategic queries...",
            "start_time": time.time()
        }
        
        # Create shared data store
        shared = {"brand_config": brand_config}
        
        # Run the analysis flow
        flow = create_brand_monitoring_flow()
        flow.run(shared)
        
        # Store results in database
        db = SimpleJSONDB()
        brand_id = db.store_brand_config(brand_config)
        
        # Store analysis results with defaults
        analysis_data = {
            "session_id": session_id,
            "brand_config": shared.get("brand_config", {}),
            "analysis": {
                "total_responses": shared.get("analysis", {}).get("total_responses", 0),
                "total_mentions": shared.get("analysis", {}).get("total_mentions", 0),
                "total_organic_mentions": shared.get("analysis", {}).get("total_organic_mentions", 0),
                "organic_mention_rate": shared.get("analysis", {}).get("organic_mention_rate", 0),
                "avg_sentiment": shared.get("analysis", {}).get("avg_sentiment", 0),
                "category_breakdown": shared.get("analysis", {}).get("category_breakdown", {}),
                **shared.get("analysis", {})  # Include any other fields
            },
            "ai_responses": shared.get("ai_responses", {}),
            "recommendations": shared.get("recommendations", {}),
            "reports": shared.get("reports", {}),
            "completed_at": datetime.now().isoformat()
        }
        
        # Update session with results
        analysis_sessions[session_id] = {
            "status": "completed",
            "results": analysis_data,
            "completion_time": time.time()
        }
        
    except Exception as e:
        analysis_sessions[session_id] = {
            "status": "error",
            "error": str(e),
            "completion_time": time.time()
        }

@app.route('/')
def index():
    """Main form page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Start brand analysis"""
    try:
        # Validate form data
        brand_name = request.form.get('brand_name', '').strip()
        industry = request.form.get('industry', '').strip()
        keywords = request.form.get('keywords', '').strip()
        
        if not brand_name:
            flash('Brand name is required', 'error')
            return redirect(url_for('index'))
        
        if not industry:
            flash('Industry is required', 'error')
            return redirect(url_for('index'))
        
        # Process keywords
        keyword_list = [brand_name]
        if keywords:
            additional_keywords = [k.strip() for k in keywords.split('\n') if k.strip()]
            for keyword in additional_keywords:
                if keyword.lower() != brand_name.lower() and keyword not in keyword_list:
                    keyword_list.append(keyword)
        
        # Create brand configuration
        brand_config = {
            "name": brand_name,
            "keywords": keyword_list,
            "industry": industry
        }
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Start background analysis
        thread = threading.Thread(
            target=run_analysis_async, 
            args=(session_id, brand_config)
        )
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('loading', session_id=session_id))
        
    except Exception as e:
        flash(f'Error starting analysis: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/loading/<session_id>')
def loading(session_id):
    """Loading page with progress"""
    session_data = analysis_sessions.get(session_id)
    
    if not session_data:
        flash('Analysis session not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('loading.html', session_id=session_id)

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """API endpoint to check analysis status"""
    session_data = analysis_sessions.get(session_id)
    
    if not session_data:
        return jsonify({"status": "not_found"}), 404
    
    status = session_data.get("status", "unknown")
    
    if status == "completed":
        return jsonify({
            "status": "completed",
            "redirect_url": url_for('results', session_id=session_id)
        })
    elif status == "error":
        return jsonify({
            "status": "error",
            "error": session_data.get("error", "Unknown error")
        })
    else:
        return jsonify({
            "status": "running",
            "progress": session_data.get("progress", "Processing...")
        })

@app.route('/results/<session_id>')
def results(session_id):
    """Results display page"""
    session_data = analysis_sessions.get(session_id)
    
    if not session_data or session_data.get("status") != "completed":
        flash('Analysis results not found or not ready', 'error')
        return redirect(url_for('index'))
    
    results_data = session_data.get("results", {})
    return render_template('results.html', data=results_data)

@app.route('/history')
def history():
    """View historical analyses"""
    db = SimpleJSONDB()
    brands = db.data.get("brands", {})
    reports = db.data.get("reports", [])
    
    return render_template('history.html', brands=brands, reports=reports)

@app.route('/download-pdf/<session_id>')
def download_pdf(session_id):
    """Download analysis results as PDF"""
    try:
        session_data = analysis_sessions.get(session_id)
        
        if not session_data or session_data.get("status") != "completed":
            flash('Analysis results not found or not ready', 'error')
            return redirect(url_for('index'))
        
        results_data = session_data.get("results", {})
        brand_name = results_data.get("brand_config", {}).get("name", "Unknown Brand")
        
        # Generate PDF
        pdf_content = pdf_generator.generate_pdf(results_data)
        
        # Create filename
        filename = pdf_generator.get_filename(brand_name)
        
        # Return PDF as downloadable file
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('results', session_id=session_id))

if __name__ == '__main__':
    app.run(debug=True)
