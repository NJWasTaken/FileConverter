import streamlit as st
import os
import tempfile
import time
import subprocess
import ssl
import socket
from PIL import Image
import io

# Import the client code
from client import ConversionClient

# Page configuration
st.set_page_config(
    page_title="File Conversion Tool",
    page_icon="🔄",
    layout="wide",
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        max-width: 1200px;
    }
    .stButton button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .file-info {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-msg {
        padding: 1rem;
        background-color: #d1e7dd;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .error-msg {
        padding: 1rem;
        background-color: #f8d7da;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def check_server_status(host='localhost', port=8443):
    """Check if the conversion server is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def start_conversion_server():
    """Start the conversion server as a background process"""
    try:
        # Start the server as a subprocess
        subprocess.Popen(["python", "server.py"], 
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        # Wait for server to start
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"Failed to start conversion server: {str(e)}")
        return False

def check_certificate_files():
    """Check if certificate files exist"""
    cert_exists = os.path.exists('cert.pem')
    key_exists = os.path.exists('key.pem')
    return cert_exists and key_exists

def generate_certificate():
    """Generate self-signed certificate for SSL"""
    try:
        # Generate key and certificate
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", "key.pem", "-out", "cert.pem", 
            "-days", "365", "-nodes", "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True)
        return True
    except Exception as e:
        st.error(f"Failed to generate certificate: {str(e)}")
        return False

def display_file_info(file):
    """Display information about the uploaded file"""
    file_size = len(file.getvalue())
    
    # Format file size
    size_str = f"{file_size} bytes"
    if file_size > 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    if file_size > 1024 * 1024:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    
    # Updated styling for file details
    st.markdown(f"""
    <div style="
        padding: 1rem;
        background-color: #1e301c;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-family: Arial, sans-serif;
    ">
        <h4 style="margin-bottom: 0.5rem;">📄 File Details</h4>
        <p style="margin: 0.2rem 0;"><strong>Name:</strong> {file.name}</p>
        <p style="margin: 0.2rem 0;"><strong>Size:</strong> {size_str}</p>
        <p style="margin: 0.2rem 0;"><strong>Type:</strong> {file.type}</p>
    </div>
    """, unsafe_allow_html=True)

def show_image_preview(file):
    """Show image preview if the file is an image"""
    try:
        image = Image.open(io.BytesIO(file.getvalue()))
        st.image(image, caption="Preview", use_column_width=True)
    except:
        st.info("No preview available for this file type")

def main():
    st.title("🔄 File Conversion Tool")
    st.write("Convert various file formats with ease")
    
    # Check for SSL certificates or generate them
    if not check_certificate_files():
        st.warning("SSL certificates not found. Generating self-signed certificates...")
        if generate_certificate():
            st.success("SSL certificates generated successfully!")
        else:
            st.error("Failed to generate SSL certificates. Please check if OpenSSL is installed.")
            return
    
    # Check if server is running, start if needed
    col1, col2 = st.columns(2)
    
    with col1:
        if check_server_status():
            st.success("✅ Conversion server is running")
        else:
            st.warning("⚠️ Conversion server is not running")
            if st.button("Start Server"):
                if start_conversion_server():
                    st.success("✅ Server started successfully!")
                    time.sleep(2)  # Give server time to initialize
                    st.experimental_rerun()
                else:
                    st.error("❌ Failed to start server")
    
    with col2:
        # Server settings (could be expanded)
        st.write("Server Configuration")
        server_host = st.text_input("Server Host", value="localhost")
        server_port = st.number_input("Server Port", value=8443, min_value=1024, max_value=65535)
    
    # Main conversion interface
    st.markdown("---")
    st.subheader("Upload File for Conversion")
    
    uploaded_file = st.file_uploader("Choose a file to convert", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        display_file_info(uploaded_file)
        
        # Show preview for image files
        if uploaded_file.type.startswith('image/'):
            show_image_preview(uploaded_file)
        
        # Available conversion types
        st.subheader("Select Conversion Type")
        
        conversion_options = {
            "pdf2png": "Convert PDF to PNG images",
            "png2jpg": "Convert PNG to JPG",
            "jpg2png": "Convert JPG to PNG",
            "img_grayscale": "Convert image to grayscale",
            "img_resize": "Resize image"
        }
        
        # Filter available conversions based on file type
        available_conversions = {}
        if uploaded_file.type == 'application/pdf':
            available_conversions["pdf2png"] = conversion_options["pdf2png"]
        elif uploaded_file.type == 'image/png':
            available_conversions["png2jpg"] = conversion_options["png2jpg"]
            available_conversions["img_grayscale"] = conversion_options["img_grayscale"]
            available_conversions["img_resize"] = conversion_options["img_resize"]
        elif uploaded_file.type in ['image/jpeg', 'image/jpg']:
            available_conversions["jpg2png"] = conversion_options["jpg2png"]
            available_conversions["img_grayscale"] = conversion_options["img_grayscale"]
            available_conversions["img_resize"] = conversion_options["img_resize"]
            
        if not available_conversions:
            st.warning("No conversion options available for this file type")
            return
            
        conversion_type = st.selectbox(
            "Choose conversion type",
            options=list(available_conversions.keys()),
            format_func=lambda x: available_conversions[x]
        )
        
        # Extra parameters for specific conversions
        extra_params = {}
        if conversion_type == "img_resize":
            col1, col2 = st.columns(2)
            with col1:
                width = st.number_input("Width (pixels)", min_value=1, max_value=4000, value=800)
                extra_params['width'] = width
            with col2:
                height = st.number_input("Height (pixels)", min_value=1, max_value=4000, value=600)
                extra_params['height'] = height
        
        # Process the conversion
        if st.button("Start Conversion"):
            with st.spinner("Converting..."):
                # Save uploaded file to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                
                try:
                    # Run the conversion
                    client = ConversionClient(server_host=server_host, server_port=server_port)
                    output_files = client.send_request(tmp_path, conversion_type, extra_params)
                    
                    # Show results
                    st.markdown(f"""
                    <div class="success-msg">
                        <h3 style="color: black;">✅ Conversion Complete!</h3>
                        <p style="color: black;>{len(output_files)} file(s) have been created.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display converted files
                    st.subheader("Converted Files")
                    
                    for output_path in output_files:
                        file_name = os.path.basename(output_path)
                        file_size = os.path.getsize(output_path)
                        size_str = f"{file_size/1024:.2f} KB" if file_size > 1024 else f"{file_size} bytes"
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{file_name}** ({size_str})")
                            
                            # Show image preview for image outputs
                            if output_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                                st.image(output_path)
                        
                        with col2:
                            with open(output_path, "rb") as file:
                                st.download_button(
                                    label="Download",
                                    data=file,
                                    file_name=file_name,
                                    mime="application/octet-stream"
                                )
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-msg">
                        <h3>❌ Conversion Failed</h3>
                        <p>{str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
    
    # Information section
    st.markdown("---")
    with st.expander("About This Tool"):
        st.markdown("""
        ### File Conversion Tool
        
        Created by Noel Jose and Nihal Ravi Ganesh, this tool uses a client-server architecture with SSL encryption to securely convert files between various formats.
        
        **Supported Conversions:**
        - PDF to PNG: Convert each page of a PDF to a separate PNG image
        - PNG to JPG: Convert PNG images to JPG format
        - JPG to PNG: Convert JPG images to PNG format
        - Image to Grayscale: Convert any image to grayscale
        - Image Resize: Resize an image to specific dimensions
        
        **How It Works:**
        1. Upload a file using the interface above
        2. Select your desired conversion type
        3. Configure additional parameters if necessary
        4. Click "Start Conversion" to begin
        5. Download the converted files
        
        **Security:**
        All file transfers are secured with SSL encryption.
        """)

if __name__ == "__main__":
    main()