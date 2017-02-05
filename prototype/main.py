from game import init_game, input_events
from work import do_work
from npc import iterate_npc, iterate_pathing_generator
from bge import logic, events

init_game()

running = True
def tick_game(cont):
    global running

    keyboard = logic.keyboard
    JUST_ACTIVATED = logic.KX_INPUT_JUST_ACTIVATED

    if keyboard.events[events.PADMINUS] == JUST_ACTIVATED:
        running = not running

    if running:
        do_work()
        iterate_npc(cont)
        iterate_pathing_generator()
