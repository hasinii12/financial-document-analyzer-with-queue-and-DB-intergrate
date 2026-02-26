## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai_tools import SerperDevTool
from crewai.tools import tool
from langchain_community.document_loaders import PyPDFLoader

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
class FinancialDocumentTool():
    @tool("Read Financial Document")
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        """Tool to read data from a pdf file from a path.
        
        Args:
            path: Path of the pdf file. Defaults to 'data/sample.pdf'.

        Returns:
            str: Full Financial Document file
        """
        
        docs = PyPDFLoader(file_path=path).load()

        full_report = ""
        for data in docs:
            # Clean and format the financial document data
            content = data.page_content
            
            # Remove extra whitespaces and format properly
            while "\n\n" in content:
                content = content.replace("\n\n", "\n")
                
            full_report += content + "\n"
            
        return full_report

## Creating Investment Analysis Tool
class InvestmentTool:
    @tool("Analyze Investment Data")
    def analyze_investment_tool(financial_document_data: str) -> str:
        """Analyzes investment data from a financial document.
        
        Args:
            financial_document_data: The financial document text to analyze.
            
        Returns:
            str: Investment analysis result.
        """
        # Process and analyze the financial document data
        processed_data = financial_document_data
        
        # Clean up the data format
        i = 0
        while i < len(processed_data):
            if processed_data[i:i+2] == "  ":  # Remove double spaces
                processed_data = processed_data[:i] + processed_data[i+1:]
            else:
                i += 1
                
        # TODO: Implement investment analysis logic here
        return "Investment analysis functionality to be implemented"

## Creating Risk Assessment Tool
class RiskTool:
    @tool("Create Risk Assessment")
    def create_risk_assessment_tool(financial_document_data: str) -> str:
        """Creates a risk assessment from financial document data.
        
        Args:
            financial_document_data: The financial document text to assess.
            
        Returns:
            str: Risk assessment result.
        """
        # TODO: Implement risk assessment logic here
        return "Risk assessment functionality to be implemented"
