import os
import tempfile
import base64
from typing import Optional
import pdfkit
import datetime

def html_to_pdf(html_content: str, report_title: str) -> str:
    """
    Convert HTML content to PDF file
    
    Parameters:
    -----------
    html_content : str
        HTML content to convert to PDF
    report_title : str
        Title of the report for filename
        
    Returns:
    --------
    str
        Path to generated PDF file
    """
    # Sanitize title for filename
    sanitized_title = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in report_title])
    sanitized_title = sanitized_title.replace(' ', '_')
    
    # Create temporary directory if needed
    temp_dir = tempfile.gettempdir()
    reports_dir = os.path.join(temp_dir, 'financial_reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"{sanitized_title}_{timestamp}.pdf"
    pdf_path = os.path.join(reports_dir, pdf_filename)
    
    try:
        # Convert HTML to PDF using pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm',
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'quiet': None
        }
        
        # Check for wkhtmltopdf path
        wkhtmltopdf_path = get_wkhtmltopdf_path()
        if wkhtmltopdf_path:
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
            pdfkit.from_string(html_content, pdf_path, options=options, configuration=config)
        else:
            pdfkit.from_string(html_content, pdf_path, options=options)
        
        return pdf_path
    
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        
        # Try with fewer options if the first attempt fails
        try:
            simple_options = {
                'page-size': 'A4',
                'quiet': None
            }
            pdfkit.from_string(html_content, pdf_path, options=simple_options)
            return pdf_path
        except Exception as e2:
            print(f"Second attempt to generate PDF failed: {str(e2)}")
            
            # Fall back to saving HTML if PDF conversion fails
            html_path = os.path.join(reports_dir, f"{sanitized_title}_{timestamp}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Saved HTML file instead at: {html_path}")
            return html_path

def get_wkhtmltopdf_path() -> Optional[str]:
    """
    Get the path to wkhtmltopdf executable based on platform
    
    Returns:
    --------
    str or None
        Path to wkhtmltopdf executable if found, None otherwise
    """
    # Common paths for wkhtmltopdf executable
    common_paths = [
        '/usr/bin/wkhtmltopdf',
        '/usr/local/bin/wkhtmltopdf',
        'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe',
        'C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'
    ]
    
    # Check if the executable exists in any of the common paths
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    # Check if it's in the PATH
    try:
        import subprocess
        result = subprocess.run(['which', 'wkhtmltopdf'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except Exception:
        pass
    
    return None

def html_to_base64_pdf(html_content: str) -> Optional[str]:
    """
    Convert HTML content to base64-encoded PDF data
    
    Parameters:
    -----------
    html_content : str
        HTML content to convert
        
    Returns:
    --------
    str or None
        Base64-encoded PDF data if successful, None otherwise
    """
    try:
        # Generate PDF in memory
        options = {
            'page-size': 'A4',
            'margin-top': '15mm',
            'margin-right': '15mm',
            'margin-bottom': '15mm',
            'margin-left': '15mm'
        }
        
        pdf_data = pdfkit.from_string(html_content, False, options=options)
        
        # Convert to base64
        return base64.b64encode(pdf_data).decode('utf-8')
    
    except Exception as e:
        print(f"Error generating base64 PDF: {str(e)}")
        return None

def convert_images_to_base64(html_content: str) -> str:
    """
    Convert image URLs in HTML content to base64 to make the HTML self-contained
    
    Parameters:
    -----------
    html_content : str
        HTML content with image URLs
        
    Returns:
    --------
    str
        HTML content with base64-encoded images
    """
    import re
    import requests
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all img tags
    for img in soup.find_all('img'):
        if img.has_attr('src') and img['src'].startswith(('http://', 'https://')):
            try:
                # Download the image
                response = requests.get(img['src'])
                if response.status_code == 200:
                    # Get image type
                    content_type = response.headers.get('Content-Type', 'image/png')
                    
                    # Encode to base64
                    encoded = base64.b64encode(response.content).decode('utf-8')
                    
                    # Create data URL
                    data_url = f"data:{content_type};base64,{encoded}"
                    
                    # Replace src attribute
                    img['src'] = data_url
            except Exception as e:
                print(f"Error converting image to base64: {str(e)}")
    
    return str(soup)
