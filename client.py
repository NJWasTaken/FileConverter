import os
import ssl
import socket
import argparse
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ConversionClient')

class ConversionClient:
    def __init__(self, server_host='localhost', server_port=8443, cert_path='cert.pem'):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        # Check if certificate exists
        if not os.path.exists(cert_path):
            logger.error(f"Certificate file not found: {cert_path}")
            raise FileNotFoundError(f"Certificate file not found: {cert_path}")
            
        self.context.load_verify_locations(cert_path)
        self.context.check_hostname = False
        self.server_host = server_host
        self.server_port = server_port

    def send_request(self, file_path, conversion_type, extra_params=None):
        """
        Send a conversion request to the server
        
        Args:
            file_path: Path to the file to convert
            conversion_type: Type of conversion to perform
            extra_params: Optional dict of extra parameters for certain conversions
        
        Returns:
            list: Paths to the converted files
        """
        if not os.path.exists(file_path):
            logger.error(f"Input file not found: {file_path}")
            raise FileNotFoundError(f"Input file not found: {file_path}")
            
        output_files = []
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Set a timeout for operations
                sock.settimeout(60)  # 60 seconds timeout
                
                with self.context.wrap_socket(sock, server_hostname=self.server_host) as ssock:
                    logger.info(f"Connecting to {self.server_host}:{self.server_port}")
                    ssock.connect((self.server_host, self.server_port))
                    
                    # Send metadata and file
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    # Add extra parameters if provided
                    metadata = f"{file_name}|{conversion_type}|{file_size}"
                    if extra_params:
                        for key, value in extra_params.items():
                            metadata += f"|{value}"
                    
                    logger.info(f"Sending file: {file_name}, conversion: {conversion_type}, size: {file_size}")
                    
                    # Send metadata length followed by metadata
                    ssock.send(len(metadata).to_bytes(4, 'big'))
                    ssock.send(metadata.encode())
                    
                    # Send the file in chunks
                    bytes_sent = 0
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(4096):
                            ssock.send(chunk)
                            bytes_sent += len(chunk)
                            
                    logger.info(f"File sent successfully ({bytes_sent} bytes)")
                    
                    # Receive results
                    output_dir = os.path.join(os.getcwd(), 'converted_files')
                    os.makedirs(output_dir, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    while True:
                        # Get file name length, 0 means end of transmission
                        name_len_bytes = ssock.recv(4)
                        name_len = int.from_bytes(name_len_bytes, 'big')
                        
                        if not name_len: 
                            logger.info("End of transmission reached")
                            break
                        
                        # Get file name
                        file_name = ssock.recv(name_len).decode()
                        
                        # Check if it's an error message
                        if file_name.startswith("ERROR:"):
                            logger.error(f"Server returned error: {file_name}")
                            raise RuntimeError(file_name)
                        
                        # Get file size
                        file_size = int.from_bytes(ssock.recv(8), 'big')
                        
                        # Create unique filename to avoid overwriting
                        base_name, ext = os.path.splitext(file_name)
                        unique_file_name = f"{base_name}_{timestamp}{ext}"
                        output_path = os.path.join(output_dir, unique_file_name)
                        
                        logger.info(f"Receiving {file_name} ({file_size} bytes) -> {output_path}")
                        
                        # Receive the file
                        with open(output_path, 'wb') as f:
                            received = 0
                            while received < file_size:
                                chunk = ssock.recv(min(4096, file_size - received))
                                if not chunk:
                                    raise ConnectionError("Connection closed during file transfer")
                                f.write(chunk)
                                received += len(chunk)
                                
                        output_files.append(output_path)
                        logger.info(f"File received and saved to {output_path}")

        except socket.timeout:
            logger.error("Connection timed out")
            raise TimeoutError("Connection to the server timed out")
        except ConnectionRefusedError:
            logger.error(f"Connection refused to {self.server_host}:{self.server_port}")
            raise ConnectionRefusedError(f"Server at {self.server_host}:{self.server_port} refused connection")
        except Exception as e:
            logger.error(f"Error during file transfer: {str(e)}")
            raise
            
        return output_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='File Conversion Client')
    parser.add_argument('file_path', help='Path to input file')
    parser.add_argument('conversion_type', help='Conversion type (e.g., pdf2png, png2jpg, jpg2png, img_grayscale, img_resize)')
    parser.add_argument('--width', type=int, help='Width for resize operations', default=800)
    parser.add_argument('--height', type=int, help='Height for resize operations', default=600)
    args = parser.parse_args()

    try:
        client = ConversionClient()
        
        extra_params = None
        if args.conversion_type == 'img_resize':
            extra_params = {'width': args.width, 'height': args.height}
            
        output_files = client.send_request(args.file_path, args.conversion_type, extra_params)
        
        if output_files:
            print("\nConversion completed successfully!")
            print("Output files:")
            for file_path in output_files:
                print(f"- {file_path}")
    except Exception as e:
        print(f"\nError: {str(e)}")