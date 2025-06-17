# test_category_breakdown.py
import sys
import os
import json
from pprint import pprint

# Add the current directory to path so we can import our modules
sys.path.append('.')

def test_query_generation():
    """Test if QueryGeneratorNode generates categorized queries"""
    print("="*60)
    print("1. TESTING QUERY GENERATION")
    print("="*60)
    
    try:
        from nodes import QueryGeneratorNode
        
        # Create test brand config
        brand_config = {
            "name": "Test Company",
            "keywords": ["Test Company", "consulting", "services", "business"],
            "industry": "consulting"
        }
        
        # Create shared store
        shared = {"brand_config": brand_config}
        
        # Create and run QueryGeneratorNode
        query_node = QueryGeneratorNode()
        query_node.run(shared)
        
        print(f"✅ QueryGeneratorNode completed successfully")
        
        # Check the output structure
        queries = shared.get("queries", {})
        print(f"\nQueries structure:")
        print(f"  - total_count: {queries.get('total_count', 'MISSING')}")
        print(f"  - categorized keys: {list(queries.get('categorized', {}).keys())}")
        print(f"  - all_queries length: {len(queries.get('all_queries', []))}")
        
        # Show sample queries from each category
        categorized = queries.get("categorized", {})
        for category, query_list in categorized.items():
            print(f"\n{category.upper()}:")
            for i, query in enumerate(query_list[:2], 1):  # Show first 2
                print(f"  {i}. {query}")
        
        # Check all_queries structure
        all_queries = queries.get("all_queries", [])
        if all_queries:
            print(f"\nSample all_queries item:")
            pprint(all_queries[0])
            
            # Count by category
            category_counts = {}
            for q in all_queries:
                cat = q.get("category", "unknown")
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            print(f"\nCategory distribution:")
            for cat, count in category_counts.items():
                print(f"  {cat}: {count} queries")
        
        return shared
        
    except Exception as e:
        print(f"❌ QueryGeneratorNode failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_platform_querying(shared):
    """Test if MultiPlatformQueryNode preserves category metadata"""
    print("\n" + "="*60)
    print("2. TESTING PLATFORM QUERYING")
    print("="*60)
    
    if not shared:
        print("❌ Skipping - no shared data from previous test")
        return None
    
    try:
        from nodes import MultiPlatformQueryNode
        
        # Create and run MultiPlatformQueryNode
        platform_node = MultiPlatformQueryNode()
        
        # Just test the prep step to see the structure
        query_platform_pairs = platform_node.prep(shared)
        
        print(f"✅ MultiPlatformQueryNode prep completed")
        print(f"  - Total query-platform pairs: {len(query_platform_pairs)}")
        
        # Show sample pairs
        if query_platform_pairs:
            print(f"\nSample query-platform pairs:")
            for i, pair in enumerate(query_platform_pairs[:4], 1):
                print(f"  {i}. Platform: {pair.get('platform')}")
                print(f"     Category: {pair.get('category')}")
                print(f"     Brand mentioned: {pair.get('brand_mentioned')}")
                print(f"     Query: {pair.get('query', '')[:50]}...")
                print()
        
        # Simulate some responses (don't actually call APIs for testing)
        print("Creating mock AI responses for testing...")
        ai_responses = {"chatgpt": [], "gemini": []}
        
        for pair in query_platform_pairs[:4]:  # Just test first 4
            mock_response = {
                "platform": pair["platform"],
                "query": pair["query"],
                "category": pair["category"],
                "brand_mentioned_in_query": pair["brand_mentioned"],
                "response": f"This is a mock AI response that mentions {shared['brand_config']['name']} in the context.",
                "status": "success"
            }
            ai_responses[pair["platform"]].append(mock_response)
        
        shared["ai_responses"] = ai_responses
        
        print(f"✅ Created mock responses:")
        for platform, responses in ai_responses.items():
            print(f"  {platform}: {len(responses)} responses")
            for resp in responses:
                print(f"    - Category: {resp.get('category')}, Brand in query: {resp.get('brand_mentioned_in_query')}")
        
        return shared
        
    except Exception as e:
        print(f"❌ MultiPlatformQueryNode failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_response_analysis(shared):
    """Test if ResponseAnalysisNode creates category breakdown"""
    print("\n" + "="*60)
    print("3. TESTING RESPONSE ANALYSIS")
    print("="*60)
    
    if not shared:
        print("❌ Skipping - no shared data from previous test")
        return None
    
    try:
        from nodes import ResponseAnalysisNode
        
        # Create and run ResponseAnalysisNode
        analysis_node = ResponseAnalysisNode()
        analysis_node.run(shared)
        
        print(f"✅ ResponseAnalysisNode completed successfully")
        
        # Check the analysis output
        analysis = shared.get("analysis", {})
        print(f"\nAnalysis structure:")
        for key, value in analysis.items():
            if key != "category_breakdown":
                print(f"  {key}: {value}")
        
        # Focus on category breakdown
        category_breakdown = analysis.get("category_breakdown", {})
        print(f"\nCategory Breakdown:")
        if category_breakdown:
            for category, metrics in category_breakdown.items():
                print(f"  {category}:")
                print(f"    total: {metrics.get('total', 0)}")
                print(f"    mentions: {metrics.get('mentions', 0)}")
                print(f"    organic_mentions: {metrics.get('organic_mentions', 0)}")
        else:
            print("  ❌ Category breakdown is empty!")
        
        # Check individual responses for analysis
        print(f"\nSample response analysis:")
        ai_responses = shared.get("ai_responses", {})
        for platform, responses in ai_responses.items():
            print(f"\n{platform.upper()}:")
            for i, resp in enumerate(responses[:2], 1):
                analysis_data = resp.get("analysis", {})
                print(f"  Response {i}:")
                print(f"    query_category: {analysis_data.get('query_category', 'MISSING')}")
                print(f"    brand_mentioned_in_query: {analysis_data.get('brand_mentioned_in_query', 'MISSING')}")
                print(f"    mentions_found: {analysis_data.get('mentions_found', 0)}")
                print(f"    organic_mention: {analysis_data.get('organic_mention', 'MISSING')}")
        
        return shared
        
    except Exception as e:
        print(f"❌ ResponseAnalysisNode failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_flask_template_data(shared):
    """Test what the Flask template would receive"""
    print("\n" + "="*60)
    print("4. TESTING FLASK TEMPLATE DATA")
    print("="*60)
    
    if not shared:
        print("❌ Skipping - no shared data from previous test")
        return
    
    # Simulate what Flask template receives
    template_data = {
        "brand_config": shared.get("brand_config", {}),
        "analysis": shared.get("analysis", {}),
        "ai_responses": shared.get("ai_responses", {})
    }
    
    print("Flask template data structure:")
    print(f"  brand_config: {template_data['brand_config'].get('name', 'MISSING')}")
    print(f"  analysis keys: {list(template_data['analysis'].keys())}")
    
    # Test the specific template logic
    category_breakdown = template_data['analysis'].get('category_breakdown', {})
    print(f"\nTemplate category breakdown check:")
    print(f"  category_breakdown exists: {bool(category_breakdown)}")
    print(f"  category_breakdown keys: {list(category_breakdown.keys())}")
    
    # Simulate the template loop
    print(f"\nSimulating template loop:")
    if category_breakdown:
        for category, metrics in category_breakdown.items():
            total = metrics.get('total', 0)
            if total > 0:
                print(f"  Would show card for {category}:")
                print(f"    Queries: {total}")
                print(f"    Mentions: {metrics.get('mentions', 0)}")
                print(f"    Organic: {metrics.get('organic_mentions', 0)}")
            else:
                print(f"  Would skip {category} (total = 0)")
    else:
        print("  Would show: 'Category breakdown not available. Using legacy analysis format.'")

def main():
    """Run all tests"""
    print("🧪 TESTING QUERY CATEGORY PERFORMANCE")
    print("This test simulates the entire flow to identify where category breakdown fails.\n")
    
    # Test each step
    shared = test_query_generation()
    shared = test_platform_querying(shared)
    shared = test_response_analysis(shared)
    test_flask_template_data(shared)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("If category breakdown is still empty, check:")
    print("1. Are you using the updated QueryGeneratorNode?")
    print("2. Is MultiPlatformQueryNode preserving category metadata?") 
    print("3. Is ResponseAnalysisNode receiving the category data?")
    print("\nRun this test to see exactly where the issue is!")

if __name__ == "__main__":
    main()