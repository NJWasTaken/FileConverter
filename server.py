import os
import ssl
import socket
import threading
import tempfile
from PIL import Image
import cv2
import fitz  # PyMuPDF for PDF handling
from io import BytesIO
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ConversionServer')

class ConversionServer:
    def __init__(self, host='0.0.0.0', port=8443, cert_path='cert.pem', key_path='key.pem'):
        self.host = host
        self.port = port
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Check if certificate files exist
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            logger.error(f"Certificate files not found: {cert_path}, {key_path}")
            raise FileNotFoundError(f"Certificate files not found: {cert_path}, {key_path}")
            
        self.context.load_cert_chain(cert_path, key_path)
        self.context.options |= ssl.OP_NO_TLSv1_2
        
        self.conversion_handlers = {
            'pdf2png': self.handle_pdf_to_png,
            'png2jpg': self.handle_image_conversion,
            'jpg2png': self.handle_jpg_to_png,
            'img_grayscale': self.handle_grayscale,
            'img_resize': self.handle_resize
        }

    def handle_pdf_to_png(self, input_path, output_dir):
        """Convert PDF to PNG using PyMuPDF (no Poppler dependency)"""
        pdf_document = fitz.open(input_path)
        outputs = []
        
        for page_number in range(pdf_document.page_count):
            page = pdf_document.load_page(page_number)
            
            # Higher resolution (300 DPI)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))
            output_path = os.path.join(output_dir, f'page_{page_number+1}.png')
            pix.save(output_path)
            outputs.append(output_path)
            
        pdf_document.close()
        return outputs

    def handle_image_conversion(self, input_path, output_dir):
        """Convert any image to JPG"""
        img = Image.open(input_path)
        output_path = os.path.join(output_dir, 'converted.jpg')
        img.convert('RGB').save(output_path)
        return [output_path]
        
    def handle_jpg_to_png(self, input_path, output_dir):
        """Convert JPG to PNG"""
        img = Image.open(input_path)
        output_path = os.path.join(output_dir, 'converted.png')
        img.save(output_path, 'PNG')
        return [output_path]

    def handle_grayscale(self, input_path, output_dir):
        """Convert an image to grayscale"""
        img = cv2.imread(input_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        output_path = os.path.join(output_dir, 'grayscale.jpg')
        cv2.imwrite(output_path, gray)
        return [output_path]
        
    def handle_resize(self, input_path, output_dir, width=800, height=600):
        """Resize an image to specified dimensions"""
        try:
            img = cv2.imread(input_path)
            resized = cv2.resize(img, (width, height))
            output_path = os.path.join(output_dir, 'resized.jpg')
            cv2.imwrite(output_path, resized)
            return [output_path]
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            raise

    def handle_client(self, conn):
        try:
            # Receive metadata
            metadata_len_bytes = conn.recv(4)
            if not metadata_len_bytes:
                logger.warning("Client disconnected before sending metadata length")
                return
                
            metadata_len = int.from_bytes(metadata_len_bytes, 'big')
            metadata = conn.recv(metadata_len).decode()
            
            parts = metadata.split('|')
            if len(parts) < 3:
                raise ValueError(f"Invalid metadata format: {metadata}")
                
            file_name, conversion, file_size = parts[0], parts[1], parts[2]
            file_size = int(file_size)
            
            logger.info(f"Receiving file: {file_name}, conversion: {conversion}, size: {file_size}")

            # Receive file
            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, file_name)
                with open(input_path, 'wb') as f:
                    received = 0
                    while received < file_size:
                        chunk = conn.recv(min(4096, file_size - received))
                        if not chunk:
                            raise ConnectionError("Connection closed before file was fully received")
                        f.write(chunk)
                        received += len(chunk)

                logger.info(f"File received, processing conversion: {conversion}")

                # Process conversion
                if conversion not in self.conversion_handlers:
                    raise ValueError(f"Unsupported conversion: {conversion}")
                    
                # Handle resize with extra parameters if provided
                if conversion == 'img_resize' and len(parts) >= 5:
                    width, height = int(parts[3]), int(parts[4])
                    output_files = self.handle_resize(input_path, temp_dir, width, height)
                else:
                    output_files = self.conversion_handlers[conversion](input_path, temp_dir)

                # Send results
                for output_path in output_files:
                    file_name = os.path.basename(output_path)
                    file_size = os.path.getsize(output_path)
                    
                    logger.info(f"Sending result: {file_name}, size: {file_size}")
                    
                    # Send file name length
                    conn.send(len(file_name).to_bytes(4, 'big'))
                    # Send file name
                    conn.send(file_name.encode())
                    # Send file size
                    conn.send(file_size.to_bytes(8, 'big'))
                    
                    # Send file data
                    with open(output_path, 'rb') as f:
                        bytes_sent = 0
                        while chunk := f.read(4096):
                            conn.send(chunk)
                            bytes_sent += len(chunk)
                
                # Send empty bytes to signal end of transmission
                conn.send((0).to_bytes(4, 'big'))
                logger.info("Conversion completed and sent to client")

        except Exception as e:
            logger.error(f"Error handling client: {str(e)}")
            try:
                error_msg = f"ERROR: {str(e)}".encode()
                conn.send(len(error_msg).to_bytes(4, 'big'))
                conn.send(error_msg)
            except:
                pass
        finally:
            try:
                conn.close()
            except:
                pass
            logger.info("Client connection closed")

    def start(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((self.host, self.port))
                sock.listen(5)
                logger.info(f"Server listening on {self.host}:{self.port}")
                
                with self.context.wrap_socket(sock, server_side=True) as ssock:
                    while True:
                        try:
                            conn, addr = ssock.accept()
                            logger.info(f"Connected to {addr}")
                            client_thread = threading.Thread(
                                target=self.handle_client, args=(conn,)
                            )
                            client_thread.daemon = True
                            client_thread.start()
                        except Exception as e:
                            logger.error(f"Error accepting connection: {str(e)}")
        except Exception as e:
            logger.critical(f"Server error: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        server = ConversionServer()
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical(f"Fatal server error: {str(e)}")