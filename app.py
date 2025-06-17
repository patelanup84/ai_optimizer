# app.py
import os
import uuid
import time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from flow import create_brand_monitoring_flow
from utils.database import SimpleJSONDB
import threading
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Store for tracking analysis sessions
analysis_sessions = {}

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
        
        # Store analysis results
        analysis_data = {
            "session_id": session_id,
            "brand_config": shared.get("brand_config", {}),
            "analysis": shared.get("analysis", {}),
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

if __name__ == '__main__':
    app.run(debug=True)

