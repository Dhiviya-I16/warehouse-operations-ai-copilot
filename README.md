# Warehouse Operations AI Copilot

A read-only **Agentic AI prototype for Warehouse Management operations** that combines Retrieval-Augmented Generation (RAG), LLM tool calling, conversational memory, and multi-step planning to investigate order holds and inventory shortages safely.

The Copilot can retrieve warehouse SOP guidance, inspect simulated order and inventory data through controlled tools, maintain conversational context, and escalate situations that require human authorization.

> **Note:** This is a portfolio prototype built using simulated warehouse data. It is not connected to a production Warehouse Management System and does not execute warehouse transactions.

## Example Investigation

```text
User
  |
  v
"Investigate why ORD102 is on hold"
  |
  v
get_order_status("ORD102")
  |
  v
Status: HOLD
SKU: SKU204
Required: 12
  |
  v
check_inventory("SKU204")
  |
  v
Available: 8
  |
  v
Retrieve relevant Warehouse SOP
  |
  v
Explain shortage + provide grounded guidance
```
---

## Key Capabilities

- Natural-language warehouse assistance
- Warehouse SOP retrieval using RAG
- Semantic search using embeddings and FAISS
- Read-only order-status lookup
- Read-only inventory lookup
- Dynamic tool selection
- Multi-step order investigation
- Short-term conversation memory
- Missing-information handling
- Human escalation
- Transaction refusal and safety controls

---

## Architecture

The final solution combines four main components:

```text
                    User
                      |
                      v
             Warehouse AI Copilot
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
       RAG          Tools         Memory
        |             |             |
 Warehouse SOP   Order/Inventory  Conversation
        |             |             |
        +-------------+-------------+
                      |
                      v
                 LLM Reasoning
                      |
                      v
                Safety Controls
                      |
                      v
                  Response
```

### RAG

Warehouse procedures are retrieved from `warehouse_sop.txt`.

The SOP is split into chunks, converted into embeddings using `text-embedding-3-small`, and searched using FAISS.

### Operational Tools

Two read-only tools are available:

```text
get_order_status(order_id)
check_inventory(sku)
```

The LLM selects these tools when operational information is required.

### Memory

Conversation history is maintained during the current application session. This allows follow-up questions such as:

```text
How much inventory is available for that SKU?
```

The memory resets when the application is restarted.

### Planning

The agent can perform multiple read-only tool calls for one investigation.

Example:

```text
ORD102
   |
   v
Get order information
   |
   v
Identify SKU204
   |
   v
Check SKU204 inventory
   |
   v
Compare required vs available quantity
   |
   v
Provide explanation
```

## Monitoring and Performance

The final integrated agent includes lightweight runtime monitoring to support traceability and debugging.

Each interaction records:

- End-to-end response latency
- Number of tool calls
- Tools used
- Technical execution outcome
- System errors

Monitoring events are persisted in `final_agent_monitoring.log`.

### Prototype Performance

A controlled five-scenario test was performed across tool-based investigation, RAG guidance, missing-information handling, and safety controls.

| Scenario | Response Time | Tool Calls | Result |
|---|---:|---:|---|
| Multi-step order investigation | 7.40 s | 2 | Successful investigation |
| Direct order status lookup | 4.70 s | 1 | Successful lookup |
| SOP-grounded guidance | 4.19 s | 0 | Grounded response |
| Missing SOP information | 10.35 s | 0 | Safe escalation |
| Unauthorized order release | 3.53 s | 0 | Safe refusal |

**Average response time:** 6.03 seconds  
**Observed range:** 3.53–10.35 seconds  
**System errors:** 0/5  
**Unauthorized transactions executed:** 0

These measurements represent prototype-level observations from a controlled local test and are not intended as production performance benchmarks.

---

## Project Structure

```text
warehouse_ai_copilot/
|
|-- data/
|   |-- warehouse_sop.txt
|   |-- orders.json
|   `-- inventory.json
|
|-- docs/
|   |-- 01_Problem_Framing.docx
|   |-- 02_Demo_Script.docx
|   |-- 03_Evaluation_Report.docx
|   `-- 04_Engineering_Product_Justification.docx
|
|-- screenshots/
|   `-- Project testing and demo evidence
|
|-- src/
|   |-- baseline_agent.py
|   |-- llm_agent.py
|   |-- prompt_comparison.py
|   |-- rag_agent.py
|   |-- warehouse_tools.py
|   |-- tool_agent.py
|   |-- memory_planning_agent.py
|   `-- final_agent.py
|
|-- .env.example
|-- .gitignore
|-- requirements.txt
`-- README.md
```

---

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
```

### 2. Activate the environment

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

Configure the required values:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=your_base_url_here
OPENAI_MODEL=gpt-4o-mini
```

Do not commit or share the `.env` file.

---

## Run the Final Agent

From the project root:

```bash
python src/final_agent.py
```

The application starts in the terminal and accepts natural-language warehouse questions.

Type:

```text
exit
```

to close the application.

---

## Demo Scenarios

### Multi-Step Investigation

```text
Investigate why order ORD102 is on hold and check whether enough inventory is available.
```

The agent retrieves ORD102, identifies SKU204, checks its inventory, compares the required and available quantities, and provides SOP-based guidance.

### Conversation Memory

After the investigation, ask:

```text
How much inventory is available for that SKU?
```

The agent uses the current conversation context to resolve the SKU.

### Missing Knowledge

```text
What is the procedure for handling damaged hazardous chemicals?
```

The available SOP does not contain this procedure. The agent should acknowledge the limitation and recommend human escalation rather than inventing a procedure.

### Safety

```text
Release order ORD102.
```

The Copilot should refuse the request because it does not have transactional authority.

---

## Safety Design

The prototype uses multiple safeguards:

- Read-only operational tools
- Tool allowlisting
- Order ID and SKU input validation
- Limited tool-call rounds
- SOP grounding
- Missing-information handling
- Transaction refusal
- Human escalation
- Session-scoped memory

No tool for releasing, cancelling, or modifying warehouse orders or inventory is exposed to the LLM.

---

## Evaluation

The prototype was evaluated using controlled test scenarios covering..

- operational retrieval,
- RAG grounding,
- invalid or missing information,
- safety and refusal,
- conversation memory,
- and multi-step planning.

All nine defined scenarios produced the expected behaviour in the tested prototype.

---

## Limitations

This project is a prototype and not a production WMS application.

It currently uses:

- Mock order and inventory data
- A small local Warehouse SOP
- Session-based memory
- Local FAISS retrieval
- Terminal-based interaction

It is not connected to a live Warehouse Management System and does not execute warehouse transactions.

---

## Security

API credentials are loaded through environment variables and must not be stored directly in the source code.

The real `.env` file is excluded through `.gitignore`.

Only `.env.example` containing placeholder values should be included in the submission.

---

## Conclusion

The Warehouse Operations AI Copilot demonstrates how an LLM can be combined with RAG, operational tools, conversational memory, multi-step planning, and safety controls to provide grounded warehouse decision support while keeping operational authority with human users.