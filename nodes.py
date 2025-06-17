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
    """Generate categorized queries based on search intent"""
    
    def prep(self, shared):
        """Read brand configuration from shared store"""
        brand_config = shared.get("brand_config", {})
        print(f"Generating strategic queries for: {brand_config.get('name', 'Unknown')}")
        return brand_config
    
    def exec(self, brand_config):
        """Generate categorized queries using search intent framework"""
        brand_name = brand_config.get("name", "")
        keywords = brand_config.get("keywords", [])
        industry = brand_config.get("industry", "")
        
        # Remove brand name from keywords for unbiased queries
        generic_keywords = [k for k in keywords if k.lower() != brand_name.lower()]
        
        prompt = f"""
Generate search queries that real users would ask AI assistants when researching {industry} services.

BRAND: {brand_name}
INDUSTRY: {industry}
SERVICE KEYWORDS: {', '.join(generic_keywords)}

Generate exactly 20 queries across these 4 categories (5 each):

1. CATEGORY EXPLORATION (user exploring the category - NO brand names)
   - "Who are the best [category] in [location]?"
   - "What should I look for when choosing a [service provider]?"
   
2. COMPARISON & RESEARCH (user comparing options - NO specific brand names)
   - "Compare [service providers] in [location]"
   - "What are the top [category] companies?"
   
3. PROBLEM-SOLVING (user has specific needs - NO brand names)
   - "I need [specific service], what are my options in [location]?"
   - "How do I choose between different [service providers]?"
   
4. DIRECT BRAND (user specifically asking about the brand)
   - "What do you know about {brand_name}?"
   - "Tell me about {brand_name} reviews"

CRITICAL RULES:
- Categories 1-3 should NEVER mention {brand_name} specifically
- Use generic terms like "{industry}" instead of brand names
- Focus on user intent, not brand promotion

Output as YAML:
```yaml
category_exploration:
  - "query 1"
  - "query 2"
  - "query 3"
  - "query 4"
  - "query 5"
comparison_research:
  - "query 1"
  - "query 2"
  - "query 3"
  - "query 4"
  - "query 5"
problem_solving:
  - "query 1"
  - "query 2"
  - "query 3"
  - "query 4"
  - "query 5"
direct_brand:
  - "query 1"
  - "query 2"
  - "query 3"
  - "query 4"
  - "query 5"
```"""
        
        response = call_llm(prompt)
        
        try:
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            result = yaml.safe_load(yaml_str)
            
            # Validate structure
            required_categories = ['category_exploration', 'comparison_research', 'problem_solving', 'direct_brand']
            for category in required_categories:
                if category not in result or len(result[category]) != 5:
                    raise ValueError(f"Missing or incomplete category: {category}")
            
            return result
            
        except Exception as e:
            print(f"Error parsing query generation: {e}")
            # Fallback to hardcoded strategic queries
            return {
                "category_exploration": [
                    f"Who are the best {industry} companies?",
                    f"What should I look for when choosing a {industry} company?",
                    f"Top rated {industry} services",
                    f"How to find reliable {industry} providers",
                    f"What are the leading {industry} companies?"
                ],
                "comparison_research": [
                    f"Compare {industry} companies",
                    f"{industry} company reviews and ratings",
                    f"Which {industry} company offers the best value?",
                    f"Local {industry} providers vs national companies",
                    f"How do {industry} prices compare?"
                ],
                "problem_solving": [
                    f"I need {industry} services, what are my options?",
                    f"Best {industry} providers for beginners",
                    f"Affordable {industry} services",
                    f"How long does {industry} typically take?",
                    f"What should I know before hiring {industry} services?"
                ],
                "direct_brand": [
                    f"What do you know about {brand_name}?",
                    f"Tell me about {brand_name} reviews",
                    f"Is {brand_name} a good {industry} company?",
                    f"How does {brand_name} compare to competitors?",
                    f"{brand_name} pricing and services"
                ]
            }
    
    def post(self, shared, prep_res, exec_res):
        """Store categorized queries in shared store"""
        # Flatten all queries for processing but keep category metadata
        all_queries = []
        for category, queries in exec_res.items():
            for query in queries:
                all_queries.append({
                    "query": query,
                    "category": category,
                    "brand_mentioned": shared["brand_config"]["name"].lower() in query.lower()
                })
        
        shared["queries"] = {
            "categorized": exec_res,
            "all_queries": all_queries,
            "total_count": len(all_queries),
            "generated_at": time.time()
        }
        
        print(f"Generated {len(all_queries)} strategically categorized queries")
        return "default"

class MultiPlatformQueryNode(BatchNode):
    """Query multiple AI platforms with generated queries"""
    
    def prep(self, shared):
        """Create query-platform pairs for batch processing"""
        all_queries = shared.get("queries", {}).get("all_queries", [])
        platforms = ["chatgpt", "gemini"]  # As requested, start with these two
        
        # Create all combinations of queries and platforms
        query_platform_pairs = []
        for query_data in all_queries:
            for platform in platforms:
                query_platform_pairs.append({
                    "query": query_data["query"],
                    "category": query_data["category"],
                    "brand_mentioned": query_data["brand_mentioned"],
                    "platform": platform
                })
        
        print(f"Preparing to execute {len(query_platform_pairs)} query-platform combinations")
        return query_platform_pairs
    
    def exec(self, query_platform_pair):
        """Execute a single query on a specific platform"""
        query = query_platform_pair["query"]
        platform = query_platform_pair["platform"]
        category = query_platform_pair["category"]
        brand_mentioned = query_platform_pair["brand_mentioned"]
        
        print(f"Querying {platform} ({category}): {query[:50]}...")
        
        result = None
        if platform == "chatgpt":
            result = query_chatgpt(query)
        elif platform == "gemini":
            result = query_gemini(query)
        else:
            result = {
                "platform": platform,
                "query": query,
                "response": "",
                "status": "error",
                "error": f"Unknown platform: {platform}"
            }
        
        # Add metadata
        result["category"] = category
        result["brand_mentioned_in_query"] = brand_mentioned
        return result
    
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
    """Analyze AI responses with intent-based metrics"""
    
    def prep(self, shared):
        """Prepare all responses for analysis"""
        ai_responses = shared.get("ai_responses", {})
        brand_keywords = shared.get("brand_config", {}).get("keywords", [])
        
        # Flatten all responses with their metadata
        all_responses = []
        for platform, responses in ai_responses.items():
            for response in responses:
                response["brand_keywords"] = brand_keywords
                all_responses.append(response)
        
        print(f"Analyzing {len(all_responses)} responses for brand mentions and intent")
        return all_responses
    
    def exec(self, response_data):
        """Analyze a single response for brand mentions with category context"""
        if response_data.get("status") != "success":
            return response_data  # Skip failed responses
        
        text = response_data.get("response", "")
        brand_keywords = response_data.get("brand_keywords", [])
        category = response_data.get("category", "unknown")
        brand_mentioned_in_query = response_data.get("brand_mentioned_in_query", False)
        
        # Analyze the response text
        analysis = analyze_brand_mentions(text, brand_keywords)
        
        # Enhanced analysis based on query category
        analysis["query_category"] = category
        analysis["brand_mentioned_in_query"] = brand_mentioned_in_query
        analysis["organic_mention"] = False
        
        # Determine if mention is "organic" (query didn't include brand name)
        if analysis.get("mentions_found", 0) > 0:
            analysis["organic_mention"] = not brand_mentioned_in_query
        
        # Add analysis to response data
        response_data["analysis"] = analysis
        
        return response_data
    
    def post(self, shared, prep_res, exec_res_list):
        """Create sophisticated analysis summary with organic metrics"""
        # Reorganize analyzed responses back by platform
        ai_responses = {"chatgpt": [], "gemini": []}
        
        # Calculate intent-based metrics
        category_metrics = {
            "category_exploration": {"total": 0, "mentions": 0, "organic_mentions": 0},
            "comparison_research": {"total": 0, "mentions": 0, "organic_mentions": 0},
            "problem_solving": {"total": 0, "mentions": 0, "organic_mentions": 0},
            "direct_brand": {"total": 0, "mentions": 0, "organic_mentions": 0}
        }
        
        total_mentions = 0
        total_organic_mentions = 0
        total_responses = len(exec_res_list)
        sentiment_scores = []
        
        for response in exec_res_list:
            platform = response.get("platform")
            if platform in ai_responses:
                ai_responses[platform].append(response)
                
                # Calculate category-specific metrics
                if response.get("analysis"):
                    analysis = response["analysis"]
                    category = analysis.get("query_category", "unknown")
                    
                    if category in category_metrics:
                        category_metrics[category]["total"] += 1
                        
                        mentions = analysis.get("mentions_found", 0)
                        if mentions > 0:
                            category_metrics[category]["mentions"] += mentions
                            total_mentions += mentions
                            
                            if analysis.get("organic_mention", False):
                                category_metrics[category]["organic_mentions"] += mentions
                                total_organic_mentions += mentions
                    
                    sentiment_score = analysis.get("sentiment_score", 0)
                    if sentiment_score != 0:
                        sentiment_scores.append(sentiment_score)
        
        # Calculate sophisticated metrics
        organic_mention_rate = (total_organic_mentions / total_responses) if total_responses > 0 else 0
        
        # Store updated responses and advanced analysis
        shared["ai_responses"] = ai_responses
        shared["analysis"] = {
            "total_mentions": total_mentions,
            "total_organic_mentions": total_organic_mentions,
            "organic_mention_rate": organic_mention_rate,
            "total_responses": total_responses,
            "avg_sentiment": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
            "category_breakdown": category_metrics,
            "analyzed_at": time.time()
        }
        
        print(f"Analysis complete:")
        print(f"  Total mentions: {total_mentions}")
        print(f"  Organic mentions: {total_organic_mentions}")
        print(f"  Organic mention rate: {organic_mention_rate:.1%}")
        
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
        total_organic_mentions = analysis.get("total_organic_mentions", 0)
        avg_sentiment = analysis.get("avg_sentiment", 0)
        organic_mention_rate = analysis.get("organic_mention_rate", 0)
        
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
- Organic mentions: {total_organic_mentions}
- Organic mention rate: {organic_mention_rate:.1%}
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
                    "status": "needs_improvement" if total_organic_mentions < 3 else "good",
                    "summary": f"Found {total_mentions} mentions with {total_organic_mentions} organic ({organic_mention_rate:.1%})"
                },
                "recommendations": [
                    {
                        "priority": "high",
                        "action": "Create more authoritative content",
                        "rationale": "Low organic mention rate suggests limited AI visibility"
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
                "total_organic_mentions": report_data["analysis"].get("total_organic_mentions", 0),
                "avg_sentiment": report_data["analysis"].get("avg_sentiment", 0),
                "organic_mention_rate": report_data["analysis"].get("organic_mention_rate", 0),
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