import os
import sys
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

def generate_certificates():
    """Generate self-signed certificates using Python's cryptography library"""
    print("Generating self-signed SSL certificates...")
    
    try:
        # Generate a private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Create a self-signed certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Organization"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            # Valid for 1 year
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(private_key, hashes.SHA256())

        # Write the certificate and private key to disk
        with open("cert.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open("key.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("\nSSL certificates generated successfully!")
        print("- cert.pem: SSL certificate")
        print("- key.pem: Private key")
        
        return True
        
    except Exception as e:
        print(f"\nError generating certificates: {e}")
        return False

if __name__ == "__main__":
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        overwrite = input("Certificate files already exist. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Exiting without generating new certificates.")
            sys.exit(0)
            
    if generate_certificates():
        print("\nYou can now run the server and client applications.")
    else:
        print("\nFailed to generate certificates.")
        sys.exit(1)