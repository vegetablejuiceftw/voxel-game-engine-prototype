from bge import logic, events


def manager(cont):
    shaders = logic.shaders = getattr(logic, "shaders", {1: False, 2: True, 3: False, 4: False})

    keyboard = logic.keyboard

    if keyboard.events[events.LEFTCTRLKEY] == logic.KX_INPUT_ACTIVE:

        for i, keyEvent in enumerate([events.ONEKEY, events.TWOKEY, events.THREEKEY, events.FOURKEY]):

            if keyboard.events[keyEvent] == logic.KX_INPUT_JUST_ACTIVATED:
                key = i + 1
                if not shaders[key]:
                    cont.activate('F' + str(key))
                else:
                    cont.activate('R' + str(key))
                shaders[key] = not shaders[key]
