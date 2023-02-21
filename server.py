from collections import defaultdict
import fnmatch
import socket
import hashlib
import re
import threading


# Dictionary to store the users, their messages, and the unsent message queue
accounts = {}
messages = defaultdict(lambda: defaultdict(list))
unsent_message_queue = defaultdict(list)

# Currently connected clients
connected_clients = defaultdict(set)


# Define class to package user message information
class UserMessage:
    def __init__(self, sender, recipient, message, time):
        self.sender = sender
        self.recipient = recipient
        self.message = message
        self.time = time


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
    """Send a message to each client"""

    message = f"{command}|" + "|".join(args)
    client.send(message.encode())


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
    connected_clients[username].add(client)

    # Send a success message to the client
    send_message(client, 0, "success")
    print(f"{username} has joined the chat")

    return username


def list_users(client, username, query: str = None):
    """List all users matching the inputted wildcard text query"""

    all_connected_users = list(filter(lambda x: x != username, connected_clients.keys()))
    if all_connected_users:
        # If no wildcard query provided, return all active users other than the current user
        if not query:
            send_message(client, 1, *all_connected_users)
            return all_connected_users

        # Translate wildcard query to regex
        regex = fnmatch.translate(query)
        pattern = re.compile(regex)
        result = list(filter(pattern.match, all_connected_users))

        # If username matches exist, return those matches
        if result:
            send_message(client, 1, *result)
            return result

    # Else return that no users were found.
    send_message(client, 1, "No users found.")
    return None


def deliver_new_message(client, *args):
    """Delivers new message to recipient, if the recipient is active, otherwise queues message"""

    sender, recipient, message, time = args
    packaged_message = UserMessage(sender, recipient, message, time)
    if recipient not in connected_clients:
        unsent_message_queue['recipient'].append(packaged_message)
    else:
        # TODO: Deliver message to recipient.
        pass
    messages[sender, recipient] = packaged_message
    return packaged_message


def quit(client, username):
    """Logs out the instance of account `username` using socket `client`"""

    connected_clients[username].remove(client)
    client.close()


def handle_client(client, address):
    """Handle the client connection"""

    username = login(client)
    if not username:
        quit(client, username)
        return

    # TODO: Send all messages that are queued immediately to client.

    while True:
        message = process_message(client)
        if message is None:
            break
        command, args = message

        if command == 1:
            # List other active users based on wildcard query provided (if any)
            list_users(client, username, args[0])
        elif command == 2:
            # TODO: Deliver message to user IF the recipient is logged in; otherwise, queue it.
            deliver_new_message(client, *args)
            send_message(client, 2, 'Success')
        elif command == 3:
            # Returns to client whether an account is a registered account.
            send_message(client, 3, str(args[0] in accounts))
        elif command == 4:
            # Returns to client whether a user is currently logged in on multiple devices
            send_message(client, 4, str(len(connected_clients[args[0]]) > 1))
        elif command == 5:
            # Logs out all instances of `username` aside from the one using socket `client`
            for c in connected_clients[username]:
                if c != client:
                    quit(client, username)
            send_message(client, 5, 'Success')

    # Log out `username` on the `client` socket
    connected_clients[username].remove(client)

    # If `username` maps to empty set, delete the `username`'s mapping entirely
    if not connected_clients[username]:
        del connected_clients[username]

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
