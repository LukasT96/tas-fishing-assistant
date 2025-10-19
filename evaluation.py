"""
Evaluation Framework for Tasmania Fishing Chatbot

Tests the system with:
- Ground truth passing questions (3 RAG, 3 Tools, 2 RAG+Tools)
- Difficult questions (2-3 out of scope questions)
- Verification of correct citations using verify_retrieval
- Analysis of failure points
"""

import json
import yaml
import os
import re
from typing import Dict, List
from src.rag_model import RAGModel
from src.tools_model import ToolsModel
from src.router import Router


class EvaluationFramework:
    """
    Evaluation framework for testing the chatbot's RAG and Tool capabilities.
    """
    
    def __init__(self, config_path: str = "config.yml"):
        self.rag_model = RAGModel(config_path=config_path)
        self.tools_model = ToolsModel(config_path=config_path)
        
        # Initialize Router
        self.router = Router(
            rag_model=self.rag_model,
            tools_model=self.tools_model,
            llm_callable=self.rag_model.llm_call
        )
        
        # Load documents into RAG model
        self._load_documents(config_path)
        
        # Define passing baseline questions with expected citations
        self.passing_questions = [
            {
                "id": "P1",
                "question": "What is the bag limit, minimum size for brown trout?",
                "type": "RAG",
                "expected_answer": "The bag limit for brown trout is 12 per day.",
                "expected_citations": ["tas_fishing_guide/species"],
                "key_facts_to_verify": [
                    "12",  # bag limit number
                    "trout - brown"
                ],
                "reasoning": "Tests RAG retrieval of species-specific bag limit information from species section"
            },
            {
                "id": "P2",
                "question": "Do I need a licence for fishing abalone?",
                "type": "RAG",
                "expected_answer": "Yes, you need a freshwater fishing licence.",
                "expected_citations": ["tas_fishing_guide/fishing_licence"],
                "key_facts_to_verify": [
                    "licence",
                    "abalone"
                ],
                "reasoning": "Tests RAG retrieval of licence requirement information from licence section"
            },
            {
                "id": "P3",
                "question": "Where are good spots for flathead fishing?",
                "type": "RAG",
                "expected_answer": "Derwent River, East Coast, Port Sorell",
                "expected_citations": ["tas_fishing_guide/hot_fishing_spots"],
                "key_facts_to_verify": [
                    "flathead"
                ],
                "reasoning": "Tests RAG retrieval of location information from hot_fishing_spots section"
            },
            {
                "id": "P4",
                "question": "What's the weather like for fishing at Hobart tomorrow?",
                "type": "Tool",
                "expected_answer": "Weather forecast with temperature, wind, rain, and fishing conditions assessment",
                "expected_tool": "get_fishing_weather",
                "expected_tool_params": {"location": "Hobart", "days": 5},
                "reasoning": "Tests weather tool calling for single location forecast"
            },
            {
                "id": "P5",
                "question": "Which day will have the best fishing weather in Hobart next week?",
                "type": "Tool",
                "expected_answer": "5-day forecast with best fishing day highlighted and fishing scores",
                "expected_tool": "get_fishing_weather",
                "expected_tool_params": {"location": "Hobart", "days": 5},
                "reasoning": "Tests weather tool for multi-day forecast and best day recommendation"
            },
            
            {
                "id": "P6",
                "question": "Is 30cm flathead legal to keep?",
                "type": "RAG",
                "expected_answer": "No it's not legal",
                "expected_citations": ["tas_fishing_guide/species"],
                "key_facts_to_verify": [
                    "flathead",
                    "Minimum size"
                ],
                "reasoning": "Tests rag ability to perform legal size checker"
            },
            
            # === RAG + TOOLS (2 questions) ===
            {
                "id": "P7",
                "question": "What's the weather like at Port Sorell and what species can I catch there?",
                "type": "Both",
                "expected_answer": "Weather forecast + species information from documents",
                "expected_citations": ["tas_fishing_guide/hot_fishing_spots"],
                "expected_tool": "get_fishing_weather",
                "expected_tool_params": {"location": "Port Sorell", "days": 5},
                "key_facts_to_verify": [
                    "Port Sorell"
                ],
                "reasoning": "Tests combined RAG (species at location) and Tool (weather) usage"
            },
            {
                "id": "P8",
                "question": "I want to go fishing for flathead at Burnie - what are the rules for flathead and what's the weather forecast?",
                "type": "Both",
                "expected_answer": "Bag limits, size limits from RAG + weather forecast from tool",
                "expected_citations": ["tas_fishing_guide/species", "tas_fishing_guide/hot_fishing_spots"],
                "expected_tool": "get_fishing_weather",
                "expected_tool_params": {"location": "Burnie", "days": 5},
                "key_facts_to_verify": [
                    "flathead",
                ],
                "reasoning": "Tests RAG (regulations) + Tool (weather) integration for trip planning"
            }
        ]
        
        # Define difficult questions that may fail
        self.difficult_questions = [
            {
                "id": "D1",
                "question": "What's the best time of day to catch yellowtail kingfish under the Tasman Bridge?",
                "type": "Out of Scope",
                "expected_failure": "RAG fails to retrieve relevant context - fishing techniques/timing not in documents",
                "expected_answer": "Documents don't contain information about best fishing times or techniques.",
                "reasoning": "Tests system's ability to recognize when information is not available (documents mention kingfish location but not timing)"
            },
            {
                "id": "D2",
                "question": "If I fish in both the Eastern and Western zones in one day, what's my rock lobster limit?",
                "type": "Complex Regulation",
                "expected_failure": "RAG may not retrieve zone-specific rules, or LLM may not correctly interpret multi-zone bag limits",
                "expected_answer": "Eastern Region: 2 rock lobster, Western Region: 5 rock lobster. Complex on-water possession rules apply when crossing zones.",
                "reasoning": "Tests handling of complex, multi-part regulatory questions with zone-specific rules"
            }
        ]
    
    def _load_documents(self, config_path: str):
        """Load all fishing documents into the RAG pipeline"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        base_path = config['documents']['base_path']
        sources = config['documents']['sources']
        
        print("Loading documents into RAG model...")
        for doc in sources:
            doc_path = os.path.join(base_path, doc)
            
            if os.path.exists(doc_path):
                try:
                    chunks = self.rag_model.load_ground_truth(doc_path)
                    print(f"  ✓ Loaded {doc}: {chunks} chunks")
                except Exception as e:
                    print(f"  ✗ Failed to load {doc}: {e}")
            else:
                print(f"  ✗ File not found: {doc_path}")
        
        print(f"Total documents in database: {self.rag_model.collection.count()}")
        print()
    
    def run_passing_tests(self) -> Dict:
        """Run all passing baseline tests and verify results"""
        print("\n" + "="*70)
        print("RUNNING PASSING BASELINE TESTS")
        print("="*70 + "\n")
        
        results = {
            "total": len(self.passing_questions),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for test_case in self.passing_questions:
            print(f"\n[{test_case['id']}] Testing: {test_case['question']}")
            print(f"Type: {test_case['type']}")
            print(f"Reasoning: {test_case['reasoning']}\n")
            
            # Get routing decision
            routing_decision = self.router.route(test_case['question'])
            
            # Get system response
            response = self.router.query_with_routing(test_case['question'])
            
            # Verify routing
            routing_correct = self._verify_routing(test_case, routing_decision)
            
            # Verify tool call if expected
            tool_correct = True
            if test_case['type'] in ['Tool', 'Both']:
                tool_correct = self._verify_tool_call(test_case, routing_decision)
            
            # Verify RAG retrieval if expected
            rag_correct = True
            citation_verified = True
            if test_case['type'] in ['RAG', 'Both']:
                rag_correct = self._verify_rag_retrieval(test_case, test_case['question'])
                
                # USE verify_retrieval to check if key facts are cited
                if 'key_facts_to_verify' in test_case:
                    citation_verified = self._verify_citations_in_response(
                        test_case, 
                        test_case['question'],
                        response
                    )
            
            # Overall result
            passed = routing_correct and tool_correct and rag_correct and citation_verified
            
            result_detail = {
                "id": test_case['id'],
                "question": test_case['question'],
                "type": test_case['type'],
                "passed": passed,
                "routing_correct": routing_correct,
                "tool_correct": tool_correct,
                "rag_correct": rag_correct,
                "citation_verified": citation_verified,
                "response": response,
                "routing_decision": routing_decision
            }
            
            results['details'].append(result_detail)
            
            if passed:
                results['passed'] += 1
                print(f"✅ PASSED")
            else:
                results['failed'] += 1
                print(f"❌ FAILED")
                if not routing_correct:
                    print(f"  - Routing incorrect")
                if not tool_correct:
                    print(f"  - Tool call incorrect")
                if not rag_correct:
                    print(f"  - RAG retrieval incorrect")
                if not citation_verified:
                    print(f"  - Citation verification failed")
            
            print(f"\nResponse:\n{response}\n")
            print("-" * 70)
        
        # Summary
        print("\n" + "="*70)
        print("PASSING TESTS SUMMARY")
        print("="*70)
        print(f"Total: {results['total']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {results['passed']/results['total']*100:.1f}%")
        
        return results
    
    def run_difficult_tests(self) -> Dict:
        """Run difficult tests to identify failure modes"""
        print("\n" + "="*70)
        print("RUNNING DIFFICULT TESTS (Expected Failures)")
        print("="*70 + "\n")
        
        results = {
            "total": len(self.difficult_questions),
            "details": []
        }
        
        for test_case in self.difficult_questions:
            print(f"\n[{test_case['id']}] Testing: {test_case['question']}")
            print(f"Type: {test_case['type']}")
            print(f"Expected Failure: {test_case['expected_failure']}")
            print(f"Reasoning: {test_case['reasoning']}\n")
            
            # Get routing decision
            routing_decision = self.router.route(test_case['question'])
            
            # Get system response
            response = self.router.query_with_routing(test_case['question'])
            
            # Analyze failure
            failure_analysis = self._analyze_failure(test_case, routing_decision, response)
            
            result_detail = {
                "id": test_case['id'],
                "question": test_case['question'],
                "type": test_case['type'],
                "expected_failure": test_case['expected_failure'],
                "actual_failure": failure_analysis['failure_occurred'],
                "failure_mode": failure_analysis['failure_mode'],
                "response": response,
                "routing_decision": routing_decision,
                "analysis": failure_analysis['analysis']
            }
            
            results['details'].append(result_detail)
            
            print(f"\nResponse:\n{response}\n")
            print(f"\nFailure Analysis:")
            print(f"  - Failure Occurred: {failure_analysis['failure_occurred']}")
            print(f"  - Failure Mode: {failure_analysis['failure_mode']}")
            print(f"  - Analysis: {failure_analysis['analysis']}")
            print("-" * 70)
        
        # Summary
        print("\n" + "="*70)
        print("DIFFICULT TESTS SUMMARY")
        print("="*70)
        print(f"Total Tests: {results['total']}")
        print("\nFailure Modes Identified:")
        for detail in results['details']:
            print(f"  - {detail['id']}: {detail['failure_mode']}")
        
        return results
    
    def _verify_routing(self, test_case: Dict, routing_decision: Dict) -> bool:
        """Verify routing decision matches expected type"""
        expected_type = test_case['type']
        
        if expected_type == 'RAG':
            correct = routing_decision['needs_rag'] and not routing_decision['needs_tool']
            if not correct:
                print(f"  ⚠️  Routing mismatch: expected RAG only, got needs_rag={routing_decision['needs_rag']}, needs_tool={routing_decision['needs_tool']}")
            return correct
        elif expected_type == 'Tool':
            correct = routing_decision['needs_tool']
            if not correct:
                print(f"  ⚠️  Routing mismatch: expected Tool, got needs_tool={routing_decision['needs_tool']}")
            return correct
        elif expected_type == 'Both':
            correct = routing_decision['needs_rag'] and routing_decision['needs_tool']
            if not correct:
                print(f"  ⚠️  Routing mismatch: expected Both, got needs_rag={routing_decision['needs_rag']}, needs_tool={routing_decision['needs_tool']}")
            return correct
        
        return False
    
    def _verify_tool_call(self, test_case: Dict, routing_decision: Dict) -> bool:
        """Verify tool was called with correct parameters"""
        if 'expected_tool' not in test_case:
            return True
        
        expected_tool = test_case['expected_tool']
        expected_params = test_case.get('expected_tool_params', {})
        
        # Check tool name
        if routing_decision.get('tool_name') != expected_tool:
            print(f"  ⚠️  Tool mismatch: expected {expected_tool}, got {routing_decision.get('tool_name')}")
            return False
        
        # Check parameters
        actual_params = routing_decision.get('tool_params', {})
        
        if 'location' in expected_params:
            expected_loc = expected_params['location'].lower()
            actual_loc = actual_params.get('location', '').lower()
            if expected_loc not in actual_loc and actual_loc not in expected_loc:
                print(f"  ⚠️  Location mismatch: expected '{expected_params['location']}', got '{actual_params.get('location')}'")
                return False
        
        return True
    
    def _verify_rag_retrieval(self, test_case: Dict, query: str) -> bool:
        """Verify RAG retrieved relevant citations"""
        if 'expected_citations' not in test_case:
            return True
        
        expected_sources = test_case['expected_citations']
        
        # Get actual retrievals
        retrievals = self.rag_model.search(query)
        
        if not retrievals:
            print(f"  ⚠️  No documents retrieved")
            return False
        
        # Check if expected sources are in retrievals
        retrieved_info = [(meta.get('source', ''), meta.get('section', '')) for _, _, meta in retrievals]
        
        for expected_source in expected_sources:
            # Check if source/section matches
            found = False
            for source, section in retrieved_info:
                if '/' in expected_source:
                    # Exact section match
                    if f"{source}/{section}" == expected_source:
                        found = True
                        break
                else:
                    # Just source match
                    if expected_source in source:
                        found = True
                        break
            
            if not found:
                print(f"  ⚠️  Expected source '{expected_source}' not in retrieved documents")
                print(f"      Retrieved: {retrieved_info[:3]}")
                return False
        
        print(f"  ✓ Retrieved correct sections: {[f'{s}/{sec}' for s, sec in retrieved_info[:3]]}")
        return True
    
    def _verify_citations_in_response(self, test_case: Dict, query: str, response: str) -> bool:
        """
        USE RAG MODEL'S verify_retrieval TO CHECK IF KEY FACTS APPEAR IN RETRIEVED DOCS
        """
        if 'key_facts_to_verify' not in test_case:
            return True
        
        # Get retrievals for this query
        retrievals = self.rag_model.search(query)
        
        if not retrievals:
            print(f"  ⚠️  No retrievals to verify citations against")
            return False
        
        key_facts = test_case['key_facts_to_verify']
        all_verified = True
        
        print(f"  📋 Verifying {len(key_facts)} key facts in retrieved documents:")
        
        for fact in key_facts:
            # Use RAG model's verify_retrieval method
            verified = self.rag_model.verify_retrieval(fact, retrievals)
            
            if verified:
                print(f"    ✓ '{fact}' found in retrieved documents")
            else:
                print(f"    ✗ '{fact}' NOT found in retrieved documents")
                all_verified = False
        
        return all_verified
    
    def _analyze_failure(self, test_case: Dict, routing_decision: Dict, response: str) -> Dict:
        """Analyze failure mode for difficult questions"""
        
        failure_modes = []
        
        # Check if system acknowledged missing information
        acknowledgment_phrases = [
            "don't have",
            "not in my knowledge",
            "not available",
            "can't provide",
            "outside my scope",
            "tasmania only",
            "recommend checking",
            "specialize in tasmania"
        ]
        
        acknowledged = any(phrase in response.lower() for phrase in acknowledgment_phrases)
        
        if acknowledged:
            failure_modes.append("✓ System correctly acknowledged limitation")
        else:
            failure_modes.append("⚠️ System may have hallucinated or provided unsupported answer")
        
        # Check if RAG retrieved something but LLM didn't use it
        if routing_decision.get('needs_rag'):
            retrievals = self.rag_model.search(test_case['question'])
            if retrievals and "don't have" in response.lower():
                failure_modes.append("RAG retrieved docs but LLM didn't extract answer")
        
        # Check routing decision
        route_type = routing_decision.get('route_type', 'unknown')
        failure_modes.append(f"Routed as: {route_type}")
        
        failure_mode = " | ".join(failure_modes) if failure_modes else "No clear failure identified"
        
        return {
            "failure_occurred": True,
            "failure_mode": failure_mode,
            "analysis": f"Expected: {test_case['expected_failure']}. Actual: {failure_mode}"
        }
    
    # def save_results(self, passing_results: Dict, difficult_results: Dict, output_file: str = "evaluation_results.json"):
    #     """Save evaluation results to JSON file"""
    #     results = {
    #         "passing_tests": passing_results,
    #         "difficult_tests": difficult_results
    #     }
        
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump(results, f, indent=2, ensure_ascii=False)
        
    #     print(f"\n✅ Results saved to {output_file}")


def main():
    """Run evaluation"""
    print("Tasmania Fishing Chatbot - Evaluation Framework")
    print("=" * 70)
    
    # Initialize evaluation
    eval_framework = EvaluationFramework()
    
    # Run passing tests
    passing_results = eval_framework.run_passing_tests()
    
    # Run difficult tests
    difficult_results = eval_framework.run_difficult_tests()
    
    # Save results
    eval_framework.save_results(passing_results, difficult_results)
    
    print("\n" + "="*70)
    print("EVALUATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()