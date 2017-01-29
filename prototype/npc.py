from bge import logic, render
from mathutils import Vector
from time import time
from random import random, choice

from path_finder import (
    POSSIBLE_MOVES_DICT, is_air, is_solid, is_npc, PathGenerator, PathObject, POSSIBLE_MOVES, PathManager,
    NearestTargetPathGenerator,
    HybridPathGenerator,
    SimplePathGenerator
)
from animus import AnimusAlpha
from chunk import floored_tuple


scene = logic.getCurrentScene()
logic.npc = []
logic.PathManager = PathManager()
logic.NPC_TICK_COUNTER = 0
logic.NPC_CURRENT_INDEX = 0
logic.NPC_TIME_CONSTANT = 0.01
logic.marker = 0, 0, 0


class NPC(AnimusAlpha):
    POS_CHECK = None
    POSITIONS = {}
    ROOM_SIZE = 8
    COUNT = 0

    def __init__(self, obj):
        super(NPC, self).__init__()
        NPC.POS_CHECK = logic.chunks.raycast

        pos = floored_tuple(obj.worldPosition)
        obj.worldPosition = Vector(pos)
        self._pos = obj.worldPosition

        self.last_voxel = self.POS_CHECK(self.pos)[1]
        self.register(self.last_voxel)
        self.obj = obj
        self.visual = obj.children.get(obj.name + '_visual')
        self.info = obj.children.get(obj.name + '_text')
        self.alive = True
        self.lastMove = Vector((0, 0, 0))

        self.target = None
        self.path = None

        self.stupid = True

        self.last_tick = time()
        self.energy = 0

        NPC.COUNT += 1
        self.name = 'NPC_BASIC'

    def relative_move(self, other):
        relative_vector = other - self.pos
        return self.move(relative_vector)

    @staticmethod
    def room_index(pos):
        return tuple(i // NPC.ROOM_SIZE * NPC.ROOM_SIZE for i in pos)

    def change_room(self, old):
        key = self.room_index(old)
        room = NPC.POSITIONS.get(key)
        if room:
            room.discard(self)

        key = self.room_index(self.pos)
        if key in NPC.POSITIONS:
            NPC.POSITIONS[key].add(self)
        else:
            NPC.POSITIONS[key] = {self}

    def dist(self, other):
        return (self.pos - other.pos).length

    def near(self, type_class, quick=False):
        key = self.room_index(self.pos)
        deltas = [(0, 0, 0), (-NPC.ROOM_SIZE, 0, 0), (0, -NPC.ROOM_SIZE, 0), (0, 0, -NPC.ROOM_SIZE),
                  (0, 0, NPC.ROOM_SIZE), (0, NPC.ROOM_SIZE, 0), (NPC.ROOM_SIZE, 0, 0),
                  (-NPC.ROOM_SIZE, -NPC.ROOM_SIZE, 0), (-NPC.ROOM_SIZE, 0, -NPC.ROOM_SIZE),
                  (-NPC.ROOM_SIZE, 0, NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, NPC.ROOM_SIZE, 0),
                  (0, -NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (0, -NPC.ROOM_SIZE, NPC.ROOM_SIZE),
                  (0, NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (0, NPC.ROOM_SIZE, NPC.ROOM_SIZE),
                  (NPC.ROOM_SIZE, -NPC.ROOM_SIZE, 0), (NPC.ROOM_SIZE, 0, -NPC.ROOM_SIZE),
                  (NPC.ROOM_SIZE, 0, NPC.ROOM_SIZE), (NPC.ROOM_SIZE, NPC.ROOM_SIZE, 0),
                  (-NPC.ROOM_SIZE, -NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, -NPC.ROOM_SIZE, NPC.ROOM_SIZE),
                  (-NPC.ROOM_SIZE, NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, NPC.ROOM_SIZE, NPC.ROOM_SIZE),
                  (NPC.ROOM_SIZE, -NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (NPC.ROOM_SIZE, -NPC.ROOM_SIZE, NPC.ROOM_SIZE),
                  (NPC.ROOM_SIZE, NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (NPC.ROOM_SIZE, NPC.ROOM_SIZE, NPC.ROOM_SIZE)]
        radar = []
        count = 0

        for dV in deltas:
            check_key = (key[0] + dV[0], key[1] + dV[1], key[2] + dV[2])
            neighbours = NPC.POSITIONS.get(check_key, [])
            for other in neighbours:
                count += 1
                if not type_class or isinstance(other, type_class):
                    dist = self.dist(other)
                    if quick:
                        return [(dist, other)]
                    radar.append((dist, other))
        return sorted(radar, key=lambda x: x[0])

    @property
    def pos(self):
        return Vector(self._pos)

    def register(self, voxel):
        if self.last_voxel:
            self.last_voxel.NPC = None
        if voxel:
            self.last_voxel = voxel
            voxel.NPC = self

    def recharge(self):
        self.energy += time() - self.last_tick
        self.last_tick = time()

    def move(self, vector):
        if self.visual:
            if vector.length != 0:
                self.visual.alignAxisToVect(vector, 1)
            else:
                self.visual.alignAxisToVect((0, 1, 0), 1)
            self.visual.alignAxisToVect((0, 0, 1), 2)

        air_space = POSSIBLE_MOVES_DICT.get(floored_tuple(vector))

        if air_space is None:
            return False

        for deltaAirVector in air_space:
            new_air_pos = (
                self.pos[0] + deltaAirVector[0],
                self.pos[1] + deltaAirVector[1],
                self.pos[2] + deltaAirVector[2]
            )
            _, voxel = logic.chunks.raycast(new_air_pos)
            if not is_air(voxel):
                break
        else:
            target_pos = self.pos + vector
            _, ground = logic.chunks.raycast((target_pos[0], target_pos[1], target_pos[2] - 1))
            if is_solid(ground):
                _, target_voxel = self.POS_CHECK(target_pos)
                old = Vector(self._pos)
                self._pos += vector
                self.register(target_voxel)
                self.change_room(old)
                return True
        return False

    def tick(self):
        self.gravity()

    def gravity(self):
        standing_pos = self.pos + Vector((0, 0, -1))
        standing_voxel = self.POS_CHECK(standing_pos)[1]
        if is_air(standing_voxel):
            old = Vector(self._pos)
            self._pos += Vector((0, 0, -1))
            self.register(standing_voxel)
            self.change_room(old)

        if self.pos.z < -100:
            self.die()

    def die(self):
        self.alive = False
        self.register(None)
        self.obj.endObject()

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return PathGenerator(start, logic.marker, self)

    def check_for_food(self):
        pass

    def travel(self):
        waiting = False

        while True:
            if not waiting:
                path_generator = self.path_generator_factory()
                logic.PathManager.append(path_generator)
                waiting = True
                self.path = None
            # path has arrived
            elif self.path is not None:
                # path is bad
                if self.path and not self.path.valid():
                    waiting = False
                else:
                    path_obj = self.path.path.pop(-1)
                    path_obj.assign(self)
                    state = path_obj.tick()
                    while state == PathObject.PATH_WAIT:
                        yield
                        state = path_obj.tick()

                    if state == PathObject.PATH_FAIL or not self.path.valid():
                        self.check_for_food()
                        waiting = False
            yield


class Sheep(NPC):
    def __init__(self, arg):
        super(Sheep, self).__init__(arg)
        self.stupid = True
        self.name = str(NPC.COUNT) + 'SHEEP'

    def tick(self):
        if self.energy > 0:
            self.brownian_motion()
            self.energy -= 0.21
        self.gravity()
        self.recharge()

        if random() > 0.98:
            self.info.text = 'Baah'
        elif random() > 0.97:
            self.info.text = ''

    def brownian_motion(self):
        maximum = 60
        dangerous_npc = self.near(Wolf, quick=True) + self.near(StateWolf, quick=True)

        if dangerous_npc:
            dist, danger = dangerous_npc[0]
            direction = Vector(danger.pos) - self.pos
            distance = min(direction.length, maximum)
            valid = False
            while not valid:
                random_vec = Vector(choice(list(POSSIBLE_MOVES_DICT.keys())))
                valid = direction.angle(random_vec, 999) > random() * (maximum - distance) / maximum * 4
            render.drawLine(self.pos, self.pos + random_vec * 5, (1, 0.1, 0.5))
            self.move(random_vec)
            self.lastMove = random_vec
        else:
            delta_vector = choice(list(POSSIBLE_MOVES_DICT.keys()))
            self.move(Vector(delta_vector))


class Wolf(NPC):
    def __init__(self, arg):
        super(Wolf, self).__init__(arg)
        self.task = self.travel()
        self.stupid = False

    def tick(self):
        self.gravity()
        self.recharge()
        next(self.task)

    def check_for_food(self):
        for dv in POSSIBLE_MOVES:
            check_pos = self.pos + Vector(dv)
            _, check_voxel = self.POS_CHECK(check_pos)
            if is_npc(check_voxel):
                prey = check_voxel.NPC
                if isinstance(prey, Sheep):
                    print("KILLED", prey)
                    prey.die()

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return NearestTargetPathGenerator(start, Sheep, self, search_limit=200)


class Human(NPC):
    def __init__(self, arg, path_generator=HybridPathGenerator):
        super(Human, self).__init__(arg)
        self.task = self.travel()
        self.stupid = False
        self.info.text = 'I am Human.'
        self.path_generator = SimplePathGenerator

    def tick(self):
        self.gravity()
        self.recharge()
        next(self.task)

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return self.path_generator(start, logic.marker, self, search_limit=9000)


class StateWolf(NPC):
    def __init__(self, arg):
        super(StateWolf, self).__init__(arg)
        self.task = self.travel()

    def tick(self):
        self.gravity()
        self.state = self.state.tick()
        self.info.text = self.status()

    def get_food(self):
        for dv in POSSIBLE_MOVES:
            check_pos = self.pos + Vector(dv)
            _, check_voxel = self.POS_CHECK(check_pos)
            if is_npc(check_voxel):
                prey = check_voxel.NPC
                if isinstance(prey, Sheep):
                    return prey

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return NearestTargetPathGenerator(start, Sheep, self, search_limit=200)


def init_human(cont):
    logic.npc.append(Human(cont.owner))


def init_wolf(cont):
    logic.npc.append(StateWolf(cont.owner))


def init_sheep(cont):
    logic.npc.append(Sheep(cont.owner))


def iterate_pathing_generator():
    logic.PathManager.tick()


def iterate_npc(cont):
    npc_count = len(logic.npc)
    cont.owner['npc_count'] = npc_count
    if not npc_count:
        return

    start_time = time()
    epoch = start_time // logic.NPC_TIME_CONSTANT

    if logic.NPC_TICK_COUNTER != epoch:
        if npc_count > logic.NPC_CURRENT_INDEX:
            while time() - start_time < 0.004 and npc_count > logic.NPC_CURRENT_INDEX:
                npc = logic.npc[logic.NPC_CURRENT_INDEX]
                if not npc.alive:
                    logic.npc.remove(npc)
                    del npc
                    npc_count = len(logic.npc)
                    continue
                npc.tick()
                logic.NPC_CURRENT_INDEX += 1

        else:
            logic.NPC_CURRENT_INDEX = 0
            logic.NPC_TICK_COUNTER = epoch
