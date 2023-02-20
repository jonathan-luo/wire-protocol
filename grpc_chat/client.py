import grpc
import unary_pb2_grpc as pb2_grpc
import unary_pb2 as pb2

class ChatClient(object):
    def __init__(self):
        self.host = 'localhost'
        self.server_port = 50051

        self.channel = grpc.insecure_channel(
            '{}:{}'.format(self.host, self.server_port))

        self.stub = pb2_grpc.ChatStub(self.channel)

    def create_account(self, name):
        account = pb2.Account(name=name)
        return self.stub.CreateAccount(account)

    def login(self, name):
        account = pb2.Account(name=name)
        return self.stub.Login(account)

    def list_accounts(self):
        noparam = pb2.NoParam()
        return self.stub.ListAccounts(noparam)



if __name__ == '__main__':
    # This is happening in thread 1
    while (True):
        if logged_in == True:
            # get stream 
    
    # This is happening in thread 2
    while (True):
        user_input = input(">")
        client = ChatClient()
        if user_input[0] == "1":
            #client = ChatClient()
            result = client.create_account(name=user_input[2::])
            print(f'{result}')
        elif user_input[0] == "2":
            #client = ChatClient()
            result = client.login(name=user_input[2::])
            print(f'{result}')
        elif user_input[0] == "3":
            #client = ChatClient()
            result = client.list_accounts()
            print(f'{result}')
        else:
            print("Invalid")
