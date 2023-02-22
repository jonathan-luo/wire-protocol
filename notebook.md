# Engineering Notebook #

## Connecting to the Server ##
When the user runs the client program, they will be prompted to enter the IP address of the server, which they can then connect to.

We got the computers to communicate by finding the IP address of the server under Mac > Settings > Wifi. One solution was to hardcode this address into the client.py file of the client computer. However, we ended up doing something more dynamic, by allowing users to specify the server IP address that they would connect to as a command-line prompt.

## Logging In/Creating an Account ##
Once logged in and connected to the server, the user will be prompted to enter their username.
If the username exists in the system, then they must enter their password. They have up to 3 tries to enter the correct password. They also have the option to quit, which would then alert the server to close this client. If they correctly enter their password, then they are logged in.
If the username doesn’t exist in the system, then they must create a new password and then enter a confirmation password to make a new account. Whenever they enter the wrong confirmation password, they have the option to quit or retry a different password.

- Onboarding

    The server sees: `0 [args]`

## Selection Screen ##
Once successfully logged in, the user will be greeted with a welcome message, as well as the notification of how many of the same account are logged into the system. They will receive all the undelivered messages. Then, they will receive a selection screen for what they want to do next. The menu consists of:

- List All Accounts

    The server sees: `1 [arg : str]`

    The method by which users can specify their search criteria is as follows: Once they select "View Users" as their desired task, a prompt pops up asking if they would like to submit a wildcard query for specific users. Leaving this prompt blank (i.e., by simply pressing Enter) will return all active users other than the current user, if any. Otherwise, the user can specify, using GLOB wildcard syntax, usernames that they wish to query for. On the backend, searching is done by converting the GLOB query into Regex using the `fnmatch.translate` function. Then, that regex pattern is compiled and used to filter over all active users (other than the current user). If no matches are found, "No users found." is printed, which is the same behavior as when there are no other active users at all.

- Send A Message

    The server sees: `2 [username] [message]`

- Delete Account

    The server sees: `8`

- Quit

    The server sees: `9`

In addition to these selectable operations for users, there also exist hidden operations such as the following, which are also part of our wire protocol definition, but not explicitly available for the user to invoke. These are often part of validating user input, such as ensuring that users send messages only to registered users, or that they can only delete an account when it is only logged into one device.

- Verify Registered User

    The server sees: `3 [username]`

- Verify Account Only Logged In On One Device

    The server sees: `4`

- Log Out All Other Instances

    The server sees: `5`

## Additional Notes on Wire Protocol ##
We chose a buffer size of 1024 as it encapsulates the maximum amount of information that we send over the wire at any given time
(1 (command) + 280 (max string input) * 3 + 4 (dividers) + 16 (time) = 861 bytes), while still being a power of 2.