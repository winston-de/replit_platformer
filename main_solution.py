import play
import csv
import pygame
import pygame

level_data = []  # defines the boxes in the format of a 2D list


def load_level_data(name):
    global level_data
    with open(name, newline='') as csvfile:
        level_data = list(csv.reader(csvfile))


game = play.new_image("background.png", size=84)
level_files = ["platform.csv", "platform_2.csv"]
boxes = []
game.start_index = 0
game.viewbox_length = 55  # number of boxes loaded at a time
game.end_index = game.viewbox_length  # data index for the last column of blocks loaded
game.start_x = 0  # x position of the first column of blocks loaded
game.end_x = 0  # x position of the last column of blocks loaded
game.level_index = 0  # which level the player is on

load_level_data(level_files[game.level_index])

hero_images = ["pony_left.png", "pony_right.png"]
hero = play.new_image(hero_images[1], x=0, y=0, size=16)
hero.y_velocity = 0

game.win_box = None  # step on this, win the game


def place_box(type, x, row_i):
    """Draw a box on the screen"""
    type = int(type)
    y = 300 + 20 - (20 * row_i)
    if type == 1:
        # box = play.new_box(x=x, y=y, width=24, height=24, color='blue')
        box = play.new_image("dirt.jpeg", x=x, y=y, size=24)
        box.can_collide = True
        box.type = 1
        return box
    elif type == 2:
        box = play.new_box(x=x, y=y, width=24, height=24, color='green')
        box.can_collide = True
        box.type = 2
        return box
    elif type == 3:
        box = play.new_text("Get to the blue box at the end!", x=x, y=y, size=50)
        box.can_collide = False
        box.type = 3
        return box
    elif type == 4:
        # when the player touches this block, game goes to the next level
        box = play.new_box(x=x, y=y, width=24, height=24, color='blue')
        box.can_collide = False
        box.type = 4
        game.win_box = box
        return box
    elif type == 0:
        return None


@play.repeat_forever
async def check_win_box():
    """check if the player has hit the win box, if so go to the next level"""
    if game.win_box is not None and hero.is_touching(game.win_box):
        game.win_box = None
        game.level_index += 1

        if game.level_index >= len(level_files):
            game.level_index = 0

        load_level_data(level_files[game.level_index])
        restart_game()

        win_text = play.new_text(f"Level {game.level_index + 1}", y=200)
        await play.timer(seconds=2)
        win_text.remove()


def draw_initial_level():
    """Draw the initial boxes in view"""
    for i in range(0, len(level_data)):
        row = level_data[i]
        boxes.append([])
        for j in range(0, game.end_index):
            type = row[j]
            x = -400 - 20 + (20 * j)
            boxes[i].append(place_box(type, x, i))

        game.end_x = -400 - 20 + (20 * game.end_index-1)
        game.start_x = -400 - 20


draw_initial_level()  # initial setup

hero.jump_debounce = False  # prevents infinite jumping
hero.touching_ground = False
hero.y_velocity = 0


@play.repeat_forever
def controls():
    """Handles all player movement, run every frame"""
    if play.key_is_pressed('d') or play.key_is_pressed('right'):
        hero.x += 10
        hero.image = hero_images[1]
        if check_collision():  # if the movement has caused a collision, undo it
            hero.x -= 10

    if play.key_is_pressed('a') or play.key_is_pressed('left'):
        hero.x -= 10
        hero.image = hero_images[0]
        if check_collision():  # if the movement has caused a collision, undo it
            hero.x += 10

    if play.key_is_pressed('space') and not hero.jump_debounce and hero.touching_ground:
        hero.y_velocity = 20
        hero.jump_debounce = True
    elif not play.key_is_pressed('space'):
        # prevents the player from holding down the jump key
        hero.jump_debounce = False


@play.repeat_forever
def do_physics():
    # adjust y to account for velocity, and adjust velocity to simulate falling

    if not hero.touching_ground:  # simulate gravity
        hero.y_velocity -= 2
        hero.y_velocity = max(-10, hero.y_velocity)  # terminal velocity prevents clipping

    hero.y = hero.y + hero.y_velocity
    if check_collision():
        hero.y = hero.y - hero.y_velocity  # if the movement has caused a collision, undo it and set velocity to zero
        hero.y_velocity = 0
        hero.touching_ground = True
    else:
        hero.touching_ground = False

    if hero.y < -350:  # player fell out of the world :(
        restart_game()


def restart_game():
    """Resets the view, sends the user back to the initial position"""
    hero.x = 0
    hero.y = 0
    game.end_index = game.viewbox_length
    game.start_index = 0
    game.start_x = 0
    game.end_x = 0

    # clear all loaded boxes
    for row in boxes:
        for box in row:
            if box is not None:
                box.remove()

    boxes.clear()
    draw_initial_level()


def check_collision():
    """Check if the player is touching any box on the screen"""
    for box_row in boxes:
        for box in box_row:
            if box is not None and box.can_collide and hero.is_touching(box):
                return True
    return False


@play.repeat_forever
def update_background_pos():
    """Check if the player has moved too far in either direction, and move the background as needed"""
    if hero.x > 140:
        move_background(-10)
        hero.x -= 10

    if hero.x < -140:
        move_background(10)
        hero.x += 10


def move_background(x):
    """Moves the background by x, unloading old boxes and loading new ones as needed"""
    for box_row in boxes:
        for box in box_row:
            if box is not None:
                box.x += x

    # these need to be updated so the program knows where to draw new boxes
    game.start_x += x
    game.end_x += x

    # offload boxes that are no longer visible in the view window, and load blocks
    # that are soon to be visible

    # background moving left
    if x > 0 and game.end_x > 440:
        if game.start_index > 1:
            game.start_index -= 1
            game.end_index -= 1
            for i in range(0, len(boxes)):
                # get next box to the left, then add it to leftmost position
                row = boxes[i]
                type = level_data[i][game.start_index]
                box = place_box(type, game.start_x - 20, i)
                row.insert(0, box)

                # remove rightmost box
                to_remove = row.pop(len(row) - 1)
                if to_remove is not None:
                    to_remove.remove()

            game.start_x -= 20
            game.end_x -= 20

    # background moving right
    if x < 0 and game.start_x < -440:
        if game.end_index < len(level_data[0]) - 1:
            game.start_index += 1
            game.end_index += 1
            for i in range(0, len(boxes)):
                # get next box to right, add it to rightmost position
                row = boxes[i]
                type = level_data[i][game.end_index]
                box = place_box(type, game.end_x, i)
                row.append(box)

                # remove leftmost box
                to_remove = row.pop(0)
                if to_remove is not None:
                    to_remove.remove()

            game.start_x += 20
            game.end_x += 20


play.start_program()