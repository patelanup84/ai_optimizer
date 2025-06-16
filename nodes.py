# nodes.py
from pocketflow import Node, BatchNode
from utils.call_llm import call_llm
from utils.ai_platforms import query_chatgpt, query_gemini
from utils.text_analysis import analyze_brand_mentions
from utils.report_generator import generate_performance_report, save_report
from utils.database import SimpleJSONDB
import json
import yaml
import time

class QueryGeneratorNode(Node):
    """Generate relevant search queries for brand monitoring"""
    
    def prep(self, shared):
        """Read brand configuration from shared store"""
        brand_config = shared.get("brand_config", {})
        print(f"Generating queries for brand: {brand_config.get('name', 'Unknown')}")
        return brand_config
    
    def exec(self, brand_config):
        """Generate diverse, relevant search queries using LLM"""
        brand_name = brand_config.get("name", "")
        keywords = brand_config.get("keywords", [])
        industry = brand_config.get("industry", "")
        
        prompt = f"""
Generate 10 diverse search queries that users might ask AI assistants about the brand "{brand_name}" in the {industry} industry.

Brand keywords: {', '.join(keywords)}

The queries should cover different aspects like:
- Product/service quality
- Comparisons with competitors  
- Customer reviews/opinions
- Industry leadership
- Innovation/technology
- Pricing and value
- Customer service
- General brand awareness

Output as YAML list:
```yaml
queries:
  - "query 1"
  - "query 2"
  # ... etc
```"""
        
        response = call_llm(prompt)
        
        try:
            # Extract YAML from response
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            result = yaml.safe_load(yaml_str)
            queries = result.get("queries", [])
            
            # Validate we got actual queries
            if not queries or len(queries) < 5:
                raise ValueError("Not enough queries generated")
                
            return queries
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Fallback to hardcoded queries
            return [
                f"What do you know about {brand_name}?",
                f"How does {brand_name} compare to competitors?",
                f"What are the pros and cons of {brand_name}?",
                f"Is {brand_name} a good company?",
                f"What is {brand_name} known for?",
                f"Tell me about {brand_name} products",
                f"What do customers think about {brand_name}?",
                f"Why should I choose {brand_name}?"
            ]
    
    def post(self, shared, prep_res, exec_res):
        """Store generated queries in shared store"""
        shared["queries"] = {
            "generated": exec_res,
            "count": len(exec_res),
            "generated_at": time.time()
        }
        print(f"Generated {len(exec_res)} queries for monitoring")
        return "default"

class MultiPlatformQueryNode(BatchNode):
    """Query multiple AI platforms with generated queries"""
    
    def prep(self, shared):
        """Create query-platform pairs for batch processing"""
        queries = shared.get("queries", {}).get("generated", [])
        platforms = ["chatgpt", "gemini"]  # As requested, start with these two
        
        # Create all combinations of queries and platforms
        query_platform_pairs = []
        for query in queries:
            for platform in platforms:
                query_platform_pairs.append({
                    "query": query,
                    "platform": platform
                })
        
        print(f"Preparing to execute {len(query_platform_pairs)} query-platform combinations")
        return query_platform_pairs
    
    def exec(self, query_platform_pair):
        """Execute a single query on a specific platform"""
        query = query_platform_pair["query"]
        platform = query_platform_pair["platform"]
        
        print(f"Querying {platform} with: {query[:50]}...")
        
        if platform == "chatgpt":
            return query_chatgpt(query)
        elif platform == "gemini":
            return query_gemini(query)
        else:
            return {
                "platform": platform,
                "query": query,
                "response": "",
                "status": "error",
                "error": f"Unknown platform: {platform}"
            }
    
    def post(self, shared, prep_res, exec_res_list):
        """Organize responses by platform and store in shared store"""
        ai_responses = {"chatgpt": [], "gemini": []}
        
        for response in exec_res_list:
            platform = response.get("platform")
            if platform in ai_responses:
                ai_responses[platform].append(response)
        
        shared["ai_responses"] = ai_responses
        
        total_responses = sum(len(responses) for responses in ai_responses.values())
        successful_responses = sum(1 for response in exec_res_list if response.get("status") == "success")
        
        print(f"Collected {total_responses} responses ({successful_responses} successful)")
        
        return "default"

class ResponseAnalysisNode(BatchNode):
    """Analyze AI responses for brand mentions and sentiment"""
    
    def prep(self, shared):
        """Prepare all responses for analysis"""
        ai_responses = shared.get("ai_responses", {})
        brand_keywords = shared.get("brand_config", {}).get("keywords", [])
        
        # Flatten all responses with their platform info
        all_responses = []
        for platform, responses in ai_responses.items():
            for response in responses:
                response["brand_keywords"] = brand_keywords
                all_responses.append(response)
        
        print(f"Analyzing {len(all_responses)} responses for brand mentions")
        return all_responses
    
    def exec(self, response_data):
        """Analyze a single response for brand mentions"""
        if response_data.get("status") != "success":
            return response_data  # Skip failed responses
        
        text = response_data.get("response", "")
        brand_keywords = response_data.get("brand_keywords", [])
        
        # Analyze the response text
        analysis = analyze_brand_mentions(text, brand_keywords)
        
        # Add analysis to response data
        response_data["analysis"] = analysis
        
        return response_data
    
    def post(self, shared, prep_res, exec_res_list):
        """Update responses with analysis and create summary"""
        # Reorganize analyzed responses back by platform
        ai_responses = {"chatgpt": [], "gemini": []}
        
        total_mentions = 0
        total_sentiment = 0
        sentiment_count = 0
        
        for response in exec_res_list:
            platform = response.get("platform")
            if platform in ai_responses:
                ai_responses[platform].append(response)
                
                # Aggregate metrics
                if response.get("analysis"):
                    total_mentions += response["analysis"].get("mentions_found", 0)
                    sentiment_score = response["analysis"].get("sentiment_score", 0)
                    total_sentiment += sentiment_score
                    sentiment_count += 1
        
        # Update shared store with analyzed responses
        shared["ai_responses"] = ai_responses
        
        # Create analysis summary
        shared["analysis"] = {
            "total_mentions": total_mentions,
            "avg_sentiment": total_sentiment / sentiment_count if sentiment_count > 0 else 0,
            "total_responses": len(exec_res_list),
            "mention_rate": total_mentions / len(exec_res_list) if exec_res_list else 0,
            "analyzed_at": time.time()
        }
        
        print(f"Analysis complete: {total_mentions} mentions found, avg sentiment: {shared['analysis']['avg_sentiment']:.2f}")
        
        return "default"

class OptimizationAgentNode(Node):
    """AI agent that analyzes performance and generates recommendations"""
    
    def prep(self, shared):
        """Gather all analysis data for the agent"""
        analysis = shared.get("analysis", {})
        ai_responses = shared.get("ai_responses", {})
        brand_config = shared.get("brand_config", {})
        
        return {
            "analysis": analysis,
            "ai_responses": ai_responses,
            "brand_config": brand_config
        }
    
    def exec(self, analysis_data):
        """Generate optimization recommendations using AI agent"""
        analysis = analysis_data["analysis"]
        brand_config = analysis_data["brand_config"]
        ai_responses = analysis_data["ai_responses"]
        
        # Prepare context for the optimization agent
        brand_name = brand_config.get("name", "Unknown")
        total_mentions = analysis.get("total_mentions", 0)
        avg_sentiment = analysis.get("avg_sentiment", 0)
        mention_rate = analysis.get("mention_rate", 0)
        
        # Get sample mentions for context
        sample_mentions = []
        for platform, responses in ai_responses.items():
            for response in responses:
                if response.get("analysis", {}).get("mentions"):
                    for mention in response["analysis"]["mentions"][:2]:
                        sample_mentions.append({
                            "platform": platform,
                            "query": response["query"],
                            "context": mention["context"],
                            "sentiment": response["analysis"]["sentiment_label"]
                        })
                if len(sample_mentions) >= 5:
                    break
            if len(sample_mentions) >= 5:
                break
        
        prompt = f"""
You are an AI brand optimization expert. Analyze the following brand performance data and provide actionable recommendations.

BRAND: {brand_name}
INDUSTRY: {brand_config.get('industry', 'Unknown')}

PERFORMANCE METRICS:
- Total mentions found: {total_mentions}
- Mention rate: {mention_rate:.1%}
- Average sentiment: {avg_sentiment:.2f} (-1 to 1 scale)
- Total responses analyzed: {analysis.get('total_responses', 0)}

SAMPLE MENTIONS:
{json.dumps(sample_mentions, indent=2)}

Based on this data, provide:
1. Performance assessment (good/needs improvement)
2. Top 3 specific recommendations for improvement
3. Content strategy suggestions
4. Potential risks or opportunities

Output as YAML:
```yaml
assessment:
  overall_score: # 1-10 scale
  status: # "excellent", "good", "needs_improvement", or "poor"
  summary: "brief assessment"

recommendations:
  - priority: "high/medium/low"
    action: "specific action to take"
    rationale: "why this matters"
  - priority: "high/medium/low"
    action: "specific action to take"
    rationale: "why this matters"
  - priority: "high/medium/low"
    action: "specific action to take"
    rationale: "why this matters"

content_strategy:
  - type: "content type (blog, FAQ, etc.)"
    topic: "suggested topic"
    goal: "what this achieves"

risks_opportunities:
  risks:
    - "potential risk"
  opportunities:
    - "potential opportunity"
```"""
        
        response = call_llm(prompt)
        
        try:
            # Extract YAML from response
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            recommendations = yaml.safe_load(yaml_str)
            return recommendations
        except Exception as e:
            print(f"Error parsing agent response: {e}")
            # Return fallback recommendations
            return {
                "assessment": {
                    "overall_score": 5,
                    "status": "needs_improvement" if total_mentions < 3 else "good",
                    "summary": f"Found {total_mentions} mentions with {avg_sentiment:.2f} avg sentiment"
                },
                "recommendations": [
                    {
                        "priority": "high",
                        "action": "Create more authoritative content",
                        "rationale": "Low mention rate suggests limited AI visibility"
                    }
                ],
                "content_strategy": [
                    {
                        "type": "FAQ",
                        "topic": f"Common questions about {brand_name}",
                        "goal": "Improve AI response accuracy"
                    }
                ],
                "risks_opportunities": {
                    "risks": ["Limited AI visibility"],
                    "opportunities": ["Untapped AI search traffic"]
                }
            }
    
    def post(self, shared, prep_res, exec_res):
        """Store recommendations and determine next action"""
        shared["recommendations"] = exec_res
        
        # Determine action based on assessment
        assessment = exec_res.get("assessment", {})
        status = assessment.get("status", "needs_improvement")
        
        print(f"Optimization analysis complete. Status: {status}")
        print(f"Generated {len(exec_res.get('recommendations', []))} recommendations")
        
        if status in ["poor", "needs_improvement"]:
            return "needs_attention"
        elif status == "excellent":
            return "performing_well"
        else:
            return "default"

class ReportGeneratorNode(Node):
    """Generate comprehensive performance reports"""
    
    def prep(self, shared):
        """Gather all data for report generation"""
        return {
            "brand_config": shared.get("brand_config", {}),
            "ai_responses": shared.get("ai_responses", {}),
            "analysis": shared.get("analysis", {}),
            "recommendations": shared.get("recommendations", {})
        }
    
    def exec(self, report_data):
        """Generate HTML report"""
        html_report = generate_performance_report(report_data)
        return {
            "html_content": html_report,
            "summary": {
                "total_mentions": report_data["analysis"].get("total_mentions", 0),
                "avg_sentiment": report_data["analysis"].get("avg_sentiment", 0),
                "mention_rate": report_data["analysis"].get("mention_rate", 0),
                "status": report_data["recommendations"].get("assessment", {}).get("status", "unknown")
            }
        }
    
    def post(self, shared, prep_res, exec_res):
        """Save report and update shared store"""
        # Save HTML report to file
        filename = save_report(exec_res["html_content"])
        
        shared["reports"] = {
            "latest_html": exec_res["html_content"],
            "filename": filename,
            "summary": exec_res["summary"],
            "generated_at": time.time()
        }
        
        print(f"Report generated and saved as: {filename}")
        return "default"

class DatabaseStorageNode(Node):
    """Store results in database for historical tracking"""
    
    def prep(self, shared):
        """Gather all data for storage"""
        return shared
    
    def exec(self, shared_data):
        """Store data in database"""
        db = SimpleJSONDB()
        
        # Store brand config
        brand_config = shared_data.get("brand_config", {})
        if brand_config:
            brand_id = db.store_brand_config(brand_config)
        
        # Store all AI responses
        ai_responses = shared_data.get("ai_responses", {})
        stored_responses = []
        
        for platform, responses in ai_responses.items():
            for response in responses:
                response_id = db.store_ai_response(response)
                stored_responses.append(response_id)
        
        # Store report data
        if shared_data.get("reports"):
            report_data = {
                "summary": shared_data["reports"]["summary"],
                "filename": shared_data["reports"]["filename"],
                "analysis": shared_data.get("analysis", {}),
                "recommendations": shared_data.get("recommendations", {})
            }
            report_id = db.store_report(report_data)
        
        return {
            "brand_id": brand_id if brand_config else None,
            "stored_responses": len(stored_responses),
            "report_stored": bool(shared_data.get("reports"))
        }
    
    def post(self, shared, prep_res, exec_res):
        """Update shared store with storage confirmation"""
        shared["storage"] = exec_res
        print(f"Data stored: {exec_res['stored_responses']} responses, report: {exec_res['report_stored']}")
        return "default"