"""Backend API tests for Local App Creator."""
import requests
import sys
import time
import json
from typing import Any

BASE_URL = "https://app-forge-2378.preview.emergentagent.com/api"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.notes_idea = "A personal notes app with title, body, created_at; list, view, delete; offline-friendly"
        
    def log(self, msg: str, level: str = "INFO"):
        print(f"[{level}] {msg}")
        
    def test(self, name: str, method: str, endpoint: str, expected_status: int, 
             data: dict = None, json_data: dict = None, timeout: int = 30) -> tuple[bool, Any]:
        """Run a single API test."""
        url = f"{self.base_url}/{endpoint}"
        self.tests_run += 1
        self.log(f"Testing {name}...", "TEST")
        
        try:
            headers = {'Content-Type': 'application/json'}
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=json_data or data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASS - {name} (status: {response.status_code})", "PASS")
            else:
                self.log(f"❌ FAIL - {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                self.log(f"Response: {response.text[:500]}", "DEBUG")
            
            try:
                return success, response.json() if response.text else {}
            except:
                return success, response.text
                
        except Exception as e:
            self.log(f"❌ FAIL - {name} - Error: {str(e)}", "FAIL")
            return False, {}
    
    def poll_until(self, endpoint: str, condition_fn, max_wait: int = 300, interval: int = 5) -> tuple[bool, Any]:
        """Poll an endpoint until condition is met or timeout."""
        start = time.time()
        while time.time() - start < max_wait:
            try:
                response = requests.get(f"{self.base_url}/{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if condition_fn(data):
                        return True, data
            except Exception as e:
                self.log(f"Poll error: {e}", "DEBUG")
            time.sleep(interval)
        return False, {}
    
    def run_all_tests(self):
        """Run all backend tests in sequence."""
        self.log("=" * 80, "INFO")
        self.log("Starting Backend API Tests", "INFO")
        self.log("=" * 80, "INFO")
        
        # B-1: System health
        self.log("\n--- B-1: System Health ---", "INFO")
        success, health = self.test("System Health", "GET", "system/health", 200)
        if success:
            required_fields = ["primary_available", "fallback_available", "model", "version", "product"]
            for field in required_fields:
                if field in health:
                    self.log(f"  ✓ {field}: {health[field]}", "INFO")
                else:
                    self.log(f"  ✗ Missing field: {field}", "FAIL")
        
        # B-2: Project CRUD
        self.log("\n--- B-2: Project CRUD ---", "INFO")
        success, project = self.test("Create Project", "POST", "projects", 201, 
                                     json_data={"name": "Test Notes App", "idea": self.notes_idea})
        if success and "id" in project:
            self.project_id = project["id"]
            self.log(f"  Project ID: {self.project_id}", "INFO")
            self.log(f"  State: {project.get('state')}", "INFO")
            self.log(f"  Workspace: {project.get('workspace_dir')}", "INFO")
            
            # List projects
            success, projects = self.test("List Projects", "GET", "projects", 200)
            if success and isinstance(projects, list):
                self.log(f"  Found {len(projects)} project(s)", "INFO")
            
            # Get project
            success, proj = self.test("Get Project", "GET", f"projects/{self.project_id}", 200)
            if success:
                self.log(f"  Retrieved project: {proj.get('name')}", "INFO")
        else:
            self.log("❌ CRITICAL: Failed to create project. Stopping tests.", "FAIL")
            return self.print_summary()
        
        # B-3: BRD Questions
        self.log("\n--- B-3: BRD Questions ---", "INFO")
        success, brd_resp = self.test("Generate BRD Questions", "POST", 
                                      f"projects/{self.project_id}/brd/questions", 200, timeout=90)
        if success:
            questions = brd_resp.get("questions", [])
            self.log(f"  Generated {len(questions)} questions", "INFO")
            if len(questions) > 0:
                self.log(f"  Sample question: {questions[0].get('text', '')[:100]}", "INFO")
        
        # Get BRD
        success, brd = self.test("Get BRD", "GET", f"projects/{self.project_id}/brd", 200)
        if success:
            self.log(f"  Questions: {len(brd.get('questions', []))}", "INFO")
            self.log(f"  Answers: {len(brd.get('answers', []))}", "INFO")
        
        # B-4: BRD Answers
        self.log("\n--- B-4: BRD Answers ---", "INFO")
        if brd.get("questions"):
            # Prepare answers for first 3 questions
            answers = []
            for i, q in enumerate(brd["questions"][:3]):
                answers.append({
                    "question_id": q["id"],
                    "question": q.get("text", ""),
                    "answer": f"Answer {i+1}: Single user, store notes in SQLite, basic CRUD list newest first"
                })
            
            success, brd_derived = self.test("Submit BRD Answers", "POST", 
                                            f"projects/{self.project_id}/brd/answers", 200,
                                            json_data={"answers": answers}, timeout=90)
            if success:
                maturity = brd_derived.get("maturity", 0)
                requirements = brd_derived.get("brd", {}).get("requirements", [])
                self.log(f"  Maturity score: {maturity}", "INFO")
                self.log(f"  Requirements: {len(requirements)}", "INFO")
                if maturity >= 1:
                    self.log(f"  ✓ Maturity >= 1", "PASS")
                else:
                    self.log(f"  ✗ Maturity < 1", "FAIL")
        
        # B-5: Architecture Detection
        self.log("\n--- B-5: Architecture Detection ---", "INFO")
        success, arch = self.test("Detect Architecture", "POST", 
                                 f"projects/{self.project_id}/architecture/detect", 200, timeout=60)
        if success:
            decision = arch.get("decision", {})
            kind = decision.get("kind")
            reasoning = decision.get("reasoning", [])
            requires_backend = decision.get("requires_backend")
            requires_database = decision.get("requires_database")
            self.log(f"  Kind: {kind}", "INFO")
            self.log(f"  Requires backend: {requires_backend}", "INFO")
            self.log(f"  Requires database: {requires_database}", "INFO")
            self.log(f"  Reasoning points: {len(reasoning)}", "INFO")
            
            valid_kinds = ["frontend_only", "api_driven", "db_backed", "backend_required", "full_stack"]
            if kind in valid_kinds:
                self.log(f"  ✓ Valid architecture kind", "PASS")
            else:
                self.log(f"  ✗ Invalid architecture kind: {kind}", "FAIL")
        
        # Get architecture
        success, arch_get = self.test("Get Architecture", "GET", 
                                     f"projects/{self.project_id}/architecture", 200)
        
        # B-6: Architecture Override (blocking test)
        self.log("\n--- B-6: Architecture Override (Blocking) ---", "INFO")
        success, override_blocked = self.test("Override to frontend_only (should block)", "POST",
                                             f"projects/{self.project_id}/architecture/override", 200,
                                             json_data={
                                                 "forced_architecture": "frontend_only",
                                                 "allow_limited_prototype": False
                                             })
        if success:
            blocked = override_blocked.get("decision", {}).get("blocked")
            self.log(f"  Blocked: {blocked}", "INFO")
            if blocked:
                self.log(f"  ✓ Correctly blocked frontend_only without prototype flag", "PASS")
            else:
                self.log(f"  ✗ Should have blocked but didn't", "FAIL")
        
        # Override with allow_limited_prototype
        success, override_allowed = self.test("Override to frontend_only (with prototype flag)", "POST",
                                             f"projects/{self.project_id}/architecture/override", 200,
                                             json_data={
                                                 "forced_architecture": "frontend_only",
                                                 "allow_limited_prototype": True
                                             })
        if success:
            blocked = override_allowed.get("decision", {}).get("blocked")
            self.log(f"  Blocked: {blocked}", "INFO")
            if not blocked:
                self.log(f"  ✓ Correctly allowed with prototype flag", "PASS")
            else:
                self.log(f"  ✗ Should have allowed but blocked", "FAIL")
        
        # Reset to detected architecture for pipeline
        self.test("Re-detect Architecture", "POST", 
                 f"projects/{self.project_id}/architecture/detect", 200, timeout=60)
        
        # B-7: Plan Generation
        self.log("\n--- B-7: Plan Generation ---", "INFO")
        success, plan = self.test("Generate Plan", "POST", 
                                 f"projects/{self.project_id}/plan", 200, timeout=90)
        if success:
            files = plan.get("plan", {}).get("files", [])
            self.log(f"  Plan files: {len(files)}", "INFO")
            
            mandatory_files = [
                "backend/requirements.txt", "backend/database.py", "backend/models.py",
                "backend/schemas.py", "backend/main.py", "frontend/package.json",
                "frontend/vite.config.js", "frontend/index.html", "frontend/src/main.jsx",
                "frontend/src/styles.css", "frontend/src/api.js", "frontend/src/App.jsx",
                "README.md"
            ]
            
            # Handle both string and dict formats
            file_paths = []
            for f in files:
                if isinstance(f, str):
                    file_paths.append(f)
                elif isinstance(f, dict):
                    file_paths.append(f.get("path", ""))
            missing = [f for f in mandatory_files if f not in file_paths]
            
            if len(files) >= 13:
                self.log(f"  ✓ Has >= 13 files", "PASS")
            else:
                self.log(f"  ✗ Expected >= 13 files, got {len(files)}", "FAIL")
            
            if not missing:
                self.log(f"  ✓ All mandatory files present", "PASS")
            else:
                self.log(f"  ✗ Missing files: {missing}", "FAIL")
        
        # B-8: Pipeline Generation
        self.log("\n--- B-8: Pipeline Generation ---", "INFO")
        success, gen_resp = self.test("Trigger Pipeline", "POST", 
                                     f"projects/{self.project_id}/generate", 200)
        if success:
            self.log(f"  Pipeline started: {gen_resp.get('status')}", "INFO")
            
            # Poll for completion
            self.log("  Polling for pipeline completion (max 5 minutes)...", "INFO")
            poll_success, final_status = self.poll_until(
                f"projects/{self.project_id}/generate/status",
                lambda d: not d.get("running", True),
                max_wait=360,  # 6 minutes for safety
                interval=5
            )
            
            if poll_success:
                state = final_status.get("state")
                build_status = final_status.get("last_build_status")
                acceptance_status = final_status.get("last_acceptance_status")
                
                self.log(f"  Final state: {state}", "INFO")
                self.log(f"  Build status: {build_status}", "INFO")
                self.log(f"  Acceptance status: {acceptance_status}", "INFO")
                
                if state == "Export" and acceptance_status in ["PASS", "PARTIAL"]:
                    self.log(f"  ✓ Pipeline completed successfully", "PASS")
                else:
                    self.log(f"  ⚠ Pipeline completed but state/status unexpected", "WARN")
            else:
                self.log(f"  ✗ Pipeline did not complete within timeout", "FAIL")
        else:
            self.log("❌ CRITICAL: Failed to start pipeline. Skipping remaining tests.", "FAIL")
            return self.print_summary()
        
        # B-9: Files
        self.log("\n--- B-9: Files ---", "INFO")
        success, files_resp = self.test("List Files", "GET", 
                                       f"projects/{self.project_id}/files", 200)
        if success:
            files = files_resp.get("files", [])
            self.log(f"  Total files: {len(files)}", "INFO")
            
            if len(files) >= 15:
                self.log(f"  ✓ Has >= 15 files", "PASS")
            else:
                self.log(f"  ✗ Expected >= 15 files, got {len(files)}", "FAIL")
            
            # Check for key files
            file_paths = [f.get("path") for f in files]
            if "backend/main.py" in file_paths:
                self.log(f"  ✓ backend/main.py present", "PASS")
            if "frontend/package.json" in file_paths:
                self.log(f"  ✓ frontend/package.json present", "PASS")
        
        # Get file content
        success, content = self.test("Get File Content", "GET",
                                    f"projects/{self.project_id}/files/content?path=backend/main.py", 200)
        if success and isinstance(content, str):
            if "FastAPI" in content:
                self.log(f"  ✓ backend/main.py contains 'FastAPI'", "PASS")
            else:
                self.log(f"  ✗ backend/main.py missing 'FastAPI'", "FAIL")
        
        # B-10: Builds
        self.log("\n--- B-10: Builds ---", "INFO")
        success, builds = self.test("Get Builds", "GET", 
                                   f"projects/{self.project_id}/builds", 200)
        if success:
            build_list = builds.get("builds", [])
            self.log(f"  Build records: {len(build_list)}", "INFO")
            
            if len(build_list) >= 1:
                self.log(f"  ✓ At least one build record", "PASS")
                latest = build_list[0]
                overall = latest.get("overall_status")
                self.log(f"  Overall status: {overall}", "INFO")
                if overall in ["PASS", "PARTIAL"]:
                    self.log(f"  ✓ Build status is PASS or PARTIAL", "PASS")
            else:
                self.log(f"  ✗ No build records found", "FAIL")
        
        # B-11: Acceptance
        self.log("\n--- B-11: Acceptance ---", "INFO")
        success, acceptance = self.test("Get Acceptance", "GET",
                                       f"projects/{self.project_id}/acceptance", 200)
        if success:
            report = acceptance.get("report", {})
            overall = report.get("overall")
            checks = report.get("checks", [])
            coverage = report.get("requirement_coverage", {})
            
            self.log(f"  Overall: {overall}", "INFO")
            self.log(f"  Checks: {len(checks)}", "INFO")
            self.log(f"  Coverage: {coverage}", "INFO")
            
            if overall in ["PASS", "PARTIAL"]:
                self.log(f"  ✓ Overall status is PASS or PARTIAL", "PASS")
            if len(checks) > 0:
                self.log(f"  ✓ Checks list non-empty", "PASS")
            if coverage:
                self.log(f"  ✓ Requirement coverage present", "PASS")
        
        # B-12: Export
        self.log("\n--- B-12: Export ---", "INFO")
        success, export = self.test("Get Export", "GET",
                                   f"projects/{self.project_id}/export", 200)
        if success:
            exp = export.get("export", {})
            files_count = exp.get("files", 0)
            secrets = exp.get("secret_findings", -1)
            manifest = exp.get("manifest_path")
            
            self.log(f"  Files: {files_count}", "INFO")
            self.log(f"  Secret findings: {secrets}", "INFO")
            self.log(f"  Manifest: {manifest}", "INFO")
            
            if files_count > 0:
                self.log(f"  ✓ Files > 0", "PASS")
            if secrets == 0:
                self.log(f"  ✓ Secret findings == 0", "PASS")
            if manifest:
                self.log(f"  ✓ Manifest path set", "PASS")
        
        # Get manifest
        success, manifest = self.test("Get Export Manifest", "GET",
                                     f"projects/{self.project_id}/export/manifest", 200)
        if success:
            excluded = manifest.get("excluded_dirs", [])
            self.log(f"  Excluded dirs: {excluded}", "INFO")
            if "node_modules" in excluded and "__pycache__" in excluded:
                self.log(f"  ✓ Manifest contains node_modules and __pycache__", "PASS")
        
        # Download export
        try:
            url = f"{self.base_url}/projects/{self.project_id}/export/download"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                content_length = int(response.headers.get("content-length", 0))
                self.log(f"  Content-Type: {content_type}", "INFO")
                self.log(f"  Content-Length: {content_length}", "INFO")
                
                if "application/zip" in content_type and content_length > 1000:
                    self.tests_passed += 1
                    self.log(f"  ✓ Export download successful", "PASS")
                else:
                    self.log(f"  ✗ Export download invalid", "FAIL")
                self.tests_run += 1
            else:
                self.log(f"  ✗ Export download failed: {response.status_code}", "FAIL")
                self.tests_run += 1
        except Exception as e:
            self.log(f"  ✗ Export download error: {e}", "FAIL")
            self.tests_run += 1
        
        # B-13: Events
        self.log("\n--- B-13: Events ---", "INFO")
        success, events = self.test("Get Events", "GET",
                                   f"projects/{self.project_id}/events", 200)
        if success:
            event_list = events if isinstance(events, list) else []
            self.log(f"  Total events: {len(event_list)}", "INFO")
            
            event_types = [e.get("type") for e in event_list]
            expected_types = [
                "project.created", "brd.questions.generated", "brd.derived",
                "architecture.detected", "plan.generated", "generation.started",
                "generation.completed", "build.started", "build.completed",
                "acceptance.completed", "export.completed"
            ]
            
            found_types = [t for t in expected_types if t in event_types]
            self.log(f"  Found event types: {found_types}", "INFO")
            
            if len(event_list) > 0:
                self.log(f"  ✓ Events list non-empty", "PASS")
            if len(found_types) >= 8:
                self.log(f"  ✓ Found {len(found_types)} expected event types", "PASS")
        
        # B-14: SSE (basic check)
        self.log("\n--- B-14: SSE Stream (basic check) ---", "INFO")
        try:
            url = f"{self.base_url}/projects/{self.project_id}/events/stream"
            response = requests.get(url, stream=True, timeout=5)
            content_type = response.headers.get("content-type", "")
            
            if "text/event-stream" in content_type:
                self.log(f"  ✓ Content-Type is text/event-stream", "PASS")
                self.tests_passed += 1
                
                # Try to read first event
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("event:"):
                        self.log(f"  ✓ Received SSE event: {line}", "PASS")
                        break
            else:
                self.log(f"  ✗ Wrong content-type: {content_type}", "FAIL")
            self.tests_run += 1
        except Exception as e:
            self.log(f"  ⚠ SSE test skipped (will verify via frontend): {e}", "WARN")
            self.tests_run += 1
        
        # B-15: Honesty Check (architecture blocking)
        self.log("\n--- B-15: Honesty Check ---", "INFO")
        # Create a new project for this test
        success, test_proj = self.test("Create Test Project for Honesty", "POST", "projects", 201,
                                      json_data={"name": "Honesty Test", "idea": self.notes_idea})
        if success and "id" in test_proj:
            test_id = test_proj["id"]
            
            # Generate BRD
            self.test("Generate BRD for Honesty Test", "POST",
                     f"projects/{test_id}/brd/questions", 200, timeout=90)
            
            # Force frontend_only without prototype flag
            success, override = self.test("Override to frontend_only (no prototype)", "POST",
                                        f"projects/{test_id}/architecture/override", 200,
                                        json_data={
                                            "forced_architecture": "frontend_only",
                                            "allow_limited_prototype": False
                                        })
            
            # Try to generate - should fail with 409
            success, gen_fail = self.test("Trigger Pipeline (should fail 409)", "POST",
                                         f"projects/{test_id}/generate", 409)
            if success:
                self.log(f"  ✓ Correctly blocked with 409 architecture_blocked", "PASS")
            else:
                self.log(f"  ✗ Should have returned 409 but didn't", "FAIL")
            
            # Cleanup
            self.test("Delete Test Project", "DELETE", f"projects/{test_id}", 204)
        
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        self.log("\n" + "=" * 80, "INFO")
        self.log("BACKEND TEST SUMMARY", "INFO")
        self.log("=" * 80, "INFO")
        self.log(f"Tests Run: {self.tests_run}", "INFO")
        self.log(f"Tests Passed: {self.tests_passed}", "INFO")
        self.log(f"Tests Failed: {self.tests_run - self.tests_passed}", "INFO")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%", "INFO")
        self.log("=" * 80, "INFO")
        
        return 0 if self.tests_passed == self.tests_run else 1


if __name__ == "__main__":
    tester = APITester()
    sys.exit(tester.run_all_tests())
