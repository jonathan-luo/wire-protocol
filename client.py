import socket
import threading
import inquirer
from ipaddress import ip_address

illegal_characters = ['|'] # Characters that are not allowed in usernames or passwords or messages to prevent injection attacks

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
                    message="Please select a task:",
                    choices=choices,
                    carousel=True,
                )
        ]
        answers = inquirer.prompt(questions)
        task = answers['task']
        
        # TODO: Implement functionality for each task.
        if task == 'View Users':
            string = ""
            # TODO: Ask the user for the string to search for, if empty do all
            send_message(client, 1, string)
            message = process_response(client, 1)
            print("Available users:\n" + "\n".join(message))
        elif task == 'Send New Message':
            # TODO: Send a message to a user
            pass
        elif task == 'Delete Account':
            password = input("Please enter your password to confirm deletion: ")
            send_message(client, 8, password)
            message = process_response(client, 8)
    quit(client)


def login(client):
    """Login the client or create a new account"""
    
    # Asks the server if the username is already in use
    user = input("Please enter your username: ")
    send_message(client, 0, user)
   
    response = process_response(client, 0)
    
    # If the user is already in use, ask for password and check if it matches
    if response[0] == "exists":
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
            password = input(f"Hmm, seems like your password was incorrect. You have{tries} more tries. Please re-enter your password: ")
            send_message(client, 0, password)
            
            response = process_response(client, 0)
            
        if response[0] == "success":
            print("Successfully logged in!")
    else:
        # If the user is already in use, ask for password and check if it matches
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
