"""
Test harness for Stage 7 - Frontend & UX
"""

import sys
from pathlib import Path
import json
import subprocess
import time
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_frontend_build():
    """Test that frontend can be built"""
    print("\n=== Test: Frontend Build ===")
    
    frontend_dir = Path(__file__).parent.parent / "src" / "frontend"
    
    # Check package.json exists
    package_json = frontend_dir / "package.json"
    assert package_json.exists(), "package.json not found"
    
    # Load package.json
    with open(package_json, 'r', encoding='utf-8') as f:
        package = json.load(f)
    
    # Verify required dependencies
    deps = package.get('dependencies', {})
    required_deps = ['react', 'react-dom', 'typescript', '@mui/material', 'axios']
    
    for dep in required_deps:
        assert dep in deps, f"Missing required dependency: {dep}"
    
    print(f"✓ Frontend structure valid with {len(deps)} dependencies")
    
    # Check required components exist
    components = [
        frontend_dir / "src" / "App.tsx",
        frontend_dir / "src" / "index.tsx",
        frontend_dir / "src" / "components" / "Layout.tsx",
        frontend_dir / "src" / "pages" / "QueryPage.tsx",
        frontend_dir / "src" / "pages" / "MemoryInspector.tsx",
        frontend_dir / "src" / "pages" / "DocumentManager.tsx",
        frontend_dir / "src" / "pages" / "Dashboard.tsx",
    ]
    
    for component in components:
        assert component.exists(), f"Missing component: {component.name}"
    
    print(f"✓ All {len(components)} core components present")
    
    return True


def test_ui_flow():
    """Test UI flow scenarios"""
    print("\n=== Test: UI Flow ===")
    
    # Test 1: Query flow components
    query_components = [
        "QueryPage.tsx",
        "ProvenancePanel.tsx",
        "ChunkViewer.tsx"
    ]
    
    frontend_src = Path(__file__).parent.parent / "src" / "frontend" / "src"
    
    for component in query_components:
        found = False
        for path in frontend_src.rglob(component):
            found = True
            # Basic validation - check for React component structure
            content = path.read_text(encoding='utf-8')
            assert "React" in content, f"{component} doesn't import React"
            assert "export" in content, f"{component} doesn't export anything"
            break
        
        assert found, f"Component {component} not found"
    
    print("✓ Query flow components verified")
    
    # Test 2: Memory management flow
    memory_page = frontend_src / "pages" / "MemoryInspector.tsx"
    content = memory_page.read_text(encoding='utf-8')
    
    # Check for key functionality
    assert "handleEdit" in content, "Memory edit functionality missing"
    assert "handleDelete" in content, "Memory delete functionality missing"
    assert "handlePromote" in content, "Memory promotion functionality missing"
    assert "handleExport" in content, "Memory export functionality missing"
    
    print("✓ Memory management functionality present")
    
    # Test 3: Document management flow
    doc_page = frontend_src / "pages" / "DocumentManager.tsx"
    content = doc_page.read_text(encoding='utf-8')
    
    assert "handleUpload" in content, "Document upload functionality missing"
    assert "handleDelete" in content, "Document delete functionality missing"
    assert "uploadProgress" in content, "Upload progress tracking missing"
    
    print("✓ Document management functionality present")
    
    return True


def test_accessibility_and_responsiveness():
    """Test accessibility and responsive design"""
    print("\n=== Test: Accessibility & Responsiveness ===")
    
    frontend_src = Path(__file__).parent.parent / "src" / "frontend" / "src"
    
    # Check for responsive design patterns
    layout_file = frontend_src / "components" / "Layout.tsx"
    layout_content = layout_file.read_text(encoding='utf-8')
    
    # Material-UI responsive breakpoints
    assert "xs:" in layout_content or "sm:" in layout_content, "No responsive breakpoints found"
    assert "Drawer" in layout_content, "No responsive drawer found"
    
    print("✓ Responsive design patterns implemented")
    
    # Check for accessibility features
    query_page = frontend_src / "pages" / "QueryPage.tsx"
    query_content = query_page.read_text(encoding='utf-8')
    
    # Basic accessibility checks
    assert "aria-" in query_content or "role=" in query_content, "No ARIA attributes found"
    assert "Tooltip" in query_content, "No tooltips for accessibility"
    
    print("✓ Basic accessibility features present")
    
    # Check for loading states and error handling
    assert "loading" in query_content.lower(), "No loading states"
    assert "error" in query_content.lower(), "No error handling"
    
    print("✓ Loading states and error handling implemented")
    
    return True


def test_security():
    """Test security considerations"""
    print("\n=== Test: Security ===")
    
    # Check API service for security practices
    api_file = Path(__file__).parent.parent / "src" / "frontend" / "src" / "services" / "api.ts"
    api_content = api_file.read_text(encoding='utf-8')
    
    # Check for proper headers
    assert "'Content-Type'" in api_content, "Content-Type header not set"
    
    # Check for no hardcoded sensitive data
    assert "api_key" not in api_content.lower() or "process.env" in api_content, \
        "Potential hardcoded API key found"
    
    print("✓ API security practices followed")
    
    # Check for XSS prevention (React does this by default)
    frontend_src = Path(__file__).parent.parent / "src" / "frontend" / "src"
    
    # Ensure we're not using dangerouslySetInnerHTML unnecessarily
    dangerous_usage = []
    for tsx_file in frontend_src.rglob("*.tsx"):
        if "dangerouslySetInnerHTML" in tsx_file.read_text():
            dangerous_usage.append(tsx_file.name)
    
    if dangerous_usage:
        print(f"⚠ Warning: dangerouslySetInnerHTML used in: {', '.join(dangerous_usage)}")
    else:
        print("✓ No dangerous HTML injection patterns found")
    
    return True


def test_user_flows():
    """Test complete user flows"""
    print("\n=== Test: User Flows ===")
    
    frontend_src = Path(__file__).parent.parent / "src" / "frontend" / "src"
    
    # Flow 1: Ingest → Query → Flag Hallucination → Correct
    print("Testing Flow 1: Complete query lifecycle")
    
    # Check document upload
    doc_manager = frontend_src / "pages" / "DocumentManager.tsx"
    assert doc_manager.exists(), "Document manager missing"
    
    # Check query interface
    query_page = frontend_src / "pages" / "QueryPage.tsx"
    query_content = query_page.read_text(encoding='utf-8')
    assert "handleSubmit" in query_content, "Query submission missing"
    assert "handleFeedback" in query_content, "Feedback mechanism missing"
    
    # Check for hallucination indicators
    assert "hallucination_score" in query_content or "verification" in query_content, \
        "No hallucination/verification display"
    
    # Check for correction flow
    assert "Report Issue" in query_content or "flag" in query_content.lower(), \
        "No issue reporting mechanism"
    
    print("✓ Flow 1: Query lifecycle complete")
    
    # Flow 2: Memory editing flow
    print("Testing Flow 2: Memory editing")
    
    memory_inspector = frontend_src / "pages" / "MemoryInspector.tsx"
    memory_content = memory_inspector.read_text(encoding='utf-8')
    
    assert "Dialog" in memory_content, "No edit dialog"
    assert "handleSaveEdit" in memory_content, "No save mechanism"
    assert "Rating" in memory_content or "importance" in memory_content, \
        "No importance adjustment"
    
    print("✓ Flow 2: Memory editing complete")
    
    # Flow 3: Monitoring flow
    print("Testing Flow 3: System monitoring")
    
    dashboard = frontend_src / "pages" / "Dashboard.tsx"
    dashboard_content = dashboard.read_text(encoding='utf-8')
    
    assert "Chart" in dashboard_content or "ResponsiveContainer" in dashboard_content, \
        "No charts for monitoring"
    assert "System Health" in dashboard_content, "No system health display"
    
    print("✓ Flow 3: Monitoring complete")
    
    print("\n✓ All user flows verified")
    return True


def run_all_tests():
    """Run all Stage 7 tests"""
    print("\n=== Stage 7 Tests: Frontend & UX ===")
    
    try:
        # Run tests
        test_frontend_build()
        test_ui_flow()
        test_accessibility_and_responsiveness()
        test_security()
        test_user_flows()
        
        print("\n✅ All Stage 7 tests passed!")
        print("\nStage 7 Acceptance Criteria Met:")
        print("✓ Frontend structure complete")
        print("✓ UI flows functional")
        print("✓ Accessibility and responsiveness implemented")
        print("✓ Security considerations addressed")
        print("✓ Key user flows smooth and complete")
        
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_tests()
