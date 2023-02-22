import grpc
from concurrent import futures
import time
import chat_pb2_grpc as pb2_grpc
import chat_pb2 as pb2
import threading
import re
import socket

# Associates a unique username with a password
accounts = {}

# Associates a username with a logged-in status
accounts_status = {}

# Associates a user with a dictionary storing senders : list of messages
accounts_queue = {}

class ChatService(pb2_grpc.ChatServicer):
    def __init__(self, *args, **kwargs):
        pass


    def CreateAccount(self, request, context):
        '''
        Creates a new account with the given username and password.
        If the username already exists, an error is returned.
        '''
        username = request.username
        password = request.password
        if username not in accounts:
            accounts[username] = password
            accounts_status[username] = False
            accounts_queue[username] = {}
            result = f'{username} added'
            response = {'message': result, 'error': False}
        else:
            result = "Error: Username already in use"
            response = {'message': result, 'error': True}
        
        return pb2.ServerResponse(**response)


    def DeleteAccount(self, request, context):
        '''
        Deletes the account with the given username and password.
        If the username or password is incorrect, an error is returned.
        '''
        username = request.username
        password = request.password
        if username not in accounts:
            result = f'{username} is not an existing username'
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)
            
        if password != accounts[username]:
            result = f'Wrong password for {username}'
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)

        del(accounts[username])
        result = f'{username} deleted'
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)


    def Login(self, request, context):
        # Once use logs in, server immediately creates a thread for that
        # user that is working on user's behalf
        # Looking for messages
        username = request.username
        password = request.password
        
        if username not in accounts:
            result = f'{username} is not a registered account.'
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)

        if password != accounts[username]:
            result = f"Incorrect password for {username}'s account."
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)
            
        accounts_status[username] = True
        result = f'{username}, you are logged in'
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)


    def Logout(self, request, context):
        '''Logout the client'''
        
        username = request.username
        accounts_status[username] = False
        result = f'{username}, you are logged out'
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)


    def ListAccounts(self, request, context):
        '''Lists the available accounts'''
    
        searchterm = request.searchterm
        pattern = re.compile(searchterm)
        accounts_str = ""
        for account in accounts:
            if pattern.search(account) != None:
                accounts_str += account + " "
        accounts_str = accounts_str[:-1]
        response = {'usernames': accounts_str}
        return pb2.Accounts(**response)


    def SendMessage(self, request, context):
        '''Puts message into the destination user's queue'''

        destination = request.destination
        source = request.source
        text = request.text

        # If the source is not logged in, return an error
        if source not in accounts or accounts_status[source] == False:
            result = "Error: username not valid or not logged in"
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)

        # If the destination is not a valid account, return an error
        if destination not in accounts:
            result = "Error: destination not valid"
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)
            
        if source not in accounts_queue[destination]:
            accounts_queue[destination][source] = [text]
        else:
            accounts_queue[destination][source].append(text)
        result = "Message Sent"
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)


    def ListenMessages(self, request, context):
        username = request.username
        
        while accounts_status[username] == True:
            myDict = accounts_queue[username]
            for sender in list(myDict):
                for msg in myDict[sender]:
                    response = {'destination': username, 'source': sender, 'text': msg}
                    yield pb2.MessageInfo(**response)
                    myDict[sender].remove(msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) # 10 threads
    pb2_grpc.add_ChatServicer_to_server(ChatService(), server) # Add service to server
    server.add_insecure_port('[::]:50051')
    server.start()
    host = socket.gethostbyname(socket.gethostname())
    print(f'Server started on {host}')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()