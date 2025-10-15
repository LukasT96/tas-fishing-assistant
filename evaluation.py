"""
Evaluation Framework for Tasmania Fishing Chatbot

Tests the system with:
- Ground truth passing questions (5-7 questions covering RAG, Tool, and Both)
- Difficult questions (2-3 that the system struggles with)
- Verification of correct citations and tool calls
- Analysis of failure points
"""

import json
from typing import Dict, List
from src.rag_model import RAGModel
from src.tools_model import ToolsModel


class EvaluationFramework:
    """
    Evaluation framework for testing the chatbot's RAG and Tool capabilities.
    """
    
    def __init__(self, config_path: str = "config.yml"):
        self.rag_model = RAGModel(config_path=config_path)
        self.tools_model = ToolsModel(config_path=config_path)
        
        # Load documents into RAG model
        self._load_documents(config_path)
        
        # Define passing baseline questions
        self.passing_questions = [
            {
                "id": "P1",
                "question": "What species can I catch from shore at Derwent River?",
                "type": "RAG",
                "expected_answer": "From shore at Derwent River you can catch: sand flathead, barracouta, bream, Australian salmon, trout, and mullet.",
                "expected_citations": ["Locations"],
                "reasoning": "Tests RAG retrieval of location-specific fishing information"
            },
            {
                "id": "P2",
                "question": "Is a 26cm brown trout legal to keep?",
                "type": "Tool",
                "expected_answer": "Yes, legal to keep. Minimum size is 25cm, this fish is 1cm over the limit.",
                "expected_tool": "check_legal_size",
                "expected_tool_params": {"species": "brown trout", "length_cm": 26},
                "reasoning": "Tests tool calling for legal size verification"
            },
            {
                "id": "P3",
                "question": "Do I need a licence for rod and line fishing in marine waters?",
                "type": "RAG",
                "expected_answer": "No, you don't need a licence for rod and line fishing in marine waters in Tasmania.",
                "expected_citations": ["Fishing_licences", "General_Guide"],
                "reasoning": "Tests RAG retrieval of licence requirement information"
            },
            {
                "id": "P4",
                "question": "I caught a 31cm Atlantic salmon, is it legal to keep?",
                "type": "Tool",
                "expected_answer": "Yes, legal to keep. Minimum size is 30cm, this fish is 1cm over the limit.",
                "expected_tool": "check_legal_size",
                "expected_tool_params": {"species": "atlantic salmon", "length_cm": 31},
                "reasoning": "Tests tool with legal-sized fish"
            },
            {
                "id": "P5",
                "question": "What is the daily bag limit for abalone?",
                "type": "RAG",
                "expected_answer": "The daily bag limit for abalone is 10 abalone.",
                "expected_citations": ["General_Guide"],
                "reasoning": "Tests RAG retrieval of specific bag limit information"
            },
            {
                "id": "P6",
                "question": "Can I keep a 24cm rainbow trout?",
                "type": "Tool",
                "expected_answer": "No, must be released. Minimum size is 25cm, this fish is 1cm under the limit.",
                "expected_tool": "check_legal_size",
                "expected_tool_params": {"species": "rainbow trout", "length_cm": 24},
                "reasoning": "Tests tool with undersized fish (negative case)"
            },
            {
                "id": "P7",
                "question": "When is the squid closure on the north coast?",
                "type": "RAG",
                "expected_answer": "The north coast squid closure is from 1 September to 31 October inclusive.",
                "expected_citations": ["Fishing_seasons", "General_Guide"],
                "reasoning": "Tests RAG retrieval of seasonal closure information"
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
                "question": "I caught a 18cm bream in the Derwent River, is it legal?",
                "type": "Tool Limitation",
                "expected_failure": "Tool doesn't have bream in its species list",
                "expected_answer": "Legal size checker doesn't support bream species. Check official regulations.",
                "reasoning": "Tests tool limitation handling - species not in tool's database (bream is mentioned in documents but not in tool)"
            },
            {
                "id": "D3",
                "question": "If I fish in both the Eastern and Western zones in one day, what's my rock lobster limit?",
                "type": "Complex Regulation",
                "expected_failure": "RAG may not retrieve zone-specific rules, or LLM may not correctly interpret multi-zone bag limits",
                "expected_answer": "Eastern Region: 2 rock lobster, Western Region: 5 rock lobster. Complex on-water possession rules apply when crossing zones.",
                "reasoning": "Tests handling of complex, multi-part regulatory questions with zone-specific rules"
            }
        ]
    
    def _load_documents(self, config_path: str):
        """Load all fishing documents into the RAG pipeline"""
        import yaml
        import os
        
        # Load config to get document paths
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
        """
        Run all passing baseline tests and verify results.
        
        Returns:
            Dict with test results
        """
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
            routing_decision = self.rag_model.router.route(test_case['question'])
            
            # Get system response
            response = self.rag_model.query(test_case['question'])
            
            # Verify routing
            routing_correct = self._verify_routing(test_case, routing_decision)
            
            # Verify tool call if expected
            tool_correct = True
            if test_case['type'] in ['Tool', 'Both']:
                tool_correct = self._verify_tool_call(test_case, routing_decision)
            
            # Verify RAG retrieval if expected
            rag_correct = True
            if test_case['type'] in ['RAG', 'Both']:
                rag_correct = self._verify_rag_retrieval(test_case, test_case['question'])
            
            # Overall result
            passed = routing_correct and tool_correct and rag_correct
            
            result_detail = {
                "id": test_case['id'],
                "question": test_case['question'],
                "type": test_case['type'],
                "passed": passed,
                "routing_correct": routing_correct,
                "tool_correct": tool_correct,
                "rag_correct": rag_correct,
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
            
            print(f"\nResponse:\n{response}\n")
            print("-" * 70)
        
        # Summary
        print("\n" + "="*70)
        print("PASSING TESTS SUMMARY")
        print("="*70)
        print(f"Total Tests: {results['total']}")
        print(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
        print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
        
        return results
    
    def run_difficult_tests(self) -> Dict:
        """
        Run difficult/challenging tests and analyze failure points.
        
        Returns:
            Dict with test results and failure analysis
        """
        print("\n" + "="*70)
        print("RUNNING DIFFICULT/CHALLENGING TESTS")
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
            routing_decision = self.rag_model.router.route(test_case['question'])
            
            # Get system response
            response = self.rag_model.query(test_case['question'])
            
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
            return routing_decision['needs_rag'] and not routing_decision['needs_tool']
        elif expected_type == 'Tool':
            return routing_decision['needs_tool'] and (not routing_decision['needs_rag'] or routing_decision['needs_rag'])
        elif expected_type == 'Both':
            return routing_decision['needs_rag'] and routing_decision['needs_tool']
        
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
        
        # Check parameters (species and length within reasonable range)
        actual_params = routing_decision.get('tool_params', {})
        
        if 'species' in expected_params:
            if actual_params.get('species', '').lower() != expected_params['species'].lower():
                print(f"  ⚠️  Species mismatch: expected {expected_params['species']}, got {actual_params.get('species')}")
                return False
        
        if 'length_cm' in expected_params:
            expected_length = expected_params['length_cm']
            actual_length = actual_params.get('length_cm', 0)
            # Allow 1cm tolerance for extraction errors
            if abs(actual_length - expected_length) > 1:
                print(f"  ⚠️  Length mismatch: expected {expected_length}cm, got {actual_length}cm")
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
        retrieved_sources = [meta.get('source', '') for _, _, meta in retrievals]
        
        for expected_source in expected_sources:
            if not any(expected_source in source for source in retrieved_sources):
                print(f"  ⚠️  Expected source '{expected_source}' not in retrieved documents")
                return False
        
        return True
    
    def _analyze_failure(self, test_case: Dict, routing_decision: Dict, response: str) -> Dict:
        """Analyze failure mode for difficult questions"""
        
        failure_modes = []
        
        # Check if RAG failed to retrieve
        if "I don't have" in response or "not in my knowledge base" in response.lower():
            failure_modes.append("RAG retrieval failed - no relevant context found")
        
        # Check if tool limitation
        if "don't have legal size information" in response or "Unknown species" in response:
            failure_modes.append("Tool limitation - species not supported")
        
        # Check if LLM didn't use retrieved context
        if routing_decision['needs_rag']:
            retrievals = self.rag_model.search(test_case['question'])
            if retrievals and ("I don't have" in response):
                failure_modes.append("LLM failed to use retrieved context (grounding failure)")
        
        # Check if routing was incorrect
        if not routing_decision.get('success', True):
            failure_modes.append("Router failed or used fallback")
        
        # Check if tool wasn't called when needed
        if "tool" in test_case['expected_failure'].lower() and not routing_decision['needs_tool']:
            failure_modes.append("Tool calling failed - router didn't identify tool need")
        
        failure_mode = " | ".join(failure_modes) if failure_modes else "No clear failure identified"
        
        return {
            "failure_occurred": len(failure_modes) > 0,
            "failure_mode": failure_mode,
            "analysis": f"Expected: {test_case['expected_failure']}. Actual: {failure_mode}"
        }
    
    def save_results(self, passing_results: Dict, difficult_results: Dict, output_file: str = "evaluation_results.json"):
        """Save evaluation results to JSON file"""
        results = {
            "passing_tests": passing_results,
            "difficult_tests": difficult_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to {output_file}")


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

