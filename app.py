import re
import pandas as pd
import fitz  # PyMuPDF
import gradio as gr
import tempfile
import os
from groq import Groq
# Function to extract the text from the PDF
def extract_all_text_with_fitz(file_path):

    # Open the pdf from the mentioned path
    doc = fitz.open(file_path)
    full_text = ""

    # Looping through each pages in the PDF
    for page_number, page in enumerate(doc, start=1):

        # Reading all the data as text
        text = page.get_text("text")
        full_text += f"\n--- Page {page_number} ---\n{text}"

    # Returning the text
    return full_text.strip()

# Parsing the multiline text and structuring it
def parse_multiline_transactions(raw_text):

    # Spliting lines from the raw data
    lines = raw_text.splitlines()
    transactions = []

    # Identifying patterns using regrex
    date_pattern = re.compile(r"\d{2}[-/]\d{2}[-/]\d{4}")
    buffer = []

    # Looping each line to identify the complete transaction details
    for line in lines:

        # Remove unnecessary spaces white spaces
        line = line.strip()

        # Skip blank line
        if not line:
            continue

        # Check whether the date pattern matches
        if date_pattern.match(line):
            if buffer:
                #Saving previous transaction
                transactions.append(buffer)

            # Start new transaction date
            buffer = [line]
        else:
            # Continue current transaction
            buffer.append(line)

    # Add last transaction
    if buffer:
        transactions.append(buffer)

    parsed = []

    # Loop through each transaction block to extract structured data
    for entry in transactions:

        # Skip if transaction block is too short to be valid
        if len(entry) < 4:
            continue

        # Add transaction details
        date = entry[0]
        tx_type = entry[-1].upper()
        amount_line = entry[-2]
        description_lines = entry[1:-2]

        # Join description lines into a single string
        description = " ".join(description_lines).replace('\n', ' ').strip()

        # Remove commas from amount string
        amount_str = amount_line.replace(',', '')
        try:
            #Converting amount to float
            amount = float(amount_str)
        except ValueError:
            continue

        # Storing parsed transactions details
        parsed.append({
            "Date": pd.to_datetime(date, dayfirst=True, errors="coerce").strftime('%Y-%m-%d'),
            "Description": description,
            "Amount": amount,
            "Type": "Credit" if tx_type == "CR" else "Debit",
            "Category": categorize_transaction(description)
        })

    df = pd.DataFrame(parsed)
    df = df.dropna(subset=["Date", "Amount"])
    return df.reset_index(drop=True)

# Function to identify the categorize of transactions
def categorize_transaction(description):

    # Converting the decriptions to lower case
    description = description.lower()

    # Identifying different categories based on the description
    if any(word in description for word in ['salary', 'inft']):
        return "Income"
    elif any(word in description for word in ['amazon', 'flipkart', 'delhivery']):
        return "Shopping"
    elif any(word in description for word in ['swiggy', 'zomato', 'restaurant', 'subway']):
        return "Food & Dining"
    elif any(word in description for word in ['netflix', 'prime', 'subscription', 'mandate']):
        return "Subscriptions"
    elif any(word in description for word in ['electricity', 'water', 'gas']):
        return "Utilities"
    elif any(word in description for word in ['upi', 'paytm', 'gpay', 'phonepe']):
        return "UPI Transfer"
    elif any(word in description for word in ['rent', 'lease']):
        return "Rent"
    elif 'insurance' in description:
        return "Insurance"
    elif any(word in description for word in ['uber', 'ola', 'travel']):
        return "Transport"
    else:
        return "Others"

# Initialize Groq client with your API key
client = Groq(api_key="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")

# Function to identify the spend analsyis
def spend_analysis(df):
    # List to collect insight strings
    insights = []

    # Calculate total amount spent (Debit) and received (Credit)
    total_spent = df[df['Type'] == 'Debit']['Amount'].sum()
    total_received = df[df['Type'] == 'Credit']['Amount'].sum()

    # Group and sum debit amounts by category in descending order
    top_categories = df[df['Type'] == 'Debit'].groupby('Category')['Amount'].sum().sort_values(ascending=False)

    # Group by month and type, aggregate sums, and fill missing values with 0
    monthly_summary = df.groupby([df['Date'].str[:7], 'Type'])['Amount'].sum().unstack().fillna(0)

    # Add total spent and received to insights
    insights.append(f"Total Spent: ₹{total_spent:,.2f}")
    insights.append(f"Total Received: ₹{total_received:,.2f}")

    # Add category-wise spending breakdown
    insights.append("\nSpending by Category:")
    for cat, amt in top_categories.items():
        insights.append(f"   • {cat}: ₹{amt:,.2f}")

    # Add monthly summary of spending and income
    insights.append("\nMonthly Summary:")
    for month, row in monthly_summary.iterrows():
        spent = row.get('Debit', 0.0)       # Default to 0 if no debit for the month
        earned = row.get('Credit', 0.0)     # Default to 0 if no credit for the month
        balance = earned - spent            # Calculate monthly net balance
        emoji = "📉" if balance < 0 else "📈"  # Emoji reflects financial direction
        insights.append(f"   • {month}: Spent ₹{spent:,.2f}, Received ₹{earned:,.2f} → Net {emoji} ₹{balance:,.2f}")

    # Identify top 3 highest debit transactions for the period
    top_txns = df[df['Type'] == 'Debit'].sort_values(by='Amount', ascending=False).head(3)
    insights.append("\nTop 3 Expenses:")
    for _, row in top_txns.iterrows():
        insights.append(f"   • ₹{row['Amount']:,.2f} on {row['Date']} → {row['Description'][:40]}...")

    # Return the entire insight as a single string
    return "\n".join(insights)

# Function to get advice on financial data
def ask_for_financial_advice(summary_text):

    # Adding prompt
    prompt = f"""
  Evaluate the following bank transaction summary and generate detailed financial insights in a structured yet dynamic format:

 **AI PERSONAL FINANCE ASSISTANT**

 **MONTHYLY SUMMARY**
- Period Covered: [Month(s)]
- Total Income: ₹[Total Income]
- Total Expenses: ₹[Total Expenses]
- Net Balance: ₹[Income - Expenses]

**OBSERVATIONS & HIGHLIGHTS**
- Potential Overspending in: [Top Overspent Category]
- Most Recurring Expense: [Category or Vendor]
- Saving Ratio: [Savings %]%
- Notable Spikes: [Describe spikes in any particular month]

**TOP EXPENSE CATEGORIES**
1. [Category 1] – ₹[Amount]
2. [Category 2] – ₹[Amount]
3. [Category 3] – ₹[Amount]

**AREAS FOR OPTIMIZATION**
- Unnecessary Subscriptions: [Description if any]
- Transportation Costs seem high—consider alternatives like [suggestion]
- Dining Out Frequency: [Suggestion or Concern]

**SMART MONEY MOVES**
- Target Saving: ₹[Target] per month (based on habits)
- Set category-based limits using budgeting apps
- Tip: Automate transfers to a savings account on salary day

Finish with a one-line motivational quote based on the data.

### TRANSACTION SUMMARY:
{summary_text}

"""
    # Getting advice from ai
    response = client.chat.completions.create(
        # Choosing Groq model and role to it
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful and expert financial advisor."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=8000,
        temperature=0.7
    )

    # Returing the AI response
    return response.choices[0].message.content

def gradio_interface(pdf_file):
    try:
        file_path = pdf_file  # The uploaded PDF file path provided by Gradio

        # Extract raw text from the PDF
        raw_text = extract_all_text_with_fitz(file_path)

        # Parse the raw text into a structured DataFrame
        df = parse_multiline_transactions(raw_text)

        # If the DataFrame is empty, return an error message and no CSV
        if df.empty:
            return "Unable to extract transactions. Please check the PDF format.", None

        # Generate a summarized financial report from the DataFrame
        summary = spend_analysis(df)

        # Ask Groq model to produce financial suggestions
        insights = ask_for_financial_advice(summary)

        # Save the parsed transactions DataFrame to a temporary CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline='') as temp_csv:

            # Write the DataFrame to CSV
            df.to_csv(temp_csv.name, index=False)

            # Store the CSV path for returning
            csv_path = temp_csv.name

        # Returning the AI response and the CSV file for download
        return insights, csv_path

    except Exception as e:
        # If anything goes wrong, return the error message and no file
        return f"Error: {str(e)}", None

# Define the Gradio interface with upload input and dual output (text + downloadable file)
gr.Interface(
    fn=gradio_interface,
    # Upload button for user
    inputs=gr.File(label="Upload Transaction PDF"),
    outputs=[
        gr.Textbox(label="Financial Insights"),       # Text output for AI-generated advice
        gr.File(label="Download Parsed CSV")          # Downloadable CSV of parsed data
    ],
    title="Personal AI Finance Analyzer",             # Interface title
    description="Upload your bank statement PDF to receive financial advice + download a clean CSV version.",
    allow_flagging="manual"                            # Disable Gradio flagging UI
).launch(debug=True, share=True)                                  # Enable debug mode to see errors in console
