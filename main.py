import os
import sys
from flow import create_brand_monitoring_flow, create_simple_monitoring_flow
from utils.database import SimpleJSONDB

def setup_environment():
    """Check and setup required environment variables"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for ChatGPT queries",
        "GOOGLE_API_KEY": "Google API key for Gemini queries (optional, will fallback to OpenAI)"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            if var == "GOOGLE_API_KEY":
                print(f"Warning: {var} not set - {description}")
            else:
                missing_vars.append(f"{var}: {description}")
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables and try again.")
        return False
    
    return True

def get_brand_config():
    """Get brand configuration from user input"""
    print("\n=== AI Brand Optimization Tool ===")
    print("Let's set up your competitive brand monitoring configuration.\n")
    
    brand_name = input("Enter your brand name: ").strip()
    if not brand_name:
        print("Brand name is required!")
        return None
    
    print(f"\nEnter service/product keywords (NOT including '{brand_name}'):")
    print("These should be generic terms your customers might search for.")
    print(f"Examples: 'home builder', 'calgary', 'custom homes', 'residential construction'")
    print("Press Enter after each keyword, empty line to finish:")
    
    keywords = [brand_name]  # Always include brand name
    while True:
        keyword = input("Keyword: ").strip()
        if not keyword:
            break
        if keyword.lower() != brand_name.lower() and keyword not in keywords:
            keywords.append(keyword)
    
    industry = input(f"\nWhat industry/category is {brand_name} in?: ").strip()
    if not industry:
        industry = "general services"
    
    return {
        "name": brand_name,
        "keywords": keywords,
        "industry": industry
    }

def print_results_summary(shared):
    """Print a summary of the monitoring results with organic metrics"""
    print("\n" + "="*70)
    print("AI BRAND OPTIMIZATION RESULTS")
    print("="*70)
    
    # Basic metrics
    analysis = shared.get("analysis", {})
    brand_config = shared.get("brand_config", {})
    
    print(f"Brand: {brand_config.get('name', 'Unknown')}")
    print(f"Industry: {brand_config.get('industry', 'Unknown')}")
    print(f"Keywords monitored: {', '.join(brand_config.get('keywords', []))}")
    print(f"Total responses analyzed: {analysis.get('total_responses', 0)}")
    print(f"Total mentions found: {analysis.get('total_mentions', 0)}")
    print(f"🎯 Organic mentions: {analysis.get('total_organic_mentions', 0)}")
    print(f"🎯 Organic mention rate: {analysis.get('organic_mention_rate', 0):.1%}")
    print(f"   (mentions in queries that didn't include your brand name)")
    print(f"Average sentiment: {analysis.get('avg_sentiment', 0):.2f} (-1 to 1 scale)")
    
    # Category breakdown
    category_breakdown = analysis.get('category_breakdown', {})
    if category_breakdown:
        print(f"\n📊 QUERY CATEGORY PERFORMANCE:")
        for category, metrics in category_breakdown.items():
            total = metrics.get('total', 0)
            mentions = metrics.get('mentions', 0)
            organic = metrics.get('organic_mentions', 0)
            if total > 0:
                print(f"  {category.replace('_', ' ').title()}:")
                print(f"    Queries: {total} | Total Mentions: {mentions} | Organic: {organic}")
    
    # Platform breakdown
    ai_responses = shared.get("ai_responses", {})
    print(f"\nPlatform breakdown:")
    for platform, responses in ai_responses.items():
        total_mentions = sum(r.get("analysis", {}).get("mentions_found", 0) for r in responses)
        organic_mentions = sum(r.get("analysis", {}).get("mentions_found", 0) for r in responses 
                              if r.get("analysis", {}).get("organic_mention", False))
        print(f"  {platform.upper()}: {len(responses)} responses, {total_mentions} mentions ({organic_mentions} organic)")
    
    # Top recommendations
    recommendations = shared.get("recommendations", {})
    if recommendations.get("recommendations"):
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(recommendations["recommendations"][:3], 1):
            print(f"  {i}. [{rec.get('priority', 'medium').upper()}] {rec.get('action', 'N/A')}")
    
    # Report file
    reports = shared.get("reports", {})
    if reports.get("filename"):
        print(f"\nDetailed report saved as: {reports['filename']}")
        print("Open this file in your browser to view the full analysis.")
    
    # Key insights
    organic_rate = analysis.get('organic_mention_rate', 0)
    if organic_rate == 0:
        print(f"\n💡 KEY INSIGHT: No organic mentions found. Your brand isn't appearing")
        print(f"   when users ask generic questions about {brand_config.get('industry', 'your industry')}.")
    elif organic_rate < 0.1:
        print(f"\n💡 KEY INSIGHT: Low organic visibility ({organic_rate:.1%}). Consider creating")
        print(f"   authoritative content for category-based searches.")
    else:
        print(f"\n💡 KEY INSIGHT: Good organic visibility ({organic_rate:.1%})! Your brand")
        print(f"   appears when users explore the category without mentioning you directly.")

def run_monitoring_session():
    """Run a complete brand monitoring session"""
    print("Starting brand monitoring session...")
    
    # Get brand configuration
    brand_config = get_brand_config()
    if not brand_config:
        return False
    
    # Create shared data store
    shared = {
        "brand_config": brand_config
    }
    
    print(f"\nStarting monitoring for '{brand_config['name']}'...")
    print("This may take a few minutes as we query multiple AI platforms...\n")
    
    try:
        # Create and run the monitoring flow
        flow = create_brand_monitoring_flow()
        flow.run(shared)
        
        # Print results summary
        print_results_summary(shared)
        
        return True
        
    except Exception as e:
        print(f"\nError during monitoring: {e}")
        print("You may need to check your API keys or network connection.")
        return False

def view_historical_data():
    """View historical monitoring data"""
    db = SimpleJSONDB()
    
    print("\n=== Historical Data ===")
    
    # Show stored brands
    brands = db.data.get("brands", {})
    if not brands:
        print("No historical data found. Run a monitoring session first.")
        return
    
    print("Stored brands:")
    for brand_id, brand_data in brands.items():
        print(f"  - {brand_data.get('name', brand_id)} (updated: {brand_data.get('updated_at', 'unknown')})")
    
    # Show recent reports
    reports = db.data.get("reports", [])
    if reports:
        print(f"\nTotal reports generated: {len(reports)}")
        latest_report = reports[-1]
        print(f"Latest report generated: {latest_report.get('generated_at', 'unknown')}")
        
        if latest_report.get("summary"):
            summary = latest_report["summary"]
            print(f"  - Mentions: {summary.get('total_mentions', 0)}")
            print(f"  - Sentiment: {summary.get('avg_sentiment', 0):.2f}")
            print(f"  - Status: {summary.get('status', 'unknown')}")

def main():
    """Main application entry point"""
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Main menu loop
    while True:
        print("\n" + "="*50)
        print("AI Brand Optimization Tool")
        print("="*50)
        print("1. Run brand monitoring session")
        print("2. View historical data")
        print("3. Test connection (quick test)")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == "1":
            success = run_monitoring_session()
            if success:
                input("\nPress Enter to continue...")
        
        elif choice == "2":
            view_historical_data()
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            print("\nTesting AI platform connections...")
            try:
                from utils.ai_platforms import query_chatgpt, query_gemini
                
                test_query = "What is artificial intelligence?"
                
                print("Testing ChatGPT...")
                result1 = query_chatgpt(test_query)
                print(f"ChatGPT: {result1['status']}")
                
                print("Testing Gemini...")
                result2 = query_gemini(test_query)
                print(f"Gemini: {result2['status']}")
                
                if result1['status'] == 'success' or result2['status'] in ['success', 'fallback']:
                    print("✅ Connection test successful!")
                else:
                    print("❌ Connection test failed. Check your API keys.")
                    
            except Exception as e:
                print(f"❌ Connection test failed: {e}")
            
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()
