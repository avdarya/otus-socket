import socket
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

HOST = '127.0.0.1'
PORT = 8080

end_of_stream = '\r\n\r\n'

def read_request(connection):
    client_data = ''
    while True:
        data = connection.recv(1024)
        if not data:
            break
        client_data += data.decode()
        if end_of_stream in client_data:
            break
    return client_data

def parse_request(request_text):
    request_line, headers_raw = request_text.split("\r\n", 1)
    method, path, _ = request_line.split()
    return method, path, headers_raw

def get_response_status(url_path):
    query = urlparse(url_path).query
    params = parse_qs(query)
    status_code = 200
    status_phrase = HTTPStatus(status_code).phrase
    if 'status' in params:
        try:
            status_code = int(params['status'][0])
            status_phrase = HTTPStatus(status_code).phrase
        except ValueError:
            status_code = 200
            status_phrase = HTTPStatus(status_code).phrase
    return status_code, status_phrase

def get_headers_line(raw_headers):
    headers = {}
    for line in raw_headers.split("\r\n"):
        if ': ' in line:
            key, value = line.split(': ', 1)
            if key.lower() == 'content-length':
                continue
            headers[key.strip()] = value.strip()
    line = ''
    for key, value in headers.items():
        line += f'{key}: {value}\r\n'
    return line

def get_body_line(method, address, code, phrase, headers_line):
    body = [
        f"Request Method: {method}\r\n"
        f"Request Source: {address}\r\n"
        f"Response Status: {code} {phrase}\r\n"
        f"{headers_line}"
    ]
    return ''.join(body)

def build_response(method, path, headers_raw, address):
    code, phrase = get_response_status(path)
    headers_line = get_headers_line(headers_raw)
    body_line = get_body_line(method, address, code, phrase, headers_line)
    return (
        f"HTTP/1.0 {code} {phrase}\r\n"
        f"Content-Type: text/plain; charset=UTF-8\r\n"
        f"Content-Length: {len(body_line.encode())}\r\n"
        f"{headers_line}"
        f"\r\n"
        f"{body_line}"
    )

def handle_client(connection, address):
    with connection:
        request_text = read_request(connection)
        method, path, headers_raw = parse_request(request_text)
        http_response = build_response(method, path, headers_raw, address)
        connection.sendall(http_response.encode())

with socket.socket() as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    while True:
        client_connection, client_address = server_socket.accept()
        handle_client( client_connection, client_address)
