---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
license: Complete terms in LICENSE.txt
---

# MCP Server Development Guide

## Overview

Create MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools.

## Process

### Phase 1: Deep Research and Planning

#### 1.1 Understand Modern MCP Design

- **API Coverage vs. Workflow Tools:** Balance comprehensive API endpoint coverage with specialized workflow tools.
- **Tool Naming and Discoverability:** Clear, descriptive tool names help agents find the right tools quickly.
- **Context Management:** Agents benefit from concise tool descriptions and the ability to filter/paginate results.
- **Actionable Error Messages:** Error messages should guide agents toward solutions with specific suggestions and next steps.

#### 1.2 Study MCP Protocol Documentation

Start with the sitemap: https://modelcontextprotocol.io/sitemap.xml

Key pages to review:
- Specification overview and architecture
- Transport mechanisms (streamable HTTP, stdio)
- Tool, resource, and prompt definitions

#### 1.3 Study Framework Documentation

**Recommended stack:**
- **Language**: TypeScript (high-quality SDK support)
- **Transport**: Streamable HTTP for remote servers, stdio for local servers.

### Phase 2: Implementation

#### 2.1 Set Up Project Structure

#### 2.2 Implement Core Infrastructure

Create shared utilities:
- API client with authentication
- Error handling helpers
- Response formatting (JSON/Markdown)
- Pagination support

#### 2.3 Implement Tools

For each tool:
- Input Schema: Use Zod (TypeScript) or Pydantic (Python)
- Output Schema: Define outputSchema where possible
- Tool Description: Concise summary of functionality
- Implementation: Async/await for I/O operations
- Annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint

### Phase 3: Review and Test

#### 3.1 Code Quality

Review for:
- No duplicated code (DRY principle)
- Consistent error handling
- Full type coverage

#### 3.2 Build and Test

**TypeScript:**
- Run `npm run build` to verify compilation
- Test with MCP Inspector: `npx @modelcontextprotocol/inspector`

**Python:**
- Verify syntax: `python -m py_compile your_server.py`
- Test with MCP Inspector

### Phase 4: Create Evaluations

After implementing your MCP server, create comprehensive evaluations to test its effectiveness.

#### 4.1 Understand Evaluation Purpose

Use evaluations to test whether LLMs can effectively use your MCP server to answer realistic, complex questions.

#### 4.2 Create 10 Evaluation Questions

1. **Tool Inspection**: List available tools and understand their capabilities
2. **Content Exploration**: Use READ-ONLY operations to explore available data
3. **Question Generation**: Create 10 complex, realistic questions
4. **Answer Verification**: Solve each question yourself to verify answers
