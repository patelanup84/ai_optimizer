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
