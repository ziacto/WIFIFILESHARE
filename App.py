"""
  Generates a QR code containing the URL to access the server.
  Saves the QR code image in the UPLOAD_FOLDER.
  Returns the path to the saved QR code image.

  Written by: Coder Zia
  Founder of TheAppsFirm.com
  LinkedIn: https://www.linkedin.com/in/muhammadziashahid/
  Contact: +971562529187
  """

import os
import socket
import subprocess
from flask import Flask, request, render_template, send_from_directory, jsonify
import webbrowser
import qrcode
import logging
import platform
logging.basicConfig(level=logging.DEBUG)

# Initialize the Flask application
app = Flask(__name__)

# Define the path for the upload folder
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Desktop', 'WIFI_SHARE')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it does not already exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def generate_qr_code():
    """
    Generates a QR code containing the URL to access the server.
    Saves the QR code image in the UPLOAD_FOLDER.
    Returns the path to the saved QR code image.
    """
    ip = get_real_ip();
    url = f"http://{ip}:8080/"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(UPLOAD_FOLDER, 'server_qr.png')
    img.save(qr_path)
    return qr_path

def get_windows_ip():
    """
    Get the IP address on Windows.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting IP address on Windows: {e}")
        return None


def get_mac_ip():
  """
  Get the IP address on Mac OS.
  """
  try:
    # Execute ifconfig command and capture output
    result = subprocess.check_output(["ifconfig"]).decode("utf-8")
    
    # Search for lines containing 'inet ' (excluding loopback)
    for line in result.splitlines():
      if 'inet ' in line and not '127.0.0.1' in line:
        # Extract IP address from the matched line
        ip = line.split()[1]
        return ip
    
    # No matching line found, return None
    return None
  except Exception as e:
    print(f"Error getting IP address on Mac OS: {e}")
    return None


def get_real_ip():
    """
    Get the real IP address of the machine based on the operating system.
    """
    if platform.system() == 'Windows':
        return get_windows_ip()
    elif platform.system() == 'Darwin':
        return get_mac_ip()
    else:
        return None

@app.route('/')
def index():
    """
    Main route to display the home page.
    Generates a new QR code for each server start and passes its URL to the template.
    """
    qr_path = generate_qr_code()
    qr_url = f'/static/{os.path.basename(qr_path)}'
    return render_template('index.html', qr_code_url=qr_url)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Route to handle file uploads via POST requests.
    Saves each file uploaded to the designated UPLOAD_FOLDER.
    """
    if 'files[]' not in request.files:
        return 'No file part', 400
    files = request.files.getlist('files[]')
    for file in files:
        if file.filename:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return 'Files uploaded successfully!'

@app.route('/files/', defaults={'path': ''})
@app.route('/files/<path:path>')
def list_files(path):
    logging.info(f"List files request, path: {path}")

    try:
        directory = os.path.join(UPLOAD_FOLDER, path)
        if not os.path.exists(directory):
            return jsonify({'error': 'Directory not found'}), 404

        files = [{'name': f, 'url': f"/files/{os.path.join(path, f)}" if os.path.isdir(os.path.join(directory, f)) else f"/download/{os.path.join(path, f)}",
                  'is_folder': os.path.isdir(os.path.join(directory, f))}
                 for f in os.listdir(directory)]
        
        # Add a ".." option for going back
        if path:
            parent_path = os.path.dirname(path)
            files.insert(0, {
                'name': '..',
                'url': f"/files/{parent_path}" if parent_path else "/", 
                'is_folder': True
            })
        
        # Inside list_files function
        logging.info(f"JSON Response: {files}") 
        return jsonify(files)

    except Exception as e:  
        logging.error(f"Error listing directory ({path}): {e}")
        return jsonify({'error': 'Error listing directory'}), 500  # Generic server-side error


@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Route to download a file. This route sends a file from the UPLOAD_FOLDER to the client.
    """
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/static/<filename>')
def static_files(filename):
    """
    Route to serve static files from the UPLOAD_FOLDER.
    """
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    webbrowser.open_new("http://localhost:8080/")
    app.run(host='0.0.0.0', port=8080, debug=True)
