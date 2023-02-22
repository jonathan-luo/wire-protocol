import socket
import threading
import inquirer
from datetime import datetime
from ipaddress import ip_address
from textwrap import dedent
from config import *

# Queue for message reception thread to load non-message display server messages to
server_message_queue = []

def validate_input(input):
    """Validates that an input string is not over `MAX_MESSAGE_LENGTH` and
       doesn't contain illegal characters"""
    if input == RETURN_KEYWORD:
        return True
    if len(input) > MAX_MESSAGE_LENGTH:
        raise inquirer.errors.ValidationError("", reason=f"Your input cannot exceed {MAX_MESSAGE_LENGTH} characters.")
    if len(input) == LOGIN_COMMAND:
        raise inquirer.errors.ValidationError("", reason=f"Your input cannot be empty.")
    for i in ILLEGAL_CHARS:
        if i in input:
            raise inquirer.errors.ValidationError("", reason=f"Your input cannot contain the character '{i}'.")
    return True


def is_registered_user(client, username):
    """Checks whether `username` is a registered account by contacting server"""

    if username == RETURN_KEYWORD:
        return True
    send_message(client, CHECK_ACCOUNT_COMMAND, username)
    message = process_response(client, CHECK_ACCOUNT_COMMAND)
    if message[0] == 'False':
        raise inquirer.errors.ValidationError("", reason=f"'{username}' is not a registered account.")
    return True


def receive_server_messages(client):
    """Continually receive messages from server, displaying messages if they are messages
       otherwise queuing up the message"""
    while True:
        # Receive message from server
        message = client.recv(BUFSIZE).decode()
        message = message.rstrip()

        # Remove the extra '|' at the end of the message
        message = message[:-1]

        # If message is None, we know that we've disconnected and we can exit
        if not message:
            print("You have disconnected. Goodbye!")
            exit(0)

        # Else, deserialize message
        command, *args = message.split("|")

        # If `RECEIVE_MESSAGE_COMMAND`, display message
        if int(command) == RECEIVE_MESSAGE_COMMAND:
            sender, recipient, message, time = args
            display_message(sender, recipient, message, time)

        # Else queue the operation up
        else:
            server_message_queue.append(message)


def process_response(client, desired_command):
    """Process the message from the server, hope to get the desired command, and return the arguments if successful"""

    # Wait until the server message queue is not empty
    while not server_message_queue:
        continue

    message = server_message_queue.pop(0)
    command, *args = message.split("|")

    if int(command) != desired_command:
        print("An error occurred. Please try again later.")
        quit(client)

    return args


def display_message(sender, recipient, message, time):
    print(dedent(f'''
        ----------------------------------------
        From: {sender}
        To: {recipient}
        Time: {time}

        {message}

        ----------------------------------------
    '''))


def send_message(client, command, *args):
    """Send a message to the server"""

    message = f"{command}|" + "|".join(args)
    client.send(message.encode())


def quit(client):
    """Quit the client"""

    send_message(client, QUIT_COMMAND)


def handle_client(client):
    """Send and receive messages to and from the server and print them to the console"""

    user = login(client)
    if user is None:
        send_message(client, QUIT_COMMAND)
        exit(0)

    task = None
    choices = ['View Users', 'Send New Message', 'Delete Account', 'Quit/Log Out']
    while (task != 'Quit/Log Out'):
        questions = [
                inquirer.List('task',
                    message=f"Please select a task. Type {RETURN_KEYWORD} to return to this menu.",
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
                message='Input wildcard query for specific users ("*" for all users, "b*" for all users starting with "b", etc.)',
                validate=lambda _, x: validate_input(x)
            )]
            wildcard_query = inquirer.prompt(question)['query']
            if wildcard_query != RETURN_KEYWORD:
                send_message(client, VIEW_USERS_COMMAND, wildcard_query)
                message = process_response(client, VIEW_USERS_COMMAND)
                print("\nAvailable users:\n" + "\n".join(message) + "\n")
        elif task == 'Send New Message':
            # Send a message to another user (or queue it if the other user is not active)
            deliver_new_message(client, user)
        elif task == 'Delete Account':
            # TODO: Edit to utilize wire protocols 4 and 5 (i.e., verify that only one instance of user logged in,
            # and prompt whether they want to log out every other instance)
            # Delete the user's account
            question = [inquirer.Password('password',
                message='Please enter your password to confirm deletion',
                validate=lambda _, x: validate_input(x))]
            password = inquirer.prompt(question)['password']
            send_message(client, DELETE_ACCOUNT_COMMAND, password)
            message = process_response(client, DELETE_ACCOUNT_COMMAND)
    quit(client)


def deliver_new_message(client, username):
    """Prompts user for recipient and message, and contacts server"""

    # Prompt user for their desired recipient and message
    # Validation ensures that the input doesn't exceed character limit,
    # contain illegal character, or request to send to a non-registered user
    questions = [
        inquirer.Text(
            'recipient',
            message='Who would you like to send a message to?',
            validate=lambda _, x: validate_input(x) and is_registered_user(client, x)
        ),
        inquirer.Text(
            'message',
            message='Please enter the message you would like to send',
            validate=lambda _, x: validate_input(x),
            ignore=lambda x: x['recipient'] == RETURN_KEYWORD
        )
    ]

    # Send message to server with sender, recipient, message, and current time info
    current_time = str(datetime.now().strftime(TIME_FORMAT))
    answer = inquirer.prompt(questions)
    if answer['recipient'] == RETURN_KEYWORD or answer['message'] == RETURN_KEYWORD:
        return
    recipient, message = answer['recipient'], answer['message']
    send_message(client, SEND_MESSAGE_COMMAND, username, recipient, message, current_time)
    message = process_response(client, SEND_MESSAGE_COMMAND)


def login(client):
    """Login the client or create a new account"""

    # Asks the server if the username is already in use
    question = [inquirer.Text('user',
                    message=f"Please enter your username",
                    validate=lambda _, x: validate_input(x))]
    user = inquirer.prompt(question)['user']

    send_message(client, LOGIN_COMMAND, user)

    # Follow designated login procedure based on server response
    response = process_response(client, LOGIN_COMMAND)
    return login_registered_user(client, user) if response[0] == "exists" else login_new_user(client, user)


def login_registered_user(client, user):
    """Login procedure for a registered user"""

    question = [inquirer.Password('password',
        message='Please enter your password',
        validate=lambda _, x: validate_input(x))]
    password = inquirer.prompt(question)['password']

    send_message(client, LOGIN_COMMAND, password)
    response = process_response(client, LOGIN_COMMAND)

    tries = 4
    while response[0] == "error":
        tries -= 1
        if tries == 0:
            print("Too many failed attempts. Please try again later.")
            break
        question = [inquirer.Confirm('retry', message=f"Hmm, seems like your password was incorrect. You have {tries} more tries. Would you like to retry?")]
        retry = inquirer.prompt(question)['retry']
        if not retry:
            break
        question = [inquirer.Password('password',
                    message=f"Please re-enter your password",
                    validate=lambda _, x: validate_input(x))]
        password = inquirer.prompt(question)['password']
        send_message(client, LOGIN_COMMAND, password)

        response = process_response(client, LOGIN_COMMAND)

    if response[0] == "success":
        print("Successfully logged in!")
        return user

    return None


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

    send_message(client, LOGIN_COMMAND, password)
    response = process_response(client, LOGIN_COMMAND)

    if response[0] == "success":
        print("Successfully registered and logged in!")
    else:
        print("Something went wrong. Please try again later.")
        return None

    return user


def login_new_user(client, user):
    """Account creation and login procedure for new user"""
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

    user_thread = None
    message_reception_thread = None

    while not user_thread or not message_reception_thread:
        # Asking the user to input a valid IP address
        questions = [inquirer.Text('ip', message="What's the server's IP address?",
                    validate=lambda _, x: ip_address(x))]

        answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
        host = answers['ip']
        port = PORT_NUMBER

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))

            # TODO: Come up with a badass name
            print("Welcome to <Name TBD>!")

            user_thread = threading.Thread(target=handle_client, args=([client]))
            user_thread.start()

            message_reception_thread = threading.Thread(target=receive_server_messages, args=([client]))
            message_reception_thread.start()
        except:
            print("Unable to connect to server. Retry with a different IP address.")


if __name__ == "__main__":
    start_client()
