# flow.py
from pocketflow import Flow
from nodes import (
    QueryGeneratorNode, 
    MultiPlatformQueryNode, 
    ResponseAnalysisNode,
    OptimizationAgentNode,
    ReportGeneratorNode,
    DatabaseStorageNode
)

def create_brand_monitoring_flow():
    """Create and return the main brand monitoring flow"""
    
    # Create all nodes
    query_generator = QueryGeneratorNode()
    platform_querier = MultiPlatformQueryNode()
    response_analyzer = ResponseAnalysisNode()
    optimization_agent = OptimizationAgentNode()
    report_generator = ReportGeneratorNode()
    database_storage = DatabaseStorageNode()
    
    # Create linear flow for main processing
    query_generator >> platform_querier >> response_analyzer >> optimization_agent
    
    # Branch based on optimization results
    optimization_agent - "needs_attention" >> report_generator
    optimization_agent - "performing_well" >> report_generator  
    optimization_agent - "default" >> report_generator
    
    # Always store data after report generation
    report_generator >> database_storage
    
    # Create flow starting with query generation
    return Flow(start=query_generator)

def create_simple_monitoring_flow():
    """Create a simplified flow for quick testing"""
    
    query_generator = QueryGeneratorNode()
    platform_querier = MultiPlatformQueryNode()
    response_analyzer = ResponseAnalysisNode()
    report_generator = ReportGeneratorNode()
    
    # Simple linear flow
    query_generator >> platform_querier >> response_analyzer >> report_generator
    
    return Flow(start=query_generator)

if __name__ == "__main__":
    # Test flow creation
    flow = create_brand_monitoring_flow()
    print("Brand monitoring flow created successfully!")
    
    # Print basic flow info
    print(f"Starting node: {type(flow.start).__name__}")



