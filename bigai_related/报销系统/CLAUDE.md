# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese expense management and procurement automation system that processes invoices and generates standardized Excel reports for reimbursement and procurement requests. The system uses OCR technology to extract information from PDF invoices and images.

## Key Commands

### Running the Main Expense Request System
```bash
# Process PDF invoices from a folder
python expense_request.py "/path/to/invoice/folder"

# Example usage
python expense_request.py "/Users/lr-2002/Documents/报销材料/6.27/发票"
```

### Running the Procurement System
```bash
# Generate procurement request from image
python caigou.py
```

### Testing
```bash
# Run system tests
python test_system.py

# Test text extraction
python test_text_extraction.py

# Test procurement functionality
python test_procurement.py

# Test empty defaults handling
python test_empty_defaults.py
```

### Batch Processing
```bash
# Extract text from images in batch
python batch_extract.py

# Process entire folders
python process_folder.py

# Batch process Excel files
python batch_process_xlsx.py
```

## Core Architecture

### Main Components

1. **expense_request.py** - Main invoice processing system
   - `InvoiceProcessor` class handles PDF text extraction and OCR
   - Processes multiple PDF invoices from a folder
   - Extracts invoice numbers, amounts, and details using regex patterns
   - Generates formatted Excel reimbursement reports
   - Includes data validation and dropdown menus in Excel

2. **caigou.py** - Procurement request system
   - `ProcurementProcessor` class handles image OCR for procurement items
   - Extracts product information from images using OCR
   - Generates standardized procurement request Excel forms
   - Includes automated dropdown selections and formatting

3. **image_text_extractor.py** - OCR utility module
   - Provides text extraction from images using pytesseract
   - Supports batch processing of image files
   - Handles Chinese text recognition (chi_sim)

### Dependencies and Setup

**Python Requirements:**
- pandas>=1.5.0 - Excel file manipulation
- openpyxl>=3.0.0 - Excel formatting and data validation
- PyMuPDF>=1.20.0 - PDF text extraction
- pytesseract>=0.3.10 - OCR text recognition
- Pillow>=9.0.0 - Image processing
- pathlib2>=2.3.0 - Path utilities

**System Requirements:**
- Tesseract OCR with Chinese language pack
- Install on macOS: `brew install tesseract tesseract-lang`
- Install on Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim`

### Key Features and Patterns

1. **Dual-Mode Text Extraction**: The system first tries native PDF text extraction, then falls back to OCR if needed

2. **Chinese OCR Support**: Uses `chi_sim+eng` language configuration for Chinese and English text recognition

3. **Excel Formatting**: Creates professionally formatted Excel files with:
   - Merged cells and proper alignment
   - Data validation dropdowns
   - Border formatting and column width optimization
   - Chinese fonts (微软雅黑)

4. **Error Handling**: Comprehensive error handling with fallback defaults when OCR or extraction fails

5. **Regex Pattern Matching**: Extensive use of regex patterns for extracting:
   - Invoice numbers (8-20 digits)
   - Monetary amounts (various Chinese formats)
   - Product names and specifications

### Default Values and Configuration

The system uses these fixed defaults which can be modified in the respective classes:
- **Project Manager**: 马晓健
- **Department**: 人工智能研究院
- **Invoice Type**: 增值税电子普通发票
- **Payment Type**: 科研费用
- **Subject Detail**: 科研耗材

### File Naming Conventions

- **Expense Reports**: `YYYYMMDD_报销.xlsx`
- **Procurement Requests**: `YYYYMMDD_采购申请.xlsx`
- **Extracted Text**: `{original_name}_extracted_text.txt`

### Testing and Development

The system includes comprehensive test files for different components:
- System integration tests
- Text extraction accuracy tests
- Procurement generation tests
- Edge case handling tests

### Important Notes for Development

1. **Path Handling**: Use absolute paths for PDF/image folders
2. **Chinese Text**: Ensure UTF-8 encoding for all text processing
3. **Excel Output**: Files are generated with Chinese formatting standards
4. **OCR Fallback**: System gracefully degrades when OCR fails
5. **Amount Validation**: Includes validation for reasonable monetary ranges (0-100,000 RMB)