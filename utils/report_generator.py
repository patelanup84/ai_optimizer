# utils/call_llm.py
import openai
import os

def call_llm(prompt, model="gpt-4o-mini"):
    """Call OpenAI LLM with the given prompt"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM call failed: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    test_prompt = "What is brand monitoring?"
    print(call_llm(test_prompt))


# utils/ai_platforms.py
import requests
import json
import time
from typing import Dict, Any

def query_chatgpt(query: str) -> Dict[str, Any]:
    """Query ChatGPT and return response with metadata"""
    try:
        from utils.call_llm import call_llm
        
        # Simulate querying ChatGPT as a user would
        prompt = f"Please answer this question as you would for any user: {query}"
        response = call_llm(prompt)
        
        return {
            "platform": "chatgpt",
            "query": query,
            "response": response,
            "timestamp": time.time(),
            "status": "success"
        }
    except Exception as e:
        return {
            "platform": "chatgpt", 
            "query": query,
            "response": "",
            "timestamp": time.time(),
            "status": "error",
            "error": str(e)
        }

def query_gemini(query: str) -> Dict[str, Any]:
    """Query Google Gemini and return response with metadata"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini (requires GOOGLE_API_KEY environment variable)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise Exception("GOOGLE_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(query)
        
        return {
            "platform": "gemini",
            "query": query, 
            "response": response.text,
            "timestamp": time.time(),
            "status": "success"
        }
    except Exception as e:
        # Fallback: simulate Gemini response using OpenAI for demo
        print(f"Gemini API failed, using fallback: {e}")
        try:
            from utils.call_llm import call_llm
            prompt = f"[Simulating Gemini] Please answer: {query}"
            response = call_llm(prompt)
            
            return {
                "platform": "gemini",
                "query": query,
                "response": f"[Simulated Gemini Response] {response}",
                "timestamp": time.time(),
                "status": "fallback"
            }
        except Exception as e2:
            return {
                "platform": "gemini",
                "query": query,
                "response": "",
                "timestamp": time.time(),
                "status": "error", 
                "error": str(e2)
            }

if __name__ == "__main__":
    test_query = "What do you know about Tesla cars?"
    
    print("Testing ChatGPT:")
    result1 = query_chatgpt(test_query)
    print(f"Status: {result1['status']}")
    print(f"Response: {result1['response'][:100]}...")
    
    print("\nTesting Gemini:")
    result2 = query_gemini(test_query)
    print(f"Status: {result2['status']}")
    print(f"Response: {result2['response'][:100]}...")


# utils/text_analysis.py
import re
from typing import Dict, List, Any

def analyze_brand_mentions(text: str, brand_keywords: List[str]) -> Dict[str, Any]:
    """Analyze text for brand mentions and sentiment"""
    text_lower = text.lower()
    
    # Find brand mentions
    mentions = []
    for keyword in brand_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in text_lower:
            # Find all occurrences with context
            pattern = r'.{0,50}' + re.escape(keyword_lower) + r'.{0,50}'
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                mentions.append({
                    "keyword": keyword,
                    "context": match.group(),
                    "position": match.start()
                })
    
    # Simple sentiment analysis (you could use a proper NLP library here)
    sentiment_score = calculate_sentiment(text, mentions)
    
    # Extract key themes/topics
    themes = extract_themes(text)
    
    return {
        "mentions_found": len(mentions),
        "mentions": mentions,
        "sentiment_score": sentiment_score,
        "sentiment_label": get_sentiment_label(sentiment_score),
        "themes": themes,
        "word_count": len(text.split()),
        "contains_brand": len(mentions) > 0
    }

def calculate_sentiment(text: str, mentions: List[Dict]) -> float:
    """Calculate sentiment score (-1 to 1)"""
    if not mentions:
        return 0.0
    
    # Simple keyword-based sentiment
    positive_words = ['good', 'great', 'excellent', 'amazing', 'best', 'love', 'fantastic', 
                      'wonderful', 'outstanding', 'superior', 'innovative', 'reliable']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'horrible', 'poor',
                      'disappointing', 'unreliable', 'expensive', 'overpriced', 'problem']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    # Normalize by text length
    sentiment = (positive_count - negative_count) / max(total_words / 10, 1)
    return max(-1.0, min(1.0, sentiment))

def get_sentiment_label(score: float) -> str:
    """Convert sentiment score to label"""
    if score > 0.2:
        return "positive"
    elif score < -0.2:
        return "negative"
    else:
        return "neutral"

def extract_themes(text: str) -> List[str]:
    """Extract key themes from text"""
    # Simple theme extraction based on common topics
    themes = []
    text_lower = text.lower()
    
    theme_keywords = {
        "product_quality": ["quality", "performance", "reliability", "durable"],
        "customer_service": ["service", "support", "help", "assistance"],
        "pricing": ["price", "cost", "expensive", "cheap", "value", "money"],
        "innovation": ["innovative", "technology", "advanced", "cutting-edge"],
        "competition": ["competitor", "alternative", "versus", "compared to"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            themes.append(theme)
    
    return themes

if __name__ == "__main__":
    test_text = "Tesla makes great electric cars with excellent performance and innovative technology."
    test_keywords = ["Tesla", "electric car"]
    
    result = analyze_brand_mentions(test_text, test_keywords)
    print("Analysis result:")
    print(json.dumps(result, indent=2))


# utils/report_generator.py
import json
from datetime import datetime
from typing import Dict, List, Any

def generate_performance_report(analysis_data: Dict[str, Any]) -> str:
    """Generate a comprehensive performance report with organic metrics"""
    
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract key metrics
    ai_responses = analysis_data.get("ai_responses", {})
    analysis = analysis_data.get("analysis", {})
    brand_config = analysis_data.get("brand_config", {})
    
    # Get new metrics
    total_queries = analysis.get("total_responses", 0)
    total_mentions = analysis.get("total_mentions", 0)
    total_organic_mentions = analysis.get("total_organic_mentions", 0)
    organic_mention_rate = analysis.get("organic_mention_rate", 0)
    avg_sentiment = analysis.get("avg_sentiment", 0)
    category_breakdown = analysis.get("category_breakdown", {})
    
    # Calculate platform-specific metrics
    platform_performance = {}
    for platform, responses in ai_responses.items():
        mentions_count = 0
        organic_mentions_count = 0
        total_sentiment = 0
        sentiment_count = 0
        
        for response in responses:
            if response.get("analysis"):
                mentions_count += response["analysis"].get("mentions_found", 0)
                if response["analysis"].get("organic_mention", False):
                    organic_mentions_count += response["analysis"].get("mentions_found", 0)
                
                sentiment_score = response["analysis"].get("sentiment_score", 0)
                if sentiment_score != 0:
                    total_sentiment += sentiment_score
                    sentiment_count += 1
        
        avg_sentiment_platform = total_sentiment / sentiment_count if sentiment_count > 0 else 0
        platform_performance[platform] = {
            "total_responses": len(responses),
            "total_mentions": mentions_count,
            "organic_mentions": organic_mentions_count,
            "avg_sentiment": round(avg_sentiment_platform, 2),
            "organic_rate": round(organic_mentions_count / len(responses) * 100, 1) if responses else 0
        }
    
    # Generate HTML report
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Brand Intelligence Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
            .metric {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
            .platform {{ background-color: #fff; padding: 15px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .positive {{ color: #4CAF50; font-weight: bold; }}
            .negative {{ color: #f44336; font-weight: bold; }}
            .neutral {{ color: #ff9800; font-weight: bold; }}
            .organic-highlight {{ background-color: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .category-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }}
            .category-card {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .raw-response {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }}
            .insight-box {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Brand Intelligence Report</h1>
            <p><strong>Brand:</strong> {brand_config.get('name', 'Unknown')}</p>
            <p><strong>Industry:</strong> {brand_config.get('industry', 'Unknown')}</p>
            <p><strong>Generated:</strong> {report_time}</p>
        </div>
        
        <div class="organic-highlight">
            <h2>🎯 Key Performance Metrics</h2>
            <p><strong>Total Queries Processed:</strong> {total_queries}</p>
            <p><strong>Total Brand Mentions:</strong> {total_mentions}</p>
            <p><strong>🌟 Organic Mentions:</strong> {total_organic_mentions} (mentions in queries without your brand name)</p>
            <p><strong>🌟 Organic Mention Rate:</strong> {organic_mention_rate:.1%}</p>
            <p><strong>Average Sentiment:</strong> {avg_sentiment:.2f} (-1 to 1 scale)</p>
        </div>
        
        <div class="insight-box">
            <h3>💡 Key Insight</h3>
    """
    
    if organic_mention_rate == 0:
        html_report += f"""
            <p><strong>No organic visibility detected.</strong> Your brand doesn't appear when users ask generic questions about {brand_config.get('industry', 'your industry')}. This suggests limited AI search authority.</p>
        """
    elif organic_mention_rate < 0.1:
        html_report += f"""
            <p><strong>Low organic visibility ({organic_mention_rate:.1%}).</strong> Your brand occasionally appears in category searches, but there's significant room for improvement in AI search authority.</p>
        """
    else:
        html_report += f"""
            <p><strong>Good organic visibility ({organic_mention_rate:.1%})!</strong> Your brand appears when users explore the category without mentioning you directly. This indicates strong AI search authority.</p>
        """
    
    html_report += """
        </div>
        
        <h2>📊 Query Category Performance</h2>
        <div class="category-grid">
    """
    
    # Add category breakdown
    for category, metrics in category_breakdown.items():
        total = metrics.get('total', 0)
        mentions = metrics.get('mentions', 0)
        organic = metrics.get('organic_mentions', 0)
        
        if total > 0:
            organic_rate = (organic / total) * 100 if total > 0 else 0
            category_display = category.replace('_', ' ').title()
            
            html_report += f"""
            <div class="category-card">
                <h4>{category_display}</h4>
                <p><strong>Queries:</strong> {total}</p>
                <p><strong>Total Mentions:</strong> {mentions}</p>
                <p><strong>Organic Mentions:</strong> {organic}</p>
                <p><strong>Organic Rate:</strong> {organic_rate:.1f}%</p>
            </div>
            """
    
    html_report += """
        </div>
        
        <h2>🤖 Platform Performance</h2>
    """
    
    for platform, metrics in platform_performance.items():
        sentiment_class = "positive" if metrics["avg_sentiment"] > 0.2 else "negative" if metrics["avg_sentiment"] < -0.2 else "neutral"
        
        html_report += f"""
        <div class="platform">
            <h3>{platform.upper()}</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                <div><strong>Responses:</strong> {metrics["total_responses"]}</div>
                <div><strong>Total Mentions:</strong> {metrics["total_mentions"]}</div>
                <div><strong>Organic Mentions:</strong> {metrics["organic_mentions"]}</div>
                <div><strong>Organic Rate:</strong> {metrics["organic_rate"]}%</div>
                <div><strong>Avg Sentiment:</strong> <span class="{sentiment_class}">{metrics["avg_sentiment"]}</span></div>
            </div>
        </div>
        """
    
    # Add recent mentions table
    html_report += """
        <h2>📝 Recent Brand Mentions</h2>
        <table>
            <tr>
                <th>Platform</th>
                <th>Query Category</th>
                <th>Query</th>
                <th>Context</th>
                <th>Type</th>
                <th>Sentiment</th>
            </tr>
    """
    
    # Show recent mentions from analysis
    mention_count = 0
    for platform, responses in ai_responses.items():
        for response in responses:
            if response.get("analysis") and response["analysis"].get("mentions"):
                for mention in response["analysis"]["mentions"][:1]:  # 1 per response
                    if mention_count >= 15:  # Limit total mentions shown
                        break
                    
                    analysis = response["analysis"]
                    category = analysis.get("query_category", "unknown")
                    sentiment_class = "positive" if analysis["sentiment_score"] > 0.2 else "negative" if analysis["sentiment_score"] < -0.2 else "neutral"
                    mention_type = "Organic" if analysis.get("organic_mention", False) else "Direct"
                    
                    html_report += f"""
                    <tr>
                        <td>{platform.upper()}</td>
                        <td>{category.replace('_', ' ').title()}</td>
                        <td>{response['query'][:60]}...</td>
                        <td>{mention['context'][:100]}...</td>
                        <td><strong>{mention_type}</strong></td>
                        <td><span class="{sentiment_class}">{analysis["sentiment_label"]}</span></td>
                    </tr>
                    """
                    mention_count += 1
                if mention_count >= 15:
                    break
        if mention_count >= 15:
            break
    
    html_report += """
        </table>
        
        <h2>🔍 Raw AI Responses Sample</h2>
        <p>Sample of actual AI responses for transparency and verification:</p>
    """
    
    # Add sample raw responses
    response_count = 0
    for platform, responses in ai_responses.items():
        for response in responses[:3]:  # First 3 responses per platform
            if response.get("status") == "success":
                category = response.get("category", "unknown")
                query = response.get("query", "Unknown query")
                ai_response = response.get("response", "No response")
                
                html_report += f"""
                <div class="platform">
                    <h4>{platform.upper()} - {category.replace('_', ' ').title()}</h4>
                    <p><strong>Query:</strong> {query}</p>
                    <div class="raw-response">
                        <strong>AI Response:</strong><br>
                        {ai_response[:500]}{'...' if len(ai_response) > 500 else ''}
                    </div>
                </div>
                """
                response_count += 1
                if response_count >= 6:  # Limit to 6 total samples
                    break
        if response_count >= 6:
            break
    
    html_report += """
        <div class="metric">
            <h2>💡 Strategic Recommendations</h2>
            <ul>
    """
    
    # Add improved recommendations based on organic performance
    if total_organic_mentions == 0:
        html_report += """
                <li><strong>Critical:</strong> Create authoritative content for category exploration queries. You need to establish thought leadership in your industry.</li>
                <li><strong>High Priority:</strong> Develop comprehensive FAQ content that answers common questions in your field.</li>
                <li><strong>Medium Priority:</strong> Build industry expertise content that AI systems can reference when users ask generic questions.</li>
        """
    elif organic_mention_rate < 0.1:
        html_report += """
                <li><strong>High Priority:</strong> Expand your content marketing to cover more category-based topics and comparisons.</li>
                <li><strong>Medium Priority:</strong> Create more educational content that positions you as an industry authority.</li>
        """
    else:
        html_report += """
                <li><strong>Maintain:</strong> Continue your content strategy as you have good organic visibility!</li>
                <li><strong>Optimize:</strong> Focus on improving sentiment and context of mentions.</li>
        """
    
    # Category-specific recommendations
    for category, metrics in category_breakdown.items():
        if metrics.get('total', 0) > 0 and metrics.get('organic_mentions', 0) == 0:
            category_name = category.replace('_', ' ')
            html_report += f"""
                <li><strong>Focus Area:</strong> No organic mentions in {category_name} queries. Create content specifically targeting this search intent.</li>
            """
    
    html_report += """
            </ul>
        </div>
        
        <div class="metric">
            <p><em>This report analyzes how your brand appears in AI-powered search engines when users ask various types of questions. Organic mentions (without your brand name in the query) indicate stronger market authority.</em></p>
        </div>
    </body>
    </html>
    """
    
    return html_report

def save_report(report_html: str, filename: str = None) -> str:
    """Save report to file and return filename"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_brand_report_{timestamp}.html"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_html)
        return filename
    except Exception as e:
        print(f"Error saving report: {e}")
        return ""

if __name__ == "__main__":
    # Test data
    test_data = {
        "brand_config": {"name": "Tesla"},
        "ai_responses": {
            "chatgpt": [
                {
                    "query": "What do you think about electric cars?",
                    "response": "Tesla makes excellent electric vehicles...",
                    "analysis": {
                        "mentions_found": 1,
                        "mentions": [{"keyword": "Tesla", "context": "Tesla makes excellent electric vehicles"}],
                        "sentiment_score": 0.8,
                        "sentiment_label": "positive"
                    }
                }
            ]
        }
    }
    
    report = generate_performance_report(test_data)
    filename = save_report(report)
    print(f"Test report saved as: {filename}")


# utils/database.py
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class SimpleJSONDB:
    """Simple JSON-based database for demo purposes"""
    
    def __init__(self, db_file: str = "ai_optimization_data.json"):
        self.db_file = db_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading database: {e}")
                return self._init_db_structure()
        return self._init_db_structure()
    
    def _init_db_structure(self) -> Dict[str, Any]:
        """Initialize database structure"""
        return {
            "brands": {},
            "queries": [],
            "responses": [],
            "reports": [],
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
    
    def save(self) -> bool:
        """Save data to JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving database: {e}")
            return False
    
    def store_brand_config(self, brand_config: Dict[str, Any]) -> str:
        """Store brand configuration"""
        brand_id = brand_config.get("name", "default").lower().replace(" ", "_")
        brand_config["updated_at"] = datetime.now().isoformat()
        self.data["brands"][brand_id] = brand_config
        self.save()
        return brand_id
    
    def get_brand_config(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """Get brand configuration"""
        return self.data["brands"].get(brand_id)
    
    def store_ai_response(self, response_data: Dict[str, Any]) -> str:
        """Store AI platform response"""
        response_id = f"{response_data['platform']}_{len(self.data['responses'])}"
        response_data["id"] = response_id
        response_data["stored_at"] = datetime.now().isoformat()
        self.data["responses"].append(response_data)
        self.save()
        return response_id
    
    def get_responses_by_platform(self, platform: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get responses for a specific platform"""
        return [r for r in self.data["responses"] if r.get("platform") == platform][-limit:]
    
    def store_report(self, report_data: Dict[str, Any]) -> str:
        """Store generated report"""
        report_id = f"report_{len(self.data['reports'])}"
        report_data["id"] = report_id
        report_data["generated_at"] = datetime.now().isoformat()
        self.data["reports"].append(report_data)
        self.save()
        return report_id
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Get the most recent report"""
        if self.data["reports"]:
            return self.data["reports"][-1]
        return None
    
    def get_historical_data(self, days: int = 30) -> Dict[str, Any]:
        """Get historical data for analysis"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_responses = []
        for response in self.data["responses"]:
            try:
                response_date = datetime.fromisoformat(response.get("stored_at", ""))
                if response_date >= cutoff_date:
                    recent_responses.append(response)
            except:
                continue
        
        return {
            "responses": recent_responses,
            "total_responses": len(recent_responses),
            "date_range": {
                "from": cutoff_date.isoformat(),
                "to": datetime.now().isoformat()
            }
        }

if __name__ == "__main__":
    # Test the database
    db = SimpleJSONDB("test_db.json")
    
    # Test brand config
    brand_config = {
        "name": "Tesla",
        "keywords": ["Tesla", "electric car", "EV"],
        "industry": "automotive"
    }
    brand_id = db.store_brand_config(brand_config)
    print(f"Stored brand config with ID: {brand_id}")
    
    # Test response storage
    test_response = {
        "platform": "chatgpt",
        "query": "What do you think about Tesla?",
        "response": "Tesla is a leading electric vehicle manufacturer...",
        "status": "success"
    }
    response_id = db.store_ai_response(test_response)
    print(f"Stored response with ID: {response_id}")
    
    # Test retrieval
    retrieved_brand = db.get_brand_config(brand_id)
    print(f"Retrieved brand: {retrieved_brand['name']}")
    
    responses = db.get_responses_by_platform("chatgpt")
    print(f"Found {len(responses)} ChatGPT responses")