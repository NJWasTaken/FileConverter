import os
import sys
import subprocess
import time
import webbrowser
import threading
import argparse
import signal

# Global process objects
server_process = None
streamlit_process = None

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import streamlit
        import PIL
        import cv2
        import fitz  # PyMuPDF
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install all required packages:")
        print("pip install -r requirements.txt")
        return False

def check_certificates():
    """Check if SSL certificates exist"""
    if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
        print("SSL certificates not found. Generating...")
        try:
            subprocess.run([sys.executable, "cert.py"], check=True)
        except subprocess.CalledProcessError:
            print("Failed to generate certificates. Please run 'python generate_certificates.py' manually.")
            return False
    return True

def start_server():
    """Start the conversion server"""
    global server_process
    print("Starting conversion server...")
    
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give the server time to start
    time.sleep(2)
    
    # Check if server is still running
    if server_process.poll() is not None:
        stderr = server_process.stderr.read().decode()
        print(f"Server failed to start: {stderr}")
        return False
        
    print("Server started successfully!")
    return True

def start_streamlit():
    """Start the Streamlit web interface"""
    global streamlit_process
    print("Starting Streamlit web interface...")
    
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give Streamlit time to start
    time.sleep(3)
    
    # Check if Streamlit is still running
    if streamlit_process.poll() is not None:
        stderr = streamlit_process.stderr.read().decode()
        print(f"Streamlit failed to start: {stderr}")
        return False
        
    print("Streamlit started successfully!")
    return True

def open_browser():
    """Open web browser to Streamlit interface"""
    url = "http://localhost:8501"
    print(f"Opening web browser to {url}")
    webbrowser.open(url)

def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    print("\nShutting down...")
    
    if server_process and server_process.poll() is None:
        print("Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
    
    if streamlit_process and streamlit_process.poll() is None:
        print("Stopping Streamlit...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()
    
    print("Shutdown complete!")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Start the File Conversion Tool")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    args = parser.parse_args()
    
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("File Conversion Tool Startup")
    print("===========================")
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Check certificates
    if not check_certificates():
        return 1
    
    # Start server
    if not start_server():
        cleanup()
        return 1
    
    # Start Streamlit
    if not start_streamlit():
        cleanup()
        return 1
    
    # Open browser unless disabled
    if not args.no_browser:
        threading.Timer(1.0, open_browser).start()
    
    print("\nFile Conversion Tool is running!")
    print("Streamlit UI: http://localhost:8501")
    print("Press Ctrl+C to exit")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if server_process.poll() is not None:
                print("Server process stopped unexpectedly!")
                cleanup()
                return 1
                
            if streamlit_process.poll() is not None:
                print("Streamlit process stopped unexpectedly!")
                cleanup()
                return 1
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())