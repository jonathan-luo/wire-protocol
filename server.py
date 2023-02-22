from collections import defaultdict
import fnmatch
import socket
import hashlib
import re
import threading
from threading import Lock
from config import *

# Dictionary to store the users, their messages, and the unsent message queue
accounts = {}                                      # Maps username to password hash
messages = defaultdict(lambda: defaultdict(list))  # Organized such that [s][r] holds a list of UserMessages sent from sender `s` to recipient `r`
unsent_message_queue = defaultdict(list)           # Organized such that [r] holds a list of unsent UserMessages to recipient `r`

# Thread locks
client_locks = {}  # Maps client to lock
user_locks = {}    # Maps username to lock

# Currently connected clients (maps from username to client socket)
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

    message = client.recv(BUFSIZE).decode()
    command, *args = message.split("|")
    try:
        return int(command), args
    except:
        return None


def process_specific_message(client, desired_command):
    """Process the message from the client, hope to get the desired command, and return the arguments if successful"""
    
    message = client.recv(BUFSIZE).decode()
    if not message:
        print("The client disconnected.")
        return None
    
    command, *args = message.split("|")
    if int(command) == QUIT_COMMAND:
        return None
    
    if int(command) != desired_command:
        print("An error occurred.")
        return None

    return args


def send_message(client, command, *args):
    """Send a message to each client"""

    with client_locks[client]:
        message = f"{command}|" + "|".join(args)
        message += '|'
        padding = ' ' * (BUFSIZE - len(message))
        message += padding
        client.send(message.encode())


def login(lock, client):
    """Login the user and return the username"""
    message = process_message(client)
    if message is None:
        return None
    command, args = message
    if command != LOGIN_COMMAND:
        return None

    username = args[0]
    if username in accounts:
        # If the username exists, ask for password
        send_message(client, LOGIN_COMMAND, "exists")

        # Hash the entered password and check it against the stored password hash
        response = process_specific_message(client, LOGIN_COMMAND)
        if response is None:
            return None
        password_hash = response[0]

        while accounts[username] != password_hash:
            send_message(client, LOGIN_COMMAND, "error")
            response = process_specific_message(client, LOGIN_COMMAND)
            if response is None:
                return None
            password_hash = response[0]
    else:
        # Create new lock associated with username
        user_locks[username] = Lock()

        # If the username doesn't exist

        send_message(client, LOGIN_COMMAND, "new")

        # Hash the entered password and check it against the stored password hash
        response = process_specific_message(client, LOGIN_COMMAND)
        if response is None:
            return None
        password_hash = response[0]
        accounts[username] = password_hash

    # Add the client to the connected clients list
    connected_clients[username].add(client)

    # Send a success message to the client

    send_message(client, LOGIN_COMMAND, "success")
    print(f"{username} has joined the chat!")

    return username


def list_users(client, username, query: str = '*'):
    """List all users matching the inputted wildcard text query"""

    all_connected_users = list(filter(lambda x: x != username, connected_clients.keys()))
    if all_connected_users:
        # If no wildcard query provided, return all active users other than the current user
        if query == '*':
            send_message(client, VIEW_USERS_COMMAND, *all_connected_users)
            return all_connected_users

        # Translate wildcard query to regex
        regex = fnmatch.translate(query)
        pattern = re.compile(regex)
        result = list(filter(pattern.match, all_connected_users))

        # If username matches exist, return those matches
        if result:
            send_message(client, VIEW_USERS_COMMAND, *result)
            return result

    # Else return that no users were found.
    send_message(client, VIEW_USERS_COMMAND, "No users found.")
    return None


def deliver_new_message(lock, client, *args):
    """Delivers new message to recipient, if the recipient is active, otherwise queues message"""

    sender, recipient, message, time = args

    # Package message into UserMessage instance for cleaner storage
    packaged_message = UserMessage(sender, recipient, message, time)

    # If recipient not logged in, queue up message
    if recipient not in connected_clients:
        with user_locks[recipient]:
            unsent_message_queue[recipient].append(packaged_message)

    # Else deliver message to each device the recipient is logged in to
    else:
        for c in connected_clients[recipient]:
            deliver_unsent_message(c, packaged_message)

    # Store message in message history dictionary
    with lock:
        messages[sender][recipient].append(packaged_message)

    # Success
    send_message(client, SEND_MESSAGE_COMMAND, 'Success')
    return packaged_message


def deliver_unsent_message(client, message):
    """Delivers unsent message to all instances where the recipent of the message is logged in"""

    send_message(
        client,
        RECEIVE_MESSAGE_COMMAND,
        message.sender, message.recipient, message.message, message.time
    )


def delete_account(client, username):
    """Deletes account from records"""

    with user_locks[username]:
        del accounts[username]
        del unsent_message_queue[username]

    send_message(client, DELETE_ACCOUNT_COMMAND, 'success')


def quit(lock, client, username, address):
    """Logs out the instance of account `username` using socket `client`"""

    with user_locks[username]:
        # Log out `username` on the `client` socket
        connected_clients[username].remove(client)

        # If `username` maps to empty set, delete the `username`'s mapping entirely
        if not connected_clients[username]:
            del connected_clients[username]

    with lock:
        # Remove client lock
        del client_locks[client]

    if username:
        print(f"{username} has left the chat.")
    else:
        print(f"Connection from {address} was ended.")
        
    client.close()


def handle_client(lock, client, address):
    """Handle the client connection"""

    username = login(lock, client)
    if not username:
        quit(lock, client, username, address)
        return

    # Send all messages that are queued immediately to client.
    unsent_messages = unsent_message_queue[username]
    while unsent_messages:
        deliver_unsent_message(client, unsent_messages.pop(0))

    while True:
        message = process_message(client)
        if message is None:
            quit(lock, client, username, address)
            break
        command, args = message

        if command == VIEW_USERS_COMMAND:
            # List other active users based on wildcard query provided (if any)
            list_users(client, username, args[0])
        elif command == SEND_MESSAGE_COMMAND:
            # Deliver message to user IF the recipient is logged in; otherwise, queue it.
            deliver_new_message(lock, client, *args)
        elif command == CHECK_ACCOUNT_COMMAND:
            # Returns to client whether an account is a registered account.
            send_message(client, CHECK_ACCOUNT_COMMAND, str(args[0] in accounts))
        elif command == MULTIPLE_LOGIN_COMMAND:
            # Returns to client whether a user is currently logged in on multiple devices
            send_message(client, MULTIPLE_LOGIN_COMMAND, str(len(connected_clients[username]) > 1))
        elif command == LOGOUT_COMMAND:
            # Logs out all instances of `username` aside from the one using socket `client`
            with user_locks[username]:
                for c in connected_clients[username].copy():
                    if c != client:
                        send_message(c, QUIT_COMMAND)
            send_message(client, LOGOUT_COMMAND, 'success')
        elif command == DELETE_ACCOUNT_COMMAND:
            # Delete account if password is correct
            if args[0] == accounts[username]:
                delete_account(client, username)
            else:
                send_message(client, DELETE_ACCOUNT_COMMAND, 'error')
        elif command == QUIT_COMMAND:
            quit(lock, client, username, address)
            break


def start_server():
    """Start the server"""

    host = socket.gethostbyname(socket.gethostname())
    port = PORT_NUMBER

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((host, port))
    server.listen()
    print(f"Server started on host {host} and port {port}. The clients will need this information to connect to the server.")

    # Create global lock
    global_lock = Lock()

    while True:
        client, address = server.accept()
        print(f"Accepted connection from {address}.")

        # Create client lock
        client_locks[client] = Lock()

        # Start client thread
        client_thread = threading.Thread(
            target=handle_client, args=(global_lock, client, address))
        client_thread.start()


if __name__ == "__main__":
    start_server()
