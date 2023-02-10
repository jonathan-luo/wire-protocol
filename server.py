import socket
import hashlib
import threading


# Dictionary to store the users and their messages
accounts = {}
messages = {}

# Currently connected clients
connected_clients = set()

def receive_message(client, address):
    """Receive messages from the client and handles them accordingly"""
    
    user = login(client)

    while True:
        data = client.recv(1024).decode()
        if data == "":
            break
         # Split the data into command and message
        command, *message = data.split(" ")

        # If the command is "login"
        if command == "login":
            # Check if the username is in the existing accounts
            if message[0] in accounts:
                client.send("Error: User already logged in".encode())
        else:
            print(f"Unknown command: {data}")


def login(client):
    """Login the user and return the username"""
    username = client.recv(1024).decode()

    if username in accounts:
        # If the username exists, ask for password
        client.send("exists".encode())
        
        # Hash the entered password and check it against the stored password hash
        password = client.recv(1024).decode()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        while accounts[username] != password_hash:
            client.send("error".encode())
            password = client.recv(1024).decode()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # TODO: Set up some sort of failure mechanism for when the password is
        # incorrect too many times or user stops wanting to try.
        
        # TODO: If the user has undelivered messages, send them to the client
    else:
        # If the username doesn't exist
        client.send("new".encode())
        
        # Hash the entered password and check it against the stored password hash
        password = client.recv(1024).decode()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        accounts[username] = password_hash
        
    # Send a success message to the client
    client.send("success".encode())
    print(f"{username} has joined the chat")
    connected_clients.add(username)
    return username


def handle_client(client, address):
    """Handle the client connection"""
    
    username = login(client)
    if not username:
        client.close()
        return

    while True:
        data = client.recv(1024).decode()
        if data == "":
            break
        command, *args = data.split(" ")
        if command == "send":
            recipient, message = args
            if recipient in accounts:
                accounts[recipient].append((username, message))
                client.send(f"Message sent to {recipient}".encode())
            else:
                client.send(f"{recipient} is not a user".encode())
        elif command == "list":
            pass
        elif command == "quit":
            pass
        elif command == "delete":
            pass
            
    connected_clients.discard(username)
    print(f"{username} has left the chat")
    client.close()


def start_server():
    """Start the server"""
    
    host = "localhost"
    port = 8000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print("Server started on", host, "port", port)

    while True:
        client, address = server.accept()
        print("Accepted connection from", address)
        client_thread = threading.Thread(
            target=handle_client, args=(client, address))
        client_thread.start()


if __name__ == "__main__":
    start_server()
