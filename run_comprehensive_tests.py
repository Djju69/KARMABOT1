#!/usr/bin/env python3
"""
Comprehensive Test Runner for KARMABOT1
Runs all test categories and generates coverage reports
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path


class ComprehensiveTestRunner:
    """Comprehensive test runner for KARMABOT1"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.coverage_data = {}
    
    def run_all_tests(self):
        """Run all test categories"""
        print("🧪 KARMABOT1 Comprehensive Test Suite")
        print("=" * 60)
        
        test_categories = [
            ("Unit Tests", "tests/unit/", "unit"),
            ("Integration Tests", "tests/integration/", "integration"),
            ("E2E Tests", "tests/e2e/", "e2e"),
            ("Performance Tests", "tests/performance/", "performance")
        ]
        
        for category, test_path, marker in test_categories:
            if os.path.exists(test_path):
                print(f"\n📋 Running {category}...")
                self._run_test_category(category, test_path, marker)
            else:
                print(f"⚠️ {category} directory not found: {test_path}")
        
        # Generate comprehensive report
        self._generate_comprehensive_report()
    
    def _run_test_category(self, category, test_path, marker):
        """Run tests for a specific category"""
        try:
            # Run tests with coverage
            cmd = [
                "python", "-m", "pytest",
                test_path,
                f"-m", marker,
                "--cov=core",
                "--cov=web",
                "--cov-report=term-missing",
                "--cov-report=json:coverage_{marker}.json",
                "-v",
                "--tb=short",
                "--durations=10"
            ]
            
            print(f"Command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(f"✅ {category} passed")
                self.test_results[category] = {
                    "status": "passed",
                    "output": result.stdout
                }
                self._parse_coverage_output(category, result.stdout)
            else:
                print(f"❌ {category} failed")
                print(f"Error: {result.stderr}")
                self.test_results[category] = {
                    "status": "failed",
                    "error": result.stderr,
                    "output": result.stdout
                }
                
        except Exception as e:
            print(f"❌ Error running {category}: {e}")
            self.test_results[category] = {
                "status": "error",
                "error": str(e)
            }
    
    def _parse_coverage_output(self, category, output):
        """Parse coverage output from pytest"""
        lines = output.split('\n')
        coverage_percent = 0
        
        for line in lines:
            if "TOTAL" in line and "%" in line:
                try:
                    coverage_percent = float(line.split()[-1].replace('%', ''))
                    break
                except (ValueError, IndexError):
                    pass
        
        self.coverage_data[category] = coverage_percent
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Comprehensive Test Report")
        print("=" * 60)
        
        # Test results summary
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result["status"] == "passed")
        total_tests = len(self.test_results)
        
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        
        # Coverage summary
        if self.coverage_data:
            avg_coverage = sum(self.coverage_data.values()) / len(self.coverage_data)
            print(f"📊 Average Coverage: {avg_coverage:.1f}%")
            
            print("\n📈 Coverage by Category:")
            for category, coverage in self.coverage_data.items():
                status = "✅" if coverage >= 80 else "⚠️" if coverage >= 70 else "❌"
                print(f"  {status} {category}: {coverage:.1f}%")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for category, result in self.test_results.items():
            status = result["status"]
            status_emoji = "✅" if status == "passed" else "❌"
            print(f"  {status_emoji} {category}: {status}")
            
            if status == "failed" and "error" in result:
                print(f"    Error: {result['error'][:100]}...")
        
        # Recommendations
        self._generate_recommendations()
        
        # Save report
        self._save_report()
    
    def _generate_recommendations(self):
        """Generate test recommendations"""
        print("\n💡 Recommendations:")
        
        recommendations = []
        
        # Check test coverage
        if self.coverage_data:
            low_coverage = [cat for cat, cov in self.coverage_data.items() if cov < 80]
            if low_coverage:
                recommendations.append(f"Improve test coverage for: {', '.join(low_coverage)}")
        
        # Check test results
        failed_tests = [cat for cat, result in self.test_results.items() 
                       if result["status"] == "failed"]
        if failed_tests:
            recommendations.append(f"Fix failing tests: {', '.join(failed_tests)}")
        
        # Check missing test categories
        expected_categories = ["Unit Tests", "Integration Tests", "E2E Tests", "Performance Tests"]
        missing_categories = [cat for cat in expected_categories 
                            if cat not in self.test_results]
        if missing_categories:
            recommendations.append(f"Add missing test categories: {', '.join(missing_categories)}")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  🎉 All tests are in good shape!")
    
    def _save_report(self):
        """Save comprehensive report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": "KARMABOT1",
            "test_results": self.test_results,
            "coverage_data": self.coverage_data,
            "summary": {
                "total_categories": len(self.test_results),
                "passed_categories": sum(1 for r in self.test_results.values() 
                                       if r["status"] == "passed"),
                "average_coverage": sum(self.coverage_data.values()) / len(self.coverage_data) 
                                  if self.coverage_data else 0
            }
        }
        
        report_file = self.project_root / "comprehensive_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Comprehensive report saved to: {report_file}")
    
    def run_specific_tests(self, test_type):
        """Run specific test type"""
        test_mappings = {
            "unit": "tests/unit/",
            "integration": "tests/integration/",
            "e2e": "tests/e2e/",
            "performance": "tests/performance/"
        }
        
        if test_type not in test_mappings:
            print(f"❌ Unknown test type: {test_type}")
            print(f"Available types: {', '.join(test_mappings.keys())}")
            return
        
        test_path = test_mappings[test_type]
        if not os.path.exists(test_path):
            print(f"❌ Test path not found: {test_path}")
            return
        
        print(f"🧪 Running {test_type.title()} Tests...")
        self._run_test_category(f"{test_type.title()} Tests", test_path, test_type)
    
    def run_coverage_only(self):
        """Run coverage analysis only"""
        print("📊 Running Coverage Analysis...")
        
        cmd = [
            "python", "-m", "pytest",
            "--cov=core",
            "--cov=web",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json",
            "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Coverage analysis completed")
                print(f"📄 HTML report: {self.project_root}/htmlcov/index.html")
                print(f"📄 JSON report: {self.project_root}/coverage.json")
            else:
                print(f"❌ Coverage analysis failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error running coverage analysis: {e}")


def main():
    """Main function"""
    runner = ComprehensiveTestRunner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "unit":
            runner.run_specific_tests("unit")
        elif command == "integration":
            runner.run_specific_tests("integration")
        elif command == "e2e":
            runner.run_specific_tests("e2e")
        elif command == "performance":
            runner.run_specific_tests("performance")
        elif command == "coverage":
            runner.run_coverage_only()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: unit, integration, e2e, performance, coverage")
    else:
        # Run all tests
        runner.run_all_tests()


if __name__ == "__main__":
    main()
