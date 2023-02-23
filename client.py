import hashlib
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
    if len(input) == 0:
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


def hash_password(password):
    """Hashes password using SHA256"""

    return hashlib.sha256(password.encode()).hexdigest()


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
            client.close()
            exit(0)

        # Else, deserialize message
        command, *args = message.split("|")

        # If `QUIT_COMMAND`, quit client
        if int(command) == QUIT_COMMAND:
            quit(client)

        # Else if `RECEIVE_MESSAGE_COMMAND`, display message
        elif int(command) == RECEIVE_MESSAGE_COMMAND:
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
    """Display a message"""
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


def delete_account(client, username):
    """Procedure to delete account"""

    # Check if user is logged in on multiple devices
    send_message(client, MULTIPLE_LOGIN_COMMAND, username)
    message = process_response(client, MULTIPLE_LOGIN_COMMAND)

    # If user is logged in on multiple devices, prompt them to log out of all other devices
    if message[0] == 'True':
        question = [inquirer.Confirm('confirm_logout',
            message='It appears that your account is logged in on multiple devices. You must only be logged in on one device to delete an account.\nWould you like to log out of all other devices?'
        )]
        response = inquirer.prompt(question)['confirm_logout']

        # If user refuses to log out of other devices, cancel account deletion
        if not response:
            return False

        # Log out all other clients if user confirms
        send_message(client, LOGOUT_COMMAND)
        message = process_response(client, LOGOUT_COMMAND)

    # Prompt user to confirm deletion with password
    question = [inquirer.Password('password',
        message='Please enter your password to confirm deletion',
        validate=lambda _, x: validate_input(x))]
    password = inquirer.prompt(question)['password']

    # Send hashed password to server for authentication
    send_message(client, DELETE_ACCOUNT_COMMAND, hash_password(password))
    message = process_response(client, DELETE_ACCOUNT_COMMAND)

    # If password is incorrect, cancel account deletion and inform user
    if message[0] == 'error':
        print("Your password was incorrect, account deletion cancelled.\n")
        return False

    # If account was successfully deleted, return True
    return True



def quit(client):
    """Quit the client"""

    send_message(client, QUIT_COMMAND)


def handle_client(client):
    """ Send and receive messages to and from the server and print them to the console. """

    # Authenticate the user with the server.
    user = login(client)

    try:
        # If the user could not be authenticated, exit the program.
        if user is None:
            send_message(client, QUIT_COMMAND)
            exit(0)

        # Prompt the user for a task until they choose to quit.
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

            # Execute the appropriate task based on the user's choice.
            if task == 'View Users':
                # Ask the user for a wildcard query for specific users.
                question = [
                    inquirer.Text(
                        'query',
                        message='Input wildcard query for specific users ("*" for all users, "b*" for all users starting with "b", etc.)',
                        validate=lambda _, x: validate_input(x)
                    )
                ]
                wildcard_query = inquirer.prompt(question)['query']

                if wildcard_query != RETURN_KEYWORD:
                    # Send a message to the server requesting the list of available users.
                    send_message(client, VIEW_USERS_COMMAND, wildcard_query)
                    # Process the response from the server and print it to the console.
                    message = process_response(client, VIEW_USERS_COMMAND)
                    print("\nAvailable users:\n" + "\n".join(message) + "\n")

            elif task == 'Send New Message':
                # Prompt the user to enter a message and recipient.
                deliver_new_message(client, user)

            elif task == 'Delete Account':
                # Attempt to delete the user's account from the server.
                if delete_account(client, user):
                    break

        # If the user has logged out, exit the program.
        if user is None:
            send_message(client, QUIT_COMMAND)
            exit(0)

        # Close the client connection.
        quit(client)

    except:
        # Exit the program if an exception is raised.
        exit(0)

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
        message=f'Welcome back, {user}! Please enter your password',
        validate=lambda _, x: validate_input(x))]
    password = inquirer.prompt(question)['password']

    send_message(client, LOGIN_COMMAND, hash_password(password))
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
        send_message(client, LOGIN_COMMAND, hash_password(password))
        response = process_response(client, LOGIN_COMMAND)

    if response[0] == "success":
        print("Successfully logged in!")
        return user

    return None


def login_new_user(client, user):
    """Account creation and login procedure for new user"""

    # Prompt for password
    questions = [
        inquirer.Password(
            'password',
            message=f"Welcome, {user}! Seems like you're new here! To register, please enter a password",
            validate=lambda _, x: validate_input(x)
        ),
        inquirer.Password(
            'confirm',
            message="Please confirm your password",
            validate=lambda _, x: validate_input(x)
        )]
    password, confirm = inquirer.prompt(questions).values()

    # If the passwords don't match, ask for password again
    while password != confirm:
        question = [inquirer.Confirm('retry', message="The passwords don't match. Would you like to try again?")]
        retry = inquirer.prompt(question)['retry']
        if not retry:
            return None

        questions = [
            inquirer.Password(
                'password',
                message="Please re-enter your desired password",
                validate=lambda _, x: validate_input(x)
            ),
            inquirer.Password(
                'confirm',
                message="Please confirm your password",
                validate=lambda _, x: validate_input(x)
            )
        ]
        password, confirm = inquirer.prompt(questions).values()

    send_message(client, LOGIN_COMMAND, hash_password(password))
    response = process_response(client, LOGIN_COMMAND)

    if response[0] == "success":
        print("Successfully registered and logged in!")
    else:
        print("Something went wrong. Please try again later.")
        return None

    return user


def login_new_user(client, user):
    """Account creation and login procedure for new user"""
    questions = [inquirer.Password('password', message=f"Welcome, {user}! Seems like you're new here! To register, please enter a password", validate=lambda _, x: validate_input(x)),
                     inquirer.Password('confirm', message="Please confirm your password", validate=lambda _, x: validate_input(x))]
    password, confirm = inquirer.prompt(questions).values()

    # If the passwords don't match, ask for password again
    while password != confirm:
        question = [inquirer.Confirm('retry', message="The passwords don't match. Would you like to try again?")]
        retry = inquirer.prompt(question)['retry']
        if not retry:
            return None

        questions = [inquirer.Password('password', message="Please re-enter your desired password", validate=lambda _, x: validate_input(x)),
                        inquirer.Password('confirm', message="Please confirm your password", validate=lambda _, x: validate_input(x))]
        password, confirm = inquirer.prompt(questions).values()

    send_message(client, 0, hash_password(password))
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

            print("Welcome to <Name TBD>!")

            user_thread = threading.Thread(target=handle_client, args=([client]))
            user_thread.start()

            message_reception_thread = threading.Thread(target=receive_server_messages, args=([client]))
            message_reception_thread.start()
        except:
            print("Unable to connect to server. Retry with a different IP address.")


if __name__ == "__main__":
    start_client()
