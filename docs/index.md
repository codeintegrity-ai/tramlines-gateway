---
hide:
  - navigation
  - toc
---

# Welcome to Tramlines!

Tramlines is a **MCP gateway proxy server** that sits between AI agents and MCP servers, providing centralized control for observability and security. Think of it as a security checkpoint where every tool call request passes through Tramlines and gets evaluated against your security policies before reaching the actual MCP server.

## Why You Need Tramlines

MCP servers expose powerful tools to AI agents without built-in security controls, leaving your systems vulnerable to data exfiltration, system compromise, privilege escalation, and tool poisoning attacks. Tramlines provides essential protection through policy-based security with simple syntax, real-time attack blocking, session tracking for multi-step threats, complete audit trails, and drop-in integration that works with any existing MCP setup.

## How It Works

```mermaid
%%{init: {'theme':'dark', 'themeVariables': { 'primaryColor': '#10b981', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#34d399', 'lineColor': '#64748b', 'secondaryColor': '#059669', 'tertiaryColor': '#f59e0b', 'background': '#1e293b', 'mainBkg': '#2d3748', 'secondBkg': '#10b981', 'tertiaryBkg': '#f59e0b'}}}%%
graph LR
    A[MCP Client] --> B[Tramlines MCP Proxy]
    B --> C{Security Check}
    C -->|Allow| D[MCP Server]
    C -->|Block| E[Security Alert]
    D --> F[Tool Execution]

    classDef default fill:#2d3748,stroke:#64748b,stroke-width:2px,color:#f8fafc
    classDef tramlines fill:#059669,stroke:#10b981,stroke-width:3px,color:#ffffff,font-weight:bold
    classDef decision fill:#d97706,stroke:#f59e0b,stroke-width:2px,color:#ffffff
    classDef server fill:#2563eb,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef alert fill:#dc2626,stroke:#ef4444,stroke-width:2px,color:#ffffff

    class B tramlines
    class C decision
    class D server
    class E alert
```

The process is straightforward: when an AI agent makes a tool call, Tramlines intercepts it and runs security policies to evaluate the request, making an allow or block decision. Safe requests proceed to the MCP server while dangerous ones are blocked and logged for security review.

## See the Difference

**Without Tramlines:**

```
AI Agent → "delete all log files" → MCP Server → Files deleted ❌
```

**With Tramlines:**

```
AI Agent → "delete all log files" → Tramlines → BLOCKED → Security Alert ✅
```

---
