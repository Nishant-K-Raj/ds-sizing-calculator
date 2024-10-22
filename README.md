# Dynamic Sizing Calculator

This is a Flask-based web application that calculates hardware requirements for Cloudera components based on user inputs. The app uses an Excel spreadsheet for initial data inputs and estimates resource needs like CPU, RAM, storage, and nodes.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Accessing the Application](#accessing-the-application)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Prerequisites
Before running the application, ensure you have the following installed:
- Python 3.8 or higher
- Pip (Python's package manager)
- An IDE like IntelliJ or any code editor

## Installation

1. **Clone or download the repository:**
   ```bash
   git clone <your-repo-url>
   cd dynamic-sizing-calculator
2. **Install the required Python packages**
   ```bash
   pip install flask pandas openpyxl

## Verify Directory Structure

``` csharp dynamic-sizing-calculator/
├── app.py
├── app_local.py
├── templates
    ├── index.html
    ├── results.html 
├── sizing.xlsx
└── README.md
```
## Running the Application

1. **Start the Flask app:**
```bash 
   cd dynamic-sizing-calculator
```

2. **Run the Application**
```bash
    python app_local.py
```
3. **Expected Output**
```bash
Serving Flask app 'app_local'
Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Running on http://127.0.0.1:5000
Press CTRL+C to quit
Restarting with stat
Debugger is active!
Debugger PIN: 123-456-789
```
## Accessing the Application

1. Open a web browser
2. Navigate to: http://127.0.0.1:5000

## Usage
Enter Parameters:

Fill in fields for different Cloudera components such as CDW, CDE, CML, and others.
Each field has default values, but you can adjust them based on your requirements.
Submit the Form:

After entering values, click Calculate to generate the results.
The results will show the estimated nodes, CPU cores, RAM, and storage required for the specified configuration.
Review Output:

The output will display a summary table of resources needed based on the inputs provided.

Refer to readme page in sizing.xlsx
