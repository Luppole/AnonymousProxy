from OpenSSL import crypto, SSL
from os.path import exists, join

CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"

def generate_self_signed_cert(cert_file, key_file):
    # Create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # Create the self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Organization"
    cert.get_subject().OU = "Organization Unit"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    with open(cert_file, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(key_file, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if not exists(CERT_FILE) or not exists(KEY_FILE):
    generate_self_signed_cert(CERT_FILE, KEY_FILE)
    print(f"Generated self-signed certificate and key: {CERT_FILE}, {KEY_FILE}")
else:
    print(f"Certificate and key already exist: {CERT_FILE}, {KEY_FILE}")
