import grpc
import unary_pb2_grpc as pb2_grpc
import unary_pb2 as pb2
import threading

class ChatClient(object):
    def __init__(self):
        self.host = 'localhost'
        self.server_port = 50051

        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port))

        self.stub = pb2_grpc.ChatStub(self.channel)

    def create_account(self, username, password):
        account = pb2.Account(username=username, password=password)
        return self.stub.CreateAccount(account)

    def delete_account(self, username, password):
        account = pb2.Account(username=username, password=password)
        return self.stub.DeleteAccount(account)

    def login(self, username, password):
        account = pb2.Account(username=username, password=password)
        return self.stub.Login(account)

    def logout(self, username):
        account = pb2.Account(username=username, password="")
        return self.stub.Logout(account)

    def list_accounts(self, searchterm):
        search_term = pb2.SearchTerm(searchterm=searchterm)
        return self.stub.ListAccounts(search_term)

    def send_message(self, destination, source, text):
        message_info = pb2.MessageInfo(destination=destination, source=source, text=text)
        return self.stub.SendMessage(message_info)
    
    def listen_messages(self, username):
        account = pb2.Account(username=username)
        messages = self.stub.ListenMessages(account)
        for msg in messages:
            print(msg.text)



def login_ui(client):
    username = input("What is your name?")
    password = input("What is your password?")
    result = client.create_account(username=username, password=password)
    if result.error == False:
        print(f'Welcome, {username}. I see this is your first time here.  Confirm your password below:')
        err = True
        while err == True:
            password = input("Password: ")
            result = client.login(username=username, password=password)
            err = result.error
            if err == True:
                print(result.message)
        print(result.message)
    else:
        result = client.login(username=username, password=password)
        while result.error == True:
            print(result.message)
            username = input("Username: ")
            password = input("Password: ")
            result = client.login(username=username, password=password)
        print(result.message)

    return username, password

if __name__ == '__main__':   
    th = None
    client = ChatClient()
    username, password = login_ui(client)

    # Once use has logged in, start thread listening for messages and printing at client
    th = threading.Thread(target=client.listen_messages, args=(username,))
    th.start()
    
    while (True):
        user_input = input("list, send, logout, or delete?")
        client = ChatClient()
        
        if user_input == "list":
            regex = input("Provide a regular expression:")
            result = client.list_accounts(regex)
            print(f'{result}')

        elif user_input == "send":
            destination = input("To:")
            text = input("Message:")
            result = client.send_message(destination=destination, source=username, text=text)
            print(f'{result}')
        
        elif user_input == "logout":
            confirmation = input("Are you sure you want to logout? (y/N)")
            if confirmation == "y" or confirmation == "Y":
                client.logout(username=username)
                print("Successfully logged out")
                username, password = login_ui(client)
                th = threading.Thread(target=client.listen_messages, args=(username,))
                th.start()
            else:
                pass

        elif user_input == "delete":
            password = input("Password:")
            confirmation = input("Are you sure you want to logout? (y/N)")
            if confirmation == "y" or confirmation == "Y":
                result = client.delete_account(username=username, password=password)
                if result.error == True:
                    print(result.message)
                else:
                    print("Successfully deleted")
                    username, password = login_ui(client)
                    th = threading.Thread(target=client.listen_messages, args=(username,))
                    th.start()

        else:
            print("Invalid")
