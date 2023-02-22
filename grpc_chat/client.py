import grpc
import chat_pb2_grpc as pb2_grpc
import chat_pb2 as pb2
import threading
import inquirer
from ipaddress import ip_address


class ChatClient:
    def __init__(self, addr):
        """
        Initialize the ChatClient instance.

        Args:
        - addr (str): IP address of the host.
        """
        self.host = addr
        self.server_port = 50051

        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port))

        self.stub = pb2_grpc.ChatStub(self.channel)

    def create_account(self, username, password):
        """
        Create a new account with the specified username and password.

        Args:
        - username (str): The username for the new account.
        - password (str): The password for the new account.

        Returns:
        - A pb2.Result object representing the result of the operation.
        """
        account = pb2.Account(username=username, password=password)
        return self.stub.CreateAccount(account)

    def delete_account(self, username, password):
        """
        Delete the account with the specified username and password.

        Args:
        - username (str): The username of the account to be deleted.
        - password (str): The password of the account to be deleted.

        Returns:
        - A pb2.Result object representing the result of the operation.
        """
        account = pb2.Account(username=username, password=password)
        return self.stub.DeleteAccount(account)

    def login(self, username, password):
        """
        Log in to the account with the specified username and password.

        Args:
        - username (str): The username of the account to log in to.
        - password (str): The password of the account to log in to.

        Returns:
        - A pb2.Result object representing the result of the operation.
        """
        account = pb2.Account(username=username, password=password)
        return self.stub.Login(account)

    def logout(self, username):
        """
        Log out of the account with the specified username.

        Args:
        - username (str): The username of the account to log out of.

        Returns:
        - A pb2.Result object representing the result of the operation.
        """
        account = pb2.Account(username=username, password="")
        return self.stub.Logout(account)

    def list_accounts(self, searchterm):
        """
        Get a list of accounts that match the specified search term.

        Args:
        - searchterm (str): The search term to use.

        Returns:
        - A pb2.Result object representing the result of the operation.
        """
        search_term = pb2.SearchTerm(searchterm=searchterm)
        return self.stub.ListAccounts(search_term)

    def send_message(self, destination, source, text):
        """
        Send a message to the specified destination.

        Args:
        - destination (str): The username of the message recipient.
        - source (str): The username of the message sender.
        - text (str): The text of the message.

        Returns:
        - A pb2.Result object representing the result of the operation.
        """
        message_info = pb2.MessageInfo(destination=destination, source=source, text=text)
        return self.stub.SendMessage(message_info)

    def listen_messages(self, username):
        """
        Listen for messages sent to the specified user and print them to the console.

        Args:
        - username (str): The username of the account to listen for messages on.
        """
        account = pb2.Account(username=username)
        messages = self.stub.ListenMessages(account)
        for msg in messages:
            format = f'''
            ______________________________________________________________
            New message from {msg.source}:
            {msg.text}
            ______________________________________________________________
            '''
            print(format)


def login_ui(client):
    """Login UI for the chat client."""
    
    questions = [
        inquirer.Text('username', message="What is your name?"),
        inquirer.Password('password', message="What is your password?")
    ]
    answers = inquirer.prompt(questions)
    result = client.create_account(username=answers['username'], password=answers['password'])
    username, password = answers["username"], answers["password"]
    if result.error == False:
        print(f'Welcome, {username}. I see this is your first time here. Confirm your password below:')
        err = True
        while err == True:
            questions = [
                inquirer.Password('password', message="Password")
            ]
            password = inquirer.prompt(questions)['password']
            result = client.login(username=username, password=password)
            err = result.error
            if err == True:
                print(result.message)
        print(result.message)
    else:
        result = client.login(username=username, password=password)
        while result.error == True:
            print(result.message)
            questions = [
                inquirer.Text('username', message="Username"),
                inquirer.Password('password', message="Password")
            ]
            answers = inquirer.prompt(questions)
            username, password = answers["username"], answers["password"]
            result = client.login(username=username, password=password)
        print(result.message)

    return username, password


if __name__ == '__main__':
    th = None
    # Get the IP address of the chat server from the user
    questions = [inquirer.Text('ip', message="What's the server's IP address?",
                    validate=lambda _, x: ip_address(x))]

    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
    addr = answers['ip']
    
    client = ChatClient(addr)
    # Prompt the user to log in
    username, password = login_ui(client)

    # Start a thread to listen for incoming messages
    th = threading.Thread(target=client.listen_messages, args=(username,))
    th.start()

    list_questions = [
            inquirer.List('action',
                      message="What do you want to do?",
                      choices=['List accounts', 'Send message', 'Logout', 'Delete account']
                      ),
    ]
    while (True):
        # Define the questions to ask the user using inquirer
        # Ask the user what action they want to take
        answers = inquirer.prompt(list_questions)

        # Handle the user's chosen action
        if answers['action'] == "List accounts":
            # Ask the user for a regular expression to use for filtering the list of accounts
            question = [
                    inquirer.Text(
                        'query',
                        message='Provide a regular expression'
                    )
                ]
            regex = inquirer.prompt(question)['query']

            # Call the list_accounts method on the ChatClient instance and print the result
            result = client.list_accounts(regex)
            print(f'{result}')

        elif answers['action'] == "Send message":
            # Ask the user for the recipient and message text
            msg_questions = [
                inquirer.Text(
                    'recipient',
                    message='Who would you like to send a message to?'
                ),
                inquirer.Text(
                    'message',
                    message='Please enter the message you would like to send'
                )
            ]
            answers = inquirer.prompt(msg_questions)
            destination, text = answers['recipient'], answers['message']
            # Call the send_message method on the ChatClient instance and print the result
            result = client.send_message(destination=destination, source=username, text=text)
            print(f'{result}')

        elif answers['action'] == "Logout":
            # Confirm that the user wants to log out
            logout_question = [inquirer.Confirm('logout', message="Are you sure you want to logout?")]
            confirmation = inquirer.prompt(logout_question)['logout']
            if confirmation:
                # Call the logout method on the ChatClient instance
                client.logout(username=username)
                print("Successfully logged out")
                # Prompt the user to log in again
                username, password = login_ui(client)
                # Start a new thread to listen for incoming messages
                th = threading.Thread(target=client.listen_messages, args=(username,))
                th.start()
            else:
                pass

        elif answers['action'] == "Delete account":
            # Ask the user for their password and confirm that they want to delete their account
            delete_question = [inquirer.Confirm('delete', message="Are you sure you want to delete your account?")]
            confirmation = inquirer.prompt(delete_question)['delete']
            if confirmation:
                # Call the delete_account method on the ChatClient instance
                delete_question = [inquirer.Password('password', message="Password:"),]
                password = inquirer.prompt(delete_question)['password']
                result = client.delete_account(username=username, password=password)
                if result.error == True:
                    print(result.message)
                else:
                    print("Successfully deleted")
                    # Prompt the user to log in again
                    username, password = login_ui(client)
                    # Start a new thread to listen for incoming messages
                    th = threading.Thread(target=client.listen_messages, args=(username,))
                    th.start()
        else:
            print("Invalid action")

