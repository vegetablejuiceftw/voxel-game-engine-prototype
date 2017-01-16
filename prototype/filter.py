from bge import logic, events

def manager(cont):
    shaders = logic.shaders = getattr(logic, "shaders", {1: False, 2: False, 3: False, 4: False})

    keyboard = logic.keyboard
    JUST_ACTIVATED = logic.KX_INPUT_JUST_ACTIVATED

    for i, keyEvent in enumerate([events.ONEKEY, events.TWOKEY, events.THREEKEY, events.FOURKEY]):

        if keyboard.events[keyEvent] == JUST_ACTIVATED:
            key = i + 1
            if not shaders[key]:
                cont.activate('F' + str(key))
            else:
                cont.activate('R' + str(key))
            shaders[key] = not shaders[key]
