from socket import *
import threading

# Function to handle client connections
def handle_client(client_socket):
    while True:
        try:
            # Receive the message from the client
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"Received from client: {message}")
            
            # Send a response back to the client
            response = f"Server received: {message}"
            client_socket.send(response.encode('utf-8'))
            print(f"Server response: {response}")

        except Exception as e:
            print(f"Error handling client: {e}")
            break

    # Close the connection
    client_socket.close()

# Start the server
def start_server():
    serverIP = "127.0.0.1"  # Localhost
    serverPort = 12345  # Server port
    serverSocket = socket(AF_INET, SOCK_STREAM)  # Create the server socket
    serverSocket.bind((serverIP, serverPort))  # Bind to IP and port
    serverSocket.listen(5)  # Listen for incoming connections

    print("Server is listening on port 12345...")

    while True:
        client_socket, addr = serverSocket.accept()  # Accept incoming connection
        print(f"Connection established with {addr}")

        # Start a new thread to handle the client
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
