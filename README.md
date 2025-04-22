# FileConverter

A secure, user-friendly file conversion tool with a web-based interface, built using a client-server architecture with SSL encryption.

## Features

- **Intuitive UI**: Clean, responsive web interface powered by Streamlit
- **Secure Transfers**: All data transfers secured with SSL encryption
- **Multiple Conversion Options**:
  - PDF to PNG: Convert each page of a PDF to separate PNG images
  - PNG to JPG: Convert PNG images to JPG format
  - JPG to PNG: Convert JPG images to PNG format
  - Image to Grayscale: Convert any image to grayscale
  - Image Resize: Resize an image to specific dimensions
- **Preview Capability**: Preview images before and after conversion
- **Automatic Server Management**: Starts necessary services automatically

## Installation
### Setup

1. Clone the repository:
   ```
   git clone https://github.com/NJWasTaken/FileConverter.git
   cd FileConverter
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Generate SSL certificates (if not present):
   ```
   python cert.py
   ```

## Usage

### Starting the Application

Run the main script to start both the conversion server and the web interface:

```
python main.py
```

This will:
1. Check for required dependencies
2. Generate SSL certificates if needed
3. Start the conversion server on port 8443
4. Launch the Streamlit web interface on port 8501
5. Open your default web browser to the application

### Command Line Options

- `--no-browser`: Start the application without automatically opening a browser
  ```
  python main.py --no-browser
  ```

### Using the Web Interface

1. **Upload a File**: Click the file uploader to select a file
2. **Select Conversion Type**: Choose from available conversion options for your file type
3. **Configure Additional Parameters**: Set specific parameters if required (e.g., width and height for image resizing)
4. **Start Conversion**: Click the "Start Conversion" button
5. **Download Results**: Download the converted files from the results section

### Direct Client Usage

You can also use the client script directly for command-line conversion:

```
python client.py /path/to/file.pdf pdf2png
```

For image resize operations:
```
python client.py /path/to/image.png img_resize --width 1024 --height 768
```

## Architecture

FileConverter uses a client-server architecture with:

- **Server (`server.py`)**: Handles file conversions using libraries like OpenCV and PyMuPDF
- **Client (`client.py`)**: Sends files to the server for conversion and receives results
- **Web Interface (`app.py`)**: Streamlit-based UI for easy interaction
- **Main Script (`main.py`)**: Orchestrates the application components

All communications between client and server are secured using SSL encryption.

## Directory Structure

- `/converted_files`: Contains output files (created automatically)
- `cert.pem` and `key.pem`: SSL certificate files (generated on first run)

## Dependencies

- **streamlit**: Web interface
- **Pillow**: Image processing
- **OpenCV**: Advanced image operations
- **PyMuPDF (fitz)**: PDF handling
- **cryptography**: SSL certificate generation

## Troubleshooting

1. **Server fails to start**: Check if port 8443 is already in use
2. **Certificate errors**: Run `python cert.py` to regenerate certificates
3. **Missing dependencies**: Run `pip install -r requirements.txt`
4. **Connection issues**: Ensure the server is running by checking logs

## Developers

Created by Noel Jose and Nihal Ravi Ganesh

## License

This project is open source and available for personal and commercial use.
