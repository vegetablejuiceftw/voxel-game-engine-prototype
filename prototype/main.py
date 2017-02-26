from bge import logic, events

from time import time
from game import init_game, input_events
from work import do_work
from npc import iterate_npc
from path_finder import PathManager

init_game()
logic.running = True
logic.debug = 0
counter = 0

logic.path_manager = PathManager()


def iterate_pathing_generator():
    logic.path_manager.tick()


def tick_game(cont):
    start = time()
    global counter

    cont.owner['RUNNING'] = logic.running
    cont.owner['DEBUG_MODE'] = logic.debug

    keyboard = logic.keyboard
    if keyboard.events[events.PADMINUS] == logic.KX_INPUT_JUST_ACTIVATED:
        logic.running = not logic.running
    if keyboard.events[events.PADPLUSKEY] == logic.KX_INPUT_JUST_ACTIVATED:
        logic.debug = (logic.debug + 1) % 3

    if logic.running:
        do_work()
        if not counter % 1:
            iterate_npc(cont)
        counter += 1
        iterate_pathing_generator()

    if logic.debug and round(time() - start, 5) >= 0.017:
        print("Game loop took too much time:", round(time() - start, 5))
