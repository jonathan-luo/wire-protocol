import socket

user = input("Welcome to <Name TBD>! Please enter your username: ")

# Check whether username alr in use by making a request to server, in which case ask user for password
# Otherwise create new account, request for password

user_exists = False
if (user_exists):
    password = input(f"Welcome back, {user}! Please enter your password: ")

    # TODO: Implement password verification procedure.

else:
    password = input(f"Welcome, {user}! Seems like you're new here! To register, please enter a password: ")
    confirm = input("Please confirm your password: ")
    while (password != confirm):
        password = input("Hmm, seems like your passwords didn't match. Please re-enter your desired password: ")
        confirm = input("Please confirm your password: ")

    # TODO: Send user and password information to server.

# TODO: Connect to server.

task = None
while (task != 'q'):
    task = input('''Please select a task by typing in a letter:
    a -- View all users
    m -- Send new message
    d -- Send undelivered messages in your queue
    q -- Quit/Log out\n''')

    # Implement functionality for each task. Prob should use dict that maps task to function.

