# Security Policies

## Generic Security Policies

PII Policy: [block_pii_in_tool_args.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/block_pii_in_tool_args.py)

Regex Patterns Policy: [block_regex_patterns.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/block_regex_patterns.py)

## MCP Server-Specific Policies

GitHub Policy: [github_enforce_single_repo.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/github_enforce_single_repo.py)

Heroku Policy: [heroku_enforce_single_app.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/heroku_enforce_single_app.py)

Linear Policy: [linear_enforce_single_team.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/linear_enforce_single_team.py)

Linear & Sentry Policy: [linear_sentry_rules.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/linear_sentry_rules.py)

Notion Policy: [notion_enforce_single_page.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/notion_enforce_single_page.py)

PayPal Policy: [paypal_policies.py](https://github.com/codeintegrity-ai/tramlines-gateway/blob/main/src/tramlines/guardrail/policies/paypal_policies.py)
