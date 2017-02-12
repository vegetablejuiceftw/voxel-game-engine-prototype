from game import init_game, input_events
from work import do_work
from npc import iterate_npc, iterate_pathing_generator
from bge import logic, events

init_game()
logic.running = True
logic.debug = 0
counter = 0

def tick_game(cont):
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
