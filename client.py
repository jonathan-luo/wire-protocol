import socket
import threading
import inquirer
from datetime import datetime
from ipaddress import ip_address

MAX_MESSAGE_LENGTH = 280
illegal_characters = {'|'} # Characters that are not allowed in usernames or passwords or messages to prevent injection attacks

def validate_input(_, input):
    if len(input) > MAX_MESSAGE_LENGTH:
        raise inquirer.errors.ValidationError("", reason=f"Your input cannot exceed {MAX_MESSAGE_LENGTH} characters.")
    for i in illegal_characters:
        if i in input:
            raise inquirer.errors.ValidationError("", reason=f"Your input cannot contain the character '{i}'.")
    return True


def is_registered_user(client, username):
    send_message(client, 3, username)
    message = process_response(client, 3)
    if message[0] == 'False':
        raise inquirer.errors.ValidationError("", reason=f"'{username}' is not a registered account.")
    return True


def process_response(client, desired_command):
    """Process the message from the server, hope to get the desired command, and return the arguments if successful"""

    message = client.recv(1024).decode()
    if not message:
        print("The server disconnected. Please try again later.")
        quit(client)

    command, *args = message.split("|")

    if int(command) != desired_command:
        print("An error occurred. Please try again later.")
        quit(client)
    return args


def send_message(client, command, *args):
    """Send a message to the server"""

    message = f"{command}|" + "|".join(args)
    client.send(message.encode())


def quit(client):
    """Quit the client"""

    client.close()
    print("Goodbye!")
    exit(0)


def handle_client(client):
    """Send and receive messages to and from the server and print them to the console"""

    user = login(client)
    if not user:
        client.close()
        return

    task = None
    choices = ['View Users', 'Send New Message', 'Delete Account', 'Quit/Log Out']
    while (task != 'Quit/Log Out'):
        questions = [
                inquirer.List('task',
                    message="Please select a task",
                    choices=choices,
                    carousel=True,
                )
        ]
        answers = inquirer.prompt(questions)
        task = answers['task']

        # TODO: Implement functionality for each task.
        if task == 'View Users':
            question = [inquirer.Text(
                'query',
                message='Input wildcard query for specific users (leave empty for all users)',
                validate=validate_input
            )]
            wildcard_query = inquirer.prompt(question)['query']
            send_message(client, 1, wildcard_query)
            message = process_response(client, 1)
            print("\nAvailable users:\n" + "\n".join(message) + "\n")
        elif task == 'Send New Message':
            # Send a message to another user (or queue it if the other user is not active)
            deliver_new_message(client, user)
        elif task == 'Delete Account':
            # TODO: Edit to utilize wire protocols 4 and 5 (i.e., verify that only one instance of user logged in,
            # and prompt whether they want to log out every other instance)
            password = input("Please enter your password to confirm deletion: ")
            send_message(client, 8, password)
            message = process_response(client, 8)
    quit(client)


def deliver_new_message(client, username):
    questions = [
        inquirer.Text(
            'recipient',
            message='Who would you like to send a message to?',
            validate=lambda _, x: validate_input(_, x) and is_registered_user(client, x)
        ),
        inquirer.Text(
            'message',
            message='Please enter the message you would like to send',
            validate=validate_input
        )
    ]
    current_time = str(datetime.now())
    answer = inquirer.prompt(questions)
    recipient, message = answer['recipient'], answer['message']
    send_message(client, 2, username, recipient, message, current_time)
    message = process_response(client, 2)


def login(client):
    """Login the client or create a new account"""

    # Asks the server if the username is already in use
    user = input("Please enter your username: ")
    while not user:
        user = input("Your username cannot be empty. Please reenter your username: ")
    send_message(client, 0, user)

    # Follow designated login procedure based on server response
    response = process_response(client, 0)
    return login_registered_user(client, user) if response[0] == "exists" else login_new_user(client, user)


def login_registered_user(client, user):
    """Login procedure for a registered user"""

    password = input(f"Welcome back, {user}! Please enter your password: ")

    send_message(client, 0, password)
    response = process_response(client, 0)

    tries = 4
    while response[0] == "error":
        tries -= 1
        if tries == 0:
            print("Too many failed attempts. Please try again later.")
            send_message(client, 9)
            return None
        question = [inquirer.Confirm('retry', message=f"Hmm, seems like your password was incorrect. You have {tries} more tries. Would you like to retry?")]
        retry = inquirer.prompt(question)['retry']
        if not retry:
            return None
        password = input(f"Please re-enter your password: ")
        send_message(client, 0, password)

        response = process_response(client, 0)

    if response[0] == "success":
        print("Successfully logged in!")

    return user


def login_new_user(client, user):
    """Account creation and login procedure for new user"""

    # Prompt for password
    questions = [inquirer.Password('password', message=f"Welcome, {user}! Seems like you're new here! To register, please enter a password"),
                 inquirer.Password('confirm', message="Please confirm your password")]
    password, confirm = inquirer.prompt(questions).values()

    # If the passwords don't match, ask for password again
    while password != confirm:
        question = [inquirer.Confirm('retry', message="The passwords don't match. Would you like to try again?")]
        retry = inquirer.prompt(question)['retry']
        if not retry:
            return None

        questions = [inquirer.Password('password', message="Please re-enter your desired password"),
                        inquirer.Password('confirm', message="Please confirm your password")]
        password, confirm = inquirer.prompt(questions).values()

    send_message(client, 0, password)
    response = process_response(client, 0)

    if response[0] == "success":
        print("Successfully registered and logged in!")
    else:
        print("Something went wrong. Please try again later.")
        return None

    return user


def start_client():
    """Start the client and connect to the server"""

    receive_thread = None

    while not receive_thread:
        # Asking the user to input a valid IP address
        questions = [inquirer.Text('ip', message="What's the server's IP address?",
                    validate=lambda _, x: ip_address(x))]

        answers = inquirer.prompt(questions)
        host = answers['ip']
        port = 8000

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))

            # TODO: Come up with a badass name
            print("Welcome to <Name TBD>!")

            receive_thread = threading.Thread(target=handle_client, args=([client]))
            receive_thread.start()
        except:
            print("Unable to connect to server. Retry with a different IP address.")


if __name__ == "__main__":
    start_client()
