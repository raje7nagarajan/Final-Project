# Personal UPI Usage and Financial Analyzer using LLMs

In today’s digital world, tracking personal finances has become more challenging than ever. With UPI-based transactions scattered across apps like Paytm, GPay, PhonePe, and more, users often struggle to gain a clear understanding of their spending habits.
This project bridges that gap. The AI-Powered UPI Statement Analyzer is a smart, intuitive tool that transforms fragmented UPI transaction data into meaningful financial insight. By leveraging advanced PDF parsing and state-of-the-art Large Language Models (LLMs), the system not only cleans and structures your transaction history, but also delivers actionable advice tailored to your financial behavior.

## Features

- **PDF Parsing & Extraction** – Handles diverse formats from Paytm, GPay, PhonePe
- **Structured Output** – Date, Vendor, Amount, Type, Category in clean CSV format
- **LLM-Powered Insights** – Financial summaries, savings tips, alerts
- **Spending Analysis** – Monthly comparisons, category breakdowns, top expenses
- **Interactive Dashboard** – Upload, analyze, visualize — all in one click

## Project Phases

### PDF Data Extraction & Parsing

**Libraries**: `PyMuPDF`, `pdfplumber`, `pdfminer.six`  
**Purpose**: Handle diverse PDF formats with varying text structures

**Logic**:
- Use regex to isolate transaction blocks (dates, vendor names, amounts)
- Normalize inconsistencies (e.g., separators `/`, `-`, vendor aliases)
- Support multilingual & fuzzy matching for transaction descriptions

---

### Data Cleaning & Structuring

**Libraries**: `pandas`, `re`, `datetime`  
**Tasks**:
- Parse multiline transactions and tag fields (Date, Amount, Vendor, Type)
- Handle OCR artifacts (misspellings, extra spaces)
- Store in structured DataFrame
- Add `Category` column using rule-based or NLP techniques

---

### LLM Integration

**Models**: `LLaMA`, `GPT-4`, `Mistral`, or open-weight Hugging Face models

**Steps**:
- Provide monthly summaries to the model
- Prompt the LLM to generate:
  - Category breakdowns
  - Financial health scores
  - Suggestions over saving targets
- Store insights for UI display

### Financial Analysis Logic

**Spending Analysis**:
- Aggregate totals by category
- Compare monthly behavior
- Detect income vs expense anomalies
- Flag high-value & recurring payments

**Custom Rules (optional ML layer)**:
- Define behavioral thresholds (e.g., >20% on Dining triggers alert)
- Scorecard for spending habits

### Deployment: Gradio Dashboard

**Gradio Interface**:
- Upload PDF → Analyze → Download CSV
- AI summary shown in textbox/markdown block

**Host on Hugging Face Spaces**:
- Easy launch, handles front-end/backend
- Free tier or upgrade for higher resource needs


