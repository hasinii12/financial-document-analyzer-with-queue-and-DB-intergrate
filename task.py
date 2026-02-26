## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier
from tools import search_tool, FinancialDocumentTool

## Creating a task to help solve user's query
analyze_financial_document = Task(
    description=(
        "Analyze the uploaded financial document to answer the user's query: {query}\n"
        "Read the financial document carefully using the provided tool.\n"
        "Extract key financial metrics, performance indicators, and relevant data points.\n"
        "Identify any notable trends, risks, or opportunities based strictly on the document content.\n"
        "Provide investment-relevant insights supported by specific data from the document.\n"
        "Search for relevant market context if needed to supplement the document analysis."
    ),
    expected_output=(
        "A structured financial analysis report that includes:\n"
        "1. A summary of the key financial metrics found in the document\n"
        "2. Analysis of financial performance and trends based on the data\n"
        "3. Identified risks and opportunities supported by document evidence\n"
        "4. Answers to the user's specific query with citations from the document\n"
        "5. A disclaimer reminding the user to consult a licensed financial advisor before making investment decisions"
    ),
    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description=(
        "Based on the financial document data, provide evidence-based investment analysis for: {query}\n"
        "Use only data present in the financial document to support investment insights.\n"
        "Assess the company's financial health using standard metrics (P/E, revenue growth, margins, etc.).\n"
        "Provide balanced investment considerations — both positive signals and risk factors.\n"
        "Do not fabricate data or recommend specific investment products without basis in the document."
    ),
    expected_output=(
        "A clear investment analysis that includes:\n"
        "1. Key financial ratios and what they indicate about the company\n"
        "2. Balanced assessment of investment merits and concerns from the document data\n"
        "3. Relevant market context where appropriate\n"
        "4. Clear disclaimer that this is informational analysis, not personalized financial advice"
    ),
    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description=(
        "Perform a thorough risk assessment based on the financial document for: {query}\n"
        "Identify specific risk factors evidenced in the financial data (liquidity, leverage, market risks, etc.).\n"
        "Use standard risk frameworks and cite specific metrics from the document.\n"
        "Provide a balanced assessment — do not overstate or understate risks.\n"
        "Include both company-specific risks and relevant industry/market risks."
    ),
    expected_output=(
        "A structured risk assessment including:\n"
        "1. Key risk factors identified from the document with supporting data\n"
        "2. Risk severity ratings based on financial metrics\n"
        "3. Mitigating factors also present in the document\n"
        "4. Overall risk profile summary grounded in the actual financial data"
    ),
    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

verification = Task(
    description=(
        "Verify that the uploaded file is a valid financial document.\n"
        "Check for standard financial document characteristics: financial statements, "
        "numerical data, fiscal periods, company identifiers, and financial terminology.\n"
        "Confirm that key data was extracted correctly and flag any anomalies."
    ),
    expected_output=(
        "A verification report stating:\n"
        "1. Whether the document is a valid financial document (yes/no with reasoning)\n"
        "2. Key document details identified (company name, period, document type)\n"
        "3. Any data quality issues or anomalies found\n"
        "4. Confirmation that the document is suitable for financial analysis"
    ),
    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False
)
