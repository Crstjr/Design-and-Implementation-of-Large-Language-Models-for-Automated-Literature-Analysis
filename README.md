# PDF Processing and LLM Analysis System

## Overview
This project is an automated **PDF processing system** that integrates **Large Language Models (LLMs)** for document analysis. It enables text extraction from PDFs, batch processing, interactive Q&A, and structured Markdown report generation. The system is designed for **academic research**, supporting multilingual analysis in **English and Chinese** using **iFLYTEK Spark 4.0 Ultra** via a **WebSocket API**.

## Features
- **PDF Text Extraction**: Uses `PDFMiner` for high-accuracy text retrieval.
- **Batch Processing**: Processes multiple PDF files simultaneously without interruptions.
- **LLM Integration**: Analyzes extracted content with `SparkApi.py`, enabling deep document understanding.
- **Interactive Q&A Mode**: Users can query processed content in real-time.
- **Markdown Report Generation**: Saves structured analysis results in `.md` format.
- **Error Handling and Resilience**:
  - Logs and manages errors (e.g., corrupted files, LLM timeouts).
  - Prevents a single failure from halting the entire batch process.
  - Provides real-time feedback to users.

## Installation
### **Prerequisites**
Ensure you have the following installed:
- **Python 3.8+**
- `pip` (Python package manager)
- Required dependencies (install via `requirements.txt`)

### **Setup**
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   cd your-repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3.Set up API credentials for SparkApi.py:
  Edit config.py (if applicable) with your API keys.



This **README.md** provides a **comprehensive guide** for users and contributors. Let me know if you’d like any modifications! 🚀
