BUFSIZE = 1024

LOGIN_COMMAND = 0 # Command number that signals to clients that they are being asked to login
VIEW_USERS_COMMAND = 1 # Command number that signals to server that they are being asked to view users
SEND_MESSAGE_COMMAND = 2 # Command number that signals to server that they are being asked to deliver a message
CHECK_ACCOUNT_COMMAND = 3 # Command number that signals to server that they are being asked to check if an username is registered
MULTIPLE_LOGIN_COMMAND = 4 # Command number that signals to server that they are being asked to check if an username is logged in on multiple devices
LOGOUT_COMMAND = 5 # Command number that signals to server that they are being asked to log out all instances of an username except the one using socket `client`

RECEIVE_MESSAGE_COMMAND = 6  # Command number that signals to clients that a message is being delivered

QUIT_COMMAND = 9 # Command number that signals to server that the client is wants to disconnect

TIME_FORMAT = '%Y-%m-%d %H:%M'
BUFSIZE = 1024

MAX_MESSAGE_LENGTH = 280     # Character limit for input strings
RECEIVE_MESSAGE_COMMAND = 6  # Command number that overrides inquirer prompts and immediately displays messages received

ILLEGAL_CHARS = {'|'}   # Characters that are not allowed in usernames or passwords or messages to prevent injection attacks