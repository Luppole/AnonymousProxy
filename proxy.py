import socket
import threading
import logging
import ssl
import configparser

# Read the configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Define constants from the config
LOCAL_HOST = config['proxy']['local_host']
LOCAL_PORT = int(config['proxy']['local_port'])
BUFFER_SIZE = int(config['proxy']['buffer_size'])
CERTFILE = config['proxy']['certfile']
KEYFILE = config['proxy']['keyfile']
LOG_FILE = config['proxy']['log_file']
LOG_LEVEL = config['proxy']['log_level']

# Configure logging
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE),
                              logging.StreamHandler()])


def modify_headers(request):
    lines = request.decode().split('\r\n')
    modified_lines = []

    for line in lines:
        if line.lower().startswith("x-forwarded-for") or line.lower().startswith("proxy-connection"):
            continue
        if line.lower().startswith("user-agent"):
            modified_lines.append("User-Agent: AnonymizedProxy")
        else:
            modified_lines.append(line)

    modified_lines.append("Connection: close")

    return "\r\n".join(modified_lines).encode() + b"\r\n\r\n"


def handle_https(client_socket, target_host, target_port):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
        server_socket = context.wrap_socket(socket.socket(socket.AF_INET), server_side=False)
        server_socket.connect((target_host, target_port))

        client_socket.setblocking(False)
        server_socket.setblocking(False)

        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if len(data) == 0:
                    break
                server_socket.sendall(data)
            except:
                pass
            try:
                data = server_socket.recv(BUFFER_SIZE)
                if len(data) == 0:
                    break
                client_socket.sendall(data)
            except:
                pass

        server_socket.close()
    except Exception as e:
        logging.error(f"Error in HTTPS handling: {e}")


def handle_client(client_socket):
    try:
        request = client_socket.recv(BUFFER_SIZE)
        first_line = request.decode().split('\n')[0]
        method = first_line.split()[0]

        if method == 'CONNECT':
            target_host, target_port = first_line.split()[1].split(':')
            target_port = int(target_port)
            client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            handle_https(client_socket, target_host, target_port)
        else:
            host_line = [line for line in request.decode().split('\n') if line.startswith('Host:')][0]
            target_host = host_line.split()[1].split(':')[0]
            target_port = 80 if ':' not in host_line.split()[1] else int(host_line.split()[1].split(':')[1])
            request = modify_headers(request)

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((target_host, target_port))
            server_socket.sendall(request)

            while True:
                response = server_socket.recv(BUFFER_SIZE)
                if len(response) == 0:
                    break
                client_socket.sendall(response)

            server_socket.close()

        logging.info(f"Connection handled successfully for target {target_host}:{target_port}")

    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        client_socket.close()
        logging.info("Client socket closed")


def main():
    try:
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.bind((LOCAL_HOST, LOCAL_PORT))
        proxy_socket.listen(5)
        logging.info(f"[*] Listening on {LOCAL_HOST}:{LOCAL_PORT}")

        while True:
            client_socket, addr = proxy_socket.accept()
            logging.info(f"[*] Accepted connection from {addr}")

            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except Exception as e:
        logging.error(f"Error in main server loop: {e}")
    finally:
        proxy_socket.close()
        logging.info("Proxy socket closed")


if __name__ == "__main__":
    main()
