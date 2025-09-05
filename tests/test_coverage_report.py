"""
Test Coverage Report Generator for KARMABOT1
Generates comprehensive test coverage reports
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path


class TestCoverageReporter:
    """Test coverage reporter for KARMABOT1"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.coverage_data = {}
        self.test_results = {}
    
    def run_coverage_analysis(self):
        """Run coverage analysis for all test modules"""
        print("🧪 Running Test Coverage Analysis...")
        print("=" * 50)
        
        # Test modules to analyze
        test_modules = [
            "core",
            "web",
            "bot",
            "api"
        ]
        
        for module in test_modules:
            if os.path.exists(os.path.join(self.project_root, module)):
                self._analyze_module_coverage(module)
        
        # Generate coverage report
        self._generate_coverage_report()
    
    def _analyze_module_coverage(self, module):
        """Analyze coverage for a specific module"""
        print(f"📊 Analyzing {module} module...")
        
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                f"tests/unit/test_{module}.py",
                f"tests/integration/test_{module}.py",
                "--cov=core",
                "--cov=web",
                "--cov-report=json",
                "--cov-report=term-missing",
                "-v"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(f"✅ {module} tests passed")
                self._parse_coverage_data(module, result.stdout)
            else:
                print(f"⚠️ {module} tests had issues: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error analyzing {module}: {e}")
    
    def _parse_coverage_data(self, module, output):
        """Parse coverage data from pytest output"""
        # This is a simplified parser - in practice, you'd parse the JSON coverage report
        lines = output.split('\n')
        coverage_percent = 0
        
        for line in lines:
            if "TOTAL" in line and "%" in line:
                # Extract coverage percentage
                try:
                    coverage_percent = float(line.split()[-1].replace('%', ''))
                    break
                except (ValueError, IndexError):
                    pass
        
        self.coverage_data[module] = {
            "coverage_percent": coverage_percent,
            "status": "passed" if coverage_percent > 80 else "needs_improvement"
        }
    
    def _generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        print("\n📋 Test Coverage Report")
        print("=" * 50)
        
        total_coverage = 0
        module_count = 0
        
        for module, data in self.coverage_data.items():
            coverage = data["coverage_percent"]
            status = data["status"]
            
            print(f"📁 {module.upper()}: {coverage:.1f}% ({status})")
            
            if coverage > 0:
                total_coverage += coverage
                module_count += 1
        
        if module_count > 0:
            average_coverage = total_coverage / module_count
            print(f"\n📊 Average Coverage: {average_coverage:.1f}%")
            
            if average_coverage >= 90:
                print("🎉 Excellent test coverage!")
            elif average_coverage >= 80:
                print("✅ Good test coverage")
            elif average_coverage >= 70:
                print("⚠️ Moderate test coverage - consider adding more tests")
            else:
                print("❌ Low test coverage - needs significant improvement")
        
        # Generate detailed report
        self._generate_detailed_report()
    
    def _generate_detailed_report(self):
        """Generate detailed test coverage report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": "KARMABOT1",
            "coverage_summary": self.coverage_data,
            "test_modules": self._get_test_modules(),
            "recommendations": self._get_recommendations()
        }
        
        # Save report to file
        report_file = self.project_root / "test_coverage_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
    
    def _get_test_modules(self):
        """Get list of test modules"""
        test_modules = []
        tests_dir = self.project_root / "tests"
        
        if tests_dir.exists():
            for test_file in tests_dir.rglob("test_*.py"):
                module_name = test_file.stem.replace("test_", "")
                test_modules.append({
                    "file": str(test_file.relative_to(self.project_root)),
                    "module": module_name,
                    "type": "unit" if "unit" in str(test_file) else "integration" if "integration" in str(test_file) else "e2e"
                })
        
        return test_modules
    
    def _get_recommendations(self):
        """Get test coverage recommendations"""
        recommendations = []
        
        # Analyze coverage data
        low_coverage_modules = [
            module for module, data in self.coverage_data.items()
            if data["coverage_percent"] < 80
        ]
        
        if low_coverage_modules:
            recommendations.append({
                "priority": "high",
                "module": low_coverage_modules,
                "recommendation": "Add more unit tests for better coverage"
            })
        
        # Check for missing test types
        test_types = set()
        tests_dir = self.project_root / "tests"
        
        if tests_dir.exists():
            for test_file in tests_dir.rglob("test_*.py"):
                if "unit" in str(test_file):
                    test_types.add("unit")
                elif "integration" in str(test_file):
                    test_types.add("integration")
                elif "e2e" in str(test_file):
                    test_types.add("e2e")
        
        if "performance" not in test_types:
            recommendations.append({
                "priority": "medium",
                "recommendation": "Add performance tests for critical components"
            })
        
        if "e2e" not in test_types:
            recommendations.append({
                "priority": "medium",
                "recommendation": "Add end-to-end tests for user workflows"
            })
        
        return recommendations
    
    def run_test_suite(self):
        """Run complete test suite"""
        print("🚀 Running Complete Test Suite...")
        print("=" * 50)
        
        test_categories = [
            ("Unit Tests", "tests/unit/"),
            ("Integration Tests", "tests/integration/"),
            ("E2E Tests", "tests/e2e/"),
            ("Performance Tests", "tests/performance/")
        ]
        
        for category, test_path in test_categories:
            if os.path.exists(os.path.join(self.project_root, test_path)):
                print(f"\n📋 Running {category}...")
                self._run_test_category(category, test_path)
            else:
                print(f"⚠️ {category} directory not found")
    
    def _run_test_category(self, category, test_path):
        """Run tests for a specific category"""
        try:
            cmd = [
                "python", "-m", "pytest",
                test_path,
                "-v",
                "--tb=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(f"✅ {category} passed")
                self.test_results[category] = "passed"
            else:
                print(f"❌ {category} failed")
                print(f"Error: {result.stderr}")
                self.test_results[category] = "failed"
                
        except Exception as e:
            print(f"❌ Error running {category}: {e}")
            self.test_results[category] = "error"
    
    def generate_final_report(self):
        """Generate final comprehensive report"""
        print("\n📊 Final Test Report")
        print("=" * 50)
        
        # Test results summary
        passed_tests = sum(1 for result in self.test_results.values() if result == "passed")
        total_tests = len(self.test_results)
        
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 All test categories passed!")
        else:
            print("⚠️ Some test categories need attention")
        
        # Coverage summary
        if self.coverage_data:
            avg_coverage = sum(data["coverage_percent"] for data in self.coverage_data.values()) / len(self.coverage_data)
            print(f"📊 Average Coverage: {avg_coverage:.1f}%")
        
        # Recommendations
        recommendations = self._get_recommendations()
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                priority = rec["priority"]
                recommendation = rec["recommendation"]
                print(f"  {priority.upper()}: {recommendation}")
        
        # Save final report
        final_report = {
            "timestamp": datetime.now().isoformat(),
            "project": "KARMABOT1",
            "test_results": self.test_results,
            "coverage_data": self.coverage_data,
            "summary": {
                "tests_passed": passed_tests,
                "total_tests": total_tests,
                "average_coverage": avg_coverage if self.coverage_data else 0
            },
            "recommendations": recommendations
        }
        
        report_file = self.project_root / "final_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n📄 Final report saved to: {report_file}")


def main():
    """Main function to run test coverage analysis"""
    reporter = TestCoverageReporter()
    
    print("🧪 KARMABOT1 Test Coverage Analysis")
    print("=" * 50)
    
    # Run test suite
    reporter.run_test_suite()
    
    # Run coverage analysis
    reporter.run_coverage_analysis()
    
    # Generate final report
    reporter.generate_final_report()
    
    print("\n🎯 Test Coverage Analysis Complete!")
    print("Check the generated reports for detailed information.")


if __name__ == "__main__":
    main()
