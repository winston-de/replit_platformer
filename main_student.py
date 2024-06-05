import play
import csv
import pygame

data = []


def load_level_data(name):
    global data
    with open(name, newline='') as csvfile:
        data = list(csv.reader(csvfile))


game = play.new_image("background.png", size=84)
level_files = ["platform.csv", "platform_2.csv"]
boxes = []
game.start_index = 0
game.viewbox_length = 55
game.end_index = game.viewbox_length
game.start_x = 0
game.end_x = 0
game.level_index = 0

load_level_data(level_files[game.level_index])

hero_images = ["pony_left.png", "pony_right.png"]
hero = play.new_image(hero_images[1], x=0, y=0, size=16)
hero.y_velocity = 0

game.win_box = None


def place_box(type, x, row_i):
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
        box.can_collide = True
        box.type = 4
        game.win_box = box
        return box
    elif type == 0:
        return None


# check if the player has hit the win box
@play.repeat_forever
async def check_win_box():
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


def draw_initial_background():
    for i in range(0, len(data)):
        row = data[i]
        boxes.append([])
        for j in range(0, game.end_index):
            type = row[j]
            x = -400 - 20 + (20 * j)
            boxes[i].append(place_box(type, x, i))

        game.end_x = -400 - 20 + (20 * game.end_index-1)
        game.start_x = -400 - 20

draw_initial_background()

hero.jump_debounce = False
@play.repeat_forever
def controls():
    if play.key_is_pressed('right') and not check_wall_collision(1):
        hero.x += 10
        hero.image = hero_images[1]

    if play.key_is_pressed('left') and not check_wall_collision(-1):
        hero.x -= 10
        hero.image = hero_images[0]

    if play.key_is_pressed('space') and not hero.jump_debounce and check_ground_collision():
        hero.y_velocity = 20
        hero.jump_debounce = True
    elif not play.key_is_pressed('space'):
        # prevents the player from holding down the jump key
        hero.jump_debounce = False


hero.touching_ground = False
hero.y_velocity = 0

@play.repeat_forever
def do_physics():
    # adjust y to account for velocity, and adjust velocity to simulate falling
    hero.touching_ground = check_ground_collision()

    if not hero.touching_ground:
        # hero.y_velocity -= 2
        hero.y_velocity = max(-10, hero.y_velocity - 2)
    elif hero.y_velocity < 0:
        hero.y_velocity = 0

    hero.y = hero.y + hero.y_velocity

    if hero.y < -350:
        restart_game()


def restart_game():
    # resets the board, sends the user back to the initial position
    hero.x = 0
    hero.y = 0
    game.end_index = game.viewbox_length
    game.start_index = 0
    game.start_x = 0
    game.end_x = 0
    for row in boxes:
        for box in row:
            if box is not None:
                box.remove()

    boxes.clear()
    draw_initial_background()


def check_ground_collision():
    # check if the player is touching the top of any box on the screen
    for box_row in boxes:
        for box in box_row:
            if box is not None and box.can_collide and hero.is_touching(box) and hero.bottom > box.bottom:
                return True
    return False


def check_wall_collision(x_dir):
    # check if the player is touching the top of any box on the screen
    for box_row in boxes:
        for box in box_row:
            if box is not None and box.can_collide and hero.is_touching(box) and not hero.bottom + 10 > box.top:
                if x_dir == 1 and hero.right > box.left and abs(hero.left - box.right) > 10:
                    return True
                elif x_dir == -1 and hero.left < box.right and abs(hero.right - box.left) > 10:
                    return True
    return False

@play.repeat_forever
def update_background_pos():
    # check if we need to move the background to match the player's position
    if hero.x > 140:
        move_background(-10)
        hero.x -= 10

    if hero.x < -140:
        move_background(10)
        hero.x += 10


def move_background(x):
    for box_row in boxes:
        for box in box_row:
            if box is not None:
                box.x += x

    game.start_x += x
    game.end_x += x

    # offload boxes that are no longer visible in the view window, and load blocks
    # that are soon to be visible

    # background moving left
    if x > 0 and game.end_x > 480:
        if game.start_index > 1:
            game.start_index -= 1
            game.end_index -= 1
            for i in range(0, len(boxes)):
                # get next box to the left, then add it to leftmost position
                row = boxes[i]
                type = data[i][game.start_index]
                box = place_box(type, game.start_x - 20, i)
                row.insert(0, box)

                # remove rightmost box
                to_remove = row.pop(len(row) - 1)
                if to_remove is not None:
                    to_remove.remove()

            game.start_x -= 20
            game.end_x -= 20

    # background moving right
    if x < 0 and game.start_x < -480:
        if game.end_index < len(data[0]) - 1:
            game.start_index += 1
            game.end_index += 1
            for i in range(0, len(boxes)):
                # get next box to right, add it to rightmost position
                row = boxes[i]
                type = data[i][game.end_index]
                box = place_box(type, game.end_x, i)
                row.append(box)

                # remove leftmost box
                to_remove = row.pop(0)
                if to_remove is not None:
                    to_remove.remove()

            game.start_x += 20
            game.end_x += 20

play.start_program()