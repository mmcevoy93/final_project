from time import sleep
from serial import Serial
import numpy as np
import cv2
import MazeGen
import time


def wait_for_confirmation():
    '''
        We use this function to 'wait' for the arduino has recieved the sent
        message and loops until the arduino sends the 'Q' character

        Arguments:
            None
        Returns:
            None
    '''
    with Serial("/dev/ttyACM0", baudrate=9600, timeout=0.1) as ser:
        while True:
            line = ser.readline()
            line_string = line.decode("ASCII")
            stripped = line_string.rstrip("\r\n")
            if stripped == 'Q':
                break
            else:
                print('Waiting for Q got: ', stripped)
            sleep(2)


def send_maze(file):
    '''
        This maze takes the generated maze file and sends it to the arduino
        line by line. It also fills the global list maze_array. You may be
        thinking that this might be redundent. Why not just have the MazeGen
        just return this list instead of creating a text file? Well my partner
        and I were working in parallel and I was using the text files were easy
        to make into a test maze that I could practice sending over to the
        arduino while my partner worked on the maze generation and when it came
        down to the colaberation we just suck to it. Adds to our run time
        but it is minimal

        Arguments:
            a read only file type of the maze generation text file
        Returns:
            list of the maze_array for us to use later for movement validation
    '''
    with Serial("/dev/ttyACM0", baudrate=9600, timeout=0.001) as ser:
        out_line = "%"
        encoded = out_line.encode("ASCII")
        ser.write(encoded)
        while True:
            line = ser.readline()
            if not line:
                print("Arduino likely stuck in loop")
                print("Reset arduino if this message appears continuously")
                continue
            line_string = line.decode("ASCII")
            stripped = line_string.rstrip("\r\n")
            if stripped[0] == 'S':   # S indicates the start of the maze gen.
                for l in file:
                    encoded = l.encode("ASCII")
                    ser.write(encoded)
                    maze_array.append(l)
                    # Tried to have a confirmation handshake here after each
                    # line was sent but it was getting stuck half the time
                    # and just worked fine as is.
                o = "O"
                # "O" indicates that all the file has been read and
                # arduino can move on to the move cursour function
                encoded = o.encode("ASCII")
                ser.write(encoded)
                return maze_array
            else:
                out_line = "%"
                # does absolutly nothing but had this in for
                # assignment 1 and it wouldn't work without it
                encoded = out_line.encode("ASCII")
                ser.write(encoded)
            sleep(2)


def validate_movement(input_key, x, y, z, maze_array):
    '''
        this will validate the keys entered to ensure it is a valid move
        if it is the move will be sent to the arduino and the lcd will update
        else nothing will happen and it will return. It does this by checking
        the maze array list and returning the updated x, y coordinates if they
        change

        NOTE: This is where we were having troubles and you will likely be stuck
        check README and maze_clinet.cpp for full details

        Input:
            input_keys:
                0x51 left
                0x52 up
                0x53 right
                0x54 left
            current_location: relative to the maze grid
                x
                y
            z:
                Checks to see if we need to escape the maze.
        Returns:
            new location if cursor moves (x, y)
            old location if cursor stays (x, y)
            z = 1 if an exit condition is met
            z = 0 else
    '''
    valid = False
    if (input_key == "D") and (y != size):  # down arrow keys
        if maze_array[y + 1][x] != "W":
            valid = True
            y += 1
    elif input_key == "R" and (x != size-1):  # right arrow key
        if maze_array[y][x + 1] != "W":
            valid = True
            x += 1
    elif input_key == "U" and (y != 1):  # up arrow keys
        if maze_array[y - 1][x] != "W":
            valid = True
            y -= 1
    elif input_key == "L" and (x != 0):  # left arrow keys
        if maze_array[y][x - 1] != "W":
            valid = True
            x -= 1
    elif input_key == "O":
        # this is the conditon where the escape key is pressed and we need to
        # break out of the maze early
        valid = True
    if maze_array[y][x] == "F":
        # If the end of the maze is reached then we end maze game
        valid = True
        input_key = "O"
        z = 1
    # if one of the above conditions is met then this communication loop is
    # entered and we wait for the arduino to responed that the message has been
    # recieved
    # NOTE This is where our unexpected and unpredictable loop occurs. The
    # problem lies on the arduino side
    if valid:
        with Serial("/dev/ttyACM0", baudrate=9600, timeout=0.001) as ser:
            k = input_key
            encoded = k.encode("ASCII")
            ser.write(encoded)
            while True:
                # we continuously send the input_key to the ardunio until it
                # responds that it got it. Once it does it will be stuck
                # in a loop waiting for us to send 'Q' to indicate that we
                # can move on
                ser.write(encoded)
                line = ser.readline()
                if not line:
                    continue
                line_string = line.decode("ASCII")
                stripped = line_string.rstrip("\r\n")
                if stripped[0] == '*':
                    q = 'Q'
                    encoded = q.encode("ASCII")
                    ser.write(encoded)
                    break
                sleep(1)
    return x, y, z


def title_screen(file, maze_array):
    '''
        This function displays the text boxes you see pop up when you run the
        code. It also takes key input from the user by just having the window
        up and entering keys

        We used a library called opencv which is a handy library for image
        manipulation. I used it heavily in another project so I am familiar
        how it works and used it here.

        This will be in the README but in case you come here first to install it
        on the VM enter this into the terminal

        sudo pip3 install opencv-python


        Arguments:
            text file of maze
            empty list of maze_array to fill later

        Returns:
            None
    '''
    # Set up for text display and font
    font = cv2.FONT_HERSHEY_SIMPLEX
    title_text = "Maze Game"
    enter_text = "Press Enter to generate maze"
    key_text = "Press arrow keys to move"
    escape_text = "Pres Esc to exit"
    over_text = "Game is over pls play again"
    error_text = "If no maze on Arduino press escape and try again"
    check_text = "Ensure arduino looks like the above rectangle before you start"
    small_text = "Press S for small"
    medium_text = "Press M for medium"
    large_text = "Press L for large"
    XL_text = "Press X for extra-large"
    time_text = "Time: "
    title = np.zeros((800, 1500, 3), np.uint8)  # Blank screen we'll add to

    # Simply adds text and shapes to title screen
    cv2.putText(title, title_text, (400, 100), font, 4,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, enter_text, (250, 500), font, 2,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.rectangle(title, (int(1500 / 2) - 80, 175),
                  (int(1500 / 2) + 80, 375), (255, 0, 0), -1)
    cv2.putText(title, check_text, (0, 780), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow("A-MAZE-ING GAME", title)  # displays the title screen
    cv2.moveWindow("A-MAZE-ING GAME", 0, 0)
    once = True
    x, y, z = 0, 1, 0  # intial start postion of Maze. z is just a check
    while True:
        # waitKey will halt the loop until a key is pressed
        # once it is pressed it will check to see if it is one of our keys of
        # intrest 'ENTER' 'ESC' 'UP' 'DOWN' 'LEFT' 'RIGHT'
        input_key = cv2.waitKey(0) & 0xFF
        if input_key == 0x0D and once:  # ENTER and we only want this to occur
            maze_array = send_maze(file)  # send the generated maze to arduino
            # removes the title screen and makes command screen
            cv2.destroyAllWindows()
            title = np.zeros((800, 1500, 3), np.uint8)
            cv2.putText(title, title_text, (350, 100), font, 4,
                        (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(title, key_text, (270, 500), font, 2,
                        (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(title, escape_text, (0, 780), font, 1,
                        (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(title, error_text, (500, 780), font, 1,
                        (255, 255, 255), 2, cv2.LINE_AA)
            once = False
            start = time.time()
        cv2.imshow("A-MAZE-ING GAME", title)
        cv2.moveWindow("A-MAZE-ING GAME", 0, 0)
        if input_key == 0x54 and not once:  # down arrow keys
            x, y, z = validate_movement("D", x, y, 0, maze_array)
        if input_key == 0x53 and not once:  # right arrow key
            x, y, z = validate_movement("R", x, y, 0, maze_array)
        if input_key == 0x52 and not once:  # up arrow keys
            x, y, z = validate_movement("U", x, y, 0, maze_array)
        if input_key == 0x51 and not once:  # left arrow keys
            x, y, z = validate_movement("L", x, y, 0, maze_array)
        if input_key == 0x1B and not once:  # escape
            if not once:
                x, y, z = validate_movement("O", x, y, 0, maze_array)
            break
        if z == 1:
            break
    # Once loop is borken we clear the arduino and remove the command screen
    # and display the display the end game screen.
    end = round(time.time() - start, 2)  # timer for game run time
    cv2.putText(title, small_text, (600, 500), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    title = np.zeros((800, 1500, 3), np.uint8)
    cv2.circle(title, (400, 750), 1500, (0, 0, 255), -1)
    cv2.putText(title, over_text, (70, 300), font, 3,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, escape_text, (0, 780), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, small_text, (600, 400), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, medium_text, (600, 450), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, large_text, (600, 500), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, XL_text, (600, 550), font, 1,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, time_text+str(end), (550, 150), font, 2,
                (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("A-MAZE-ING GAME", title)
    cv2.moveWindow("A-MAZE-ING GAME", 0, 0)
    # players will have the option to either exit or choose the size of the
    # maze for the next game


if __name__ == "__main__":
    size = 15  # intial size of maze. Later player will be able to choose this
    MazeGen.maze_gen(size)  # Generates maze text file
    file = open("sendfile.txt", "r")  # opens file to enable us to read
    maze_array = []  # empty list to fill later
    title_screen(file, maze_array)  # game one
    while True:
        # if player chooses to play again then they will be required to choose
        # maze size then it will loop over
        input_key = cv2.waitKey(0)
        if input_key == 0x1B:  # Escape
            break
        elif (input_key == 0x4C) or (input_key == 0x6C):    # L/l is large
            size = 27
            MazeGen.maze_gen(size)
            file = open("sendfile.txt", "r")
            maze_array = []
            title_screen(file, maze_array)
        elif (input_key == 0x4D) or (input_key == 0x6D):    #M/m is medium
            size = 15
            MazeGen.maze_gen(size)
            file = open("sendfile.txt", "r")
            maze_array = []
            title_screen(file, maze_array)

        elif (input_key == 0x53) or (input_key == 0x73):    #S/s is small
            size = 9
            MazeGen.maze_gen(size)
            file = open("sendfile.txt", "r")
            maze_array = []
            title_screen(file, maze_array)
        elif (input_key == 0x58) or (input_key == 0x78):    #S/s is small
            size = 57
            MazeGen.maze_gen(size)
            file = open("sendfile.txt", "r")
            maze_array = []
            title_screen(file, maze_array)
