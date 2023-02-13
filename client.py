import socket
import threading


def handle_client(client):
    """ Send and receive messages to and from the server and print them to the console """
    user = login(client)
    
    task = None
    while (task != 'q'):
        task = input('''Please select a task by typing in a letter:
            a -- View all users
            m -- Send new message
            d -- Send undelivered messages in your queue
            q -- Quit/Log out
            ''')
        
        # TODO: Implement functionality for each task.
        if task == 'a':
            client.send("list".encode())
        elif task == 'm':
            message = input("What message would you like to send?")
            recipient = input("Who would you like to send it to?")
            client.send(f"send {recipient} {message}".encode())
        elif task == 'd':
            pass
        elif task == 'q':
            pass


def login(client):
    """ Login the client or create a new account"""
    
    # Asks the server if the username is already in use
    user = input("Please enter your username: ")
    client.send(user.encode())
   
    response = client.recv(1024).decode()
    
    # If the user is already in use, ask for password and check if it matches
    if response == "exists":
        password = input(f"Welcome back, {user}! Please enter your password: ")
        
        client.send(password.encode())
        response = client.recv(1024).decode()
    
        while response == "error":
            password = input("Hmm, seems like your password was incorrect. Please re-enter your password: ")
            client.send(password.encode())
            response = client.recv(1024).decode()
            
        if response == "success":
            print("Successfully logged in!")
    else:
        # If the user is already in use, ask for password and check if it matches
        password = input(f"Welcome, {user}! Seems like you're new here! To register, please enter a password: ")
        confirm = input("Please confirm your password: ")

        # If the passwords don't match, ask for password again
        while (password != confirm):
            password = input("Hmm, seems like your passwords didn't match. Please re-enter your desired password: ")
            confirm = input("Please confirm your password: ")
    
        client.send(password.encode())
        response = client.recv(1024).decode()

        if response == "success":
            print("Successfully registered and logged in!")
            
    return user


def start_client():
    """ Start the client and connect to the server """
    
    # TODO: CHANGE THIS TO THE SERVER'S IP ADDRESS
    host = "localhost" 
    port = 8000

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    # TODO: Come up with a badass name
    print("Welcome to <Name TBD>!")

    receive_thread = threading.Thread(target=handle_client, args=([client]))
    receive_thread.start()


if __name__ == "__main__":
    start_client()
