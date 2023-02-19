import socket
import hashlib
import threading


# Dictionary to store the users and their messages
accounts = {}
messages = {}

# Currently connected clients
connected_clients = {}

def process_message(client):
    """Process the message from the client and return the command and arguments"""
    message = client.recv(1024).decode()
    command, *args = message.split("|")
    try:
        return int(command), args
    except:
        return None
    
def process_specific_message(client, desired_command):
    """Process the message from the client, hope to get the desired command, and return the arguments if successful"""
    
    message = client.recv(1024).decode()
    if not message:
        print("The client disconnected.")
        return None
        
    command, *args = message.split("|")
    
    if int(command) != desired_command:
        print("An error occurred.")
        return None
        
    return args
    
def send_message(client, command, *args):
    """Send a message to the server"""
    message = f"{command}|" + "|".join(args)
    client.send(message.encode())

   
def quit(client):
    """Quit the client"""
    client.close()


def login(client):
    """Login the user and return the username"""
    message = process_message(client)
    if message is None:
        return None
    command, args = message
    
    if command != 0:
        return None
    
    username = args[0]
    if username in accounts:
        # If the username exists, ask for password
        send_message(client, 0, "exists")
        
        # Hash the entered password and check it against the stored password hash
        response = process_specific_message(client, 0)
        if response is None:
            return None
        password = response[0]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        while accounts[username] != password_hash:
            send_message(client, 0, "error")
            response = process_specific_message(client, 0)
            if response is None:
                return None
            password = response[0]
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # TODO: If the user has undelivered messages, send them to the client
    else:
        # If the username doesn't exist
        send_message(client, 0, "new")
        
        # Hash the entered password and check it against the stored password hash
        response = process_specific_message(client, 0)
        if response is None:
            return None
        password = response[0]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        accounts[username] = password_hash
    
    # Add the client to the connected clients list
    if username in connected_clients:
        connected_clients[username].append(client)
    else:
        connected_clients[username] = [client]
        
    # Send a success message to the client
    send_message(client, 0, "success")
    print(f"{username} has joined the chat")
        
    return username


def list_users(input: str = None):
    """List all users matching the input"""
    if input is None:
        list(connected_clients.keys())
    pass


def handle_client(client, address):
    """Handle the client connection"""
    
    username = login(client)
    if not username:
        quit(client)
        return

    while True:
        message = process_message(client)
        if message is None:
            break   
        command, args = message
        
        if command == 1:
            list_users(args)
        elif command == 2:
            pass
        elif command == 3:
            pass
            
    connected_clients[username].remove(client)
    print(f"{username} has left the chat")
    client.close()


def start_server():
    """Start the server"""
    
    host = socket.gethostbyname(socket.gethostname())
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
