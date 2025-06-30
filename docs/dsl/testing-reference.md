# Testing Reference

Testing your policies is essential to ensure they work correctly and don't block legitimate operations. Tramlines provides a testing framework to validate policy behavior.

## Basic Testing Structure

```python
from tramlines.guardrail.dsl.testing import simulate_calls, assert_allowed, assert_blocked
from tramlines.session import ToolCall

def test_policy_allows_normal_operation():
    """Test that normal operations are allowed."""
    calls = [
        ToolCall("get_user", {"user_id": "123"}),
        ToolCall("update_user", {"user_id": "123", "name": "New Name"})
    ]
    
    result = simulate_calls(my_policy, calls)
    assert_allowed(result)

def test_policy_blocks_dangerous_operation():
    """Test that dangerous operations are blocked."""
    calls = [
        ToolCall("delete_user", {"user_id": "123"})
    ]
    
    result = simulate_calls(my_policy, calls)
    assert_blocked(result, by_rule="Block dangerous operations")
```

## Testing Functions

### `simulate_calls(policy, calls)`
Simulates tool calls against a policy and returns a result for assertion.

### `assert_allowed(result)`
Asserts that the tool call was allowed.

### `assert_blocked(result, by_rule=None)`
Asserts that the tool call was blocked, optionally by a specific rule.

## Example Test Cases

```python
def test_github_single_repo_policy():
    """Test GitHub single repository enforcement."""
    
    # Should allow calls to same repository
    same_repo_calls = [
        ToolCall("get_repo", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("create_issue", {"owner": "octocat", "repo": "hello-world", "title": "Bug"})
    ]
    result = simulate_calls(github_policy, same_repo_calls)
    assert_allowed(result)
    
    # Should block calls to different repositories
    different_repo_calls = [
        ToolCall("get_repo", {"owner": "octocat", "repo": "hello-world"}),
        ToolCall("create_issue", {"owner": "octocat", "repo": "different-repo", "title": "Bug"})
    ]
    result = simulate_calls(github_policy, different_repo_calls)
    assert_blocked(result, by_rule="Enforce single repository")

def test_pii_detection_policy():
    """Test PII detection in tool arguments."""
    
    # Should allow normal data
    normal_calls = [
        ToolCall("create_issue", {"title": "Bug report", "body": "System not working"})
    ]
    result = simulate_calls(pii_policy, normal_calls)
    assert_allowed(result)
    
    # Should block PII data
    pii_calls = [
        ToolCall("create_issue", {"title": "Bug", "body": "Contact john@example.com"})
    ]
    result = simulate_calls(pii_policy, pii_calls)
    assert_blocked(result)
```

Testing ensures your policies work as expected and helps catch issues before deployment. 