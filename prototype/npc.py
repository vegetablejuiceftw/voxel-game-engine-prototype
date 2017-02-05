from bge import logic, render
from mathutils import Vector
from time import time
from random import random, choice

from path_finder import (
    POSSIBLE_MOVES_DICT, is_air, is_solid, is_npc, PathObject, POSSIBLE_MOVES, POSSIBLE_MOVES_VECTORS, PathManager,
    NearestTargetPathGenerator,
    SimplePathGenerator
)
from animus import AnimusAlpha
from chunk import floored_tuple

scene = logic.getCurrentScene()
logic.npc = []
logic.PathManager = PathManager()
logic.NPC_TICK_COUNTER = 0
logic.NPC_CURRENT_INDEX = 0
logic.NPC_TIME_CONSTANT = 0.002
logic.marker = 0, 0, 0
logic.epoch = lambda: time() // logic.NPC_TIME_CONSTANT


class NPC(AnimusAlpha):
    POSITIONS = {}
    ROOM_SIZE = 8
    COUNT = 0

    def __init__(self, obj):
        super(NPC, self).__init__()

        pos = floored_tuple(obj.worldPosition)
        obj.worldPosition = Vector(pos)
        self._pos = obj.worldPosition

        self.last_voxel = logic.chunks.quick_voxel(self.pos)
        self.register(self.last_voxel)
        self.obj = obj
        self.visual = obj.children.get(obj.name + '_visual')
        self.info = obj.children.get(obj.name + '_text')
        self.alive = True

        self.target = None
        self.path = None

        self.stupid = True

        self.energy = 0

        NPC.COUNT += 1
        self.name = 'NPC_BASIC'

        self.old_trace = 0, None

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
            check_key = key[0] + dV[0], key[1] + dV[1], key[2] + dV[2]
            neighbours = NPC.POSITIONS.get(check_key, [])
            for other in neighbours:
                count += 1
                if other != self and (not type_class or isinstance(other, type_class)):
                    dist = self.dist(other)
                    if quick:
                        return other
                    radar.append((dist, other))
        return sorted(radar, key=lambda x: x[0])

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, vector):
        self.obj.worldPosition = floored_tuple(vector)
        self._pos = self.obj.worldPosition.copy()
        return self._pos

    def register(self, voxel):
        self.old_trace = self.last_voxel.trace
        if self.last_voxel:
            self.last_voxel.NPC = None
        if voxel:
            self.last_voxel = voxel
            voxel.NPC = self

    def move(self, vector):
        if self.visual:
            if vector.length != 0:
                self.visual.alignAxisToVect(vector, 1)
            else:
                self.visual.alignAxisToVect((0, 1, 0), 1)
            self.visual.alignAxisToVect((0, 0, 1), 2)

        x, y, z = self.pos
        ground = logic.chunks.quick_voxel((x, y, z - 1))
        if not is_solid(ground):
            return False

        air_space = POSSIBLE_MOVES_DICT.get(floored_tuple(vector))

        if air_space is None:
            return False

        for deltaAirVector in air_space:
            new_air_pos = (
                x + deltaAirVector[0],
                y + deltaAirVector[1],
                z + deltaAirVector[2]
            )
            if not is_air(logic.chunks.quick_voxel(new_air_pos)):
                break
        else:
            target_pos = self.pos + vector
            ground = logic.chunks.quick_voxel((target_pos[0], target_pos[1], target_pos[2] - 1))
            if is_solid(ground) or self.stupid:
                target = logic.chunks.quick_voxel(target_pos)
                old = Vector(self._pos)
                self.pos += vector
                self.register(target)
                self.change_room(old)
                return True
        return False

    def tick(self):
        self._pos = self.obj.worldPosition.copy()
        if self.health <= 0:
            print("dieded")
            return self.die()
        self.gravity()
        self.recharge()
        if self.can_breed():
            self.breed()

    def gravity(self):
        standing_pos = self.pos + Vector((0, 0, -1))
        standing_voxel = logic.chunks.quick_voxel(standing_pos)
        if is_air(standing_voxel):
            old = Vector(self._pos)
            self.pos += Vector((0, 0, -1))
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
        return SimplePathGenerator(start, logic.marker, self)

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

    def breed(self):
        up = logic.chunks.quick_voxel(self.pos + Vector((0,0,1)))
        if is_air(up):
            self.maturity = 0
            self.hunger = 50
            child = scene.addObject(self.obj.name, self.obj)
            child.worldPosition = self.pos + Vector((0,0,1))


class Sheep(NPC):
    def __init__(self, arg):
        super(Sheep, self).__init__(arg)
        self.stupid = True
        self.name = str(NPC.COUNT) + 'SHEEP'
        self.last_move_timeout = 0
        self.last_move = Vector((0, 0, 0))
        self.last_bump = logic.epoch()

    def tick(self):
        super(Sheep, self).tick()

        self.stupid = False
        if random() > 0.97:
            self.stupid = not self.stupid

        if self.energy > 1:
            self.brownian_motion()

        if random() > 0.98:
            self.info.text = 'Baah %.1f' % self.maturity
        elif random() > 0.97:
            self.info.text = '%.2f' % self.maturity

        if logic.epoch() - self.last_bump:
            self.maturity = min(self.maturity + (self.old_trace[0] > 40) * 0.5, 100)

    @staticmethod
    def closest_move(direction):
        largest_number, random_vec = 0, None
        while not largest_number:
            for i in range(len(POSSIBLE_MOVES_VECTORS)):
                temp_random_vec = choice(POSSIBLE_MOVES_VECTORS)
                angle = direction.angle(temp_random_vec, 0)
                if angle > largest_number:
                    largest_number, random_vec = angle, temp_random_vec
        return random_vec

    def brownian_motion(self):
        if self.last_move_timeout:
            self.last_move_timeout -= 1
            if not self.move(self.last_move):
                self.last_move_timeout = 0
                return
            self.walk_expend()
            return

        too_close_npc = self.near(None, quick=True)
        if too_close_npc:
            pos = self.pos
            direction = too_close_npc.pos - pos
            random_vec = self.closest_move(direction)
            render.drawLine(pos, pos + random_vec * 5, (1, 0.1, 0.5))
            self.last_bump = logic.epoch()
        else:
            random_vec = choice(POSSIBLE_MOVES_VECTORS)

        if self.move(random_vec):
            self.walk_expend()
            self.last_move = random_vec
            self.last_move_timeout = 5


class Human(NPC):
    def __init__(self, arg, path_generator=SimplePathGenerator):
        super(Human, self).__init__(arg)
        self.task = self.travel()
        self.stupid = False
        self.info.text = 'I am Human.'
        self.path_generator = path_generator

    def tick(self):
        super(Human, self).tick()
        next(self.task)

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return self.path_generator(start, logic.marker, self, search_limit=4000)


class Wolf(NPC):
    def __init__(self, arg):
        super(Wolf, self).__init__(arg)
        self.task = self.travel()
        self.energy = 100

    def tick(self):
        super(Wolf, self).tick()
        self.state = self.state.tick()
        self.info.text = self.status()

    def get_food(self):
        for dv in POSSIBLE_MOVES:
            check_pos = self.pos + Vector(dv)
            check_voxel = logic.chunks.quick_voxel(check_pos)
            if is_npc(check_voxel):
                prey = check_voxel.NPC
                if isinstance(prey, Sheep):
                    return prey

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return NearestTargetPathGenerator(start, Sheep, self, search_limit=50 + int(self.hunger) * 7)


def init_human(cont):
    logic.npc.append(Human(cont.owner))


def init_wolf(cont):
    logic.npc.append(Wolf(cont.owner))


def init_sheep(cont):
    logic.npc.append(Sheep(cont.owner))


def iterate_pathing_generator():
    logic.PathManager.tick()


def iterate_npc(cont):
    npc_count = len(logic.npc)
    cont.owner['NPC_COUNT'] = npc_count
    if not npc_count:
        return

    start_time = time()
    epoch = logic.epoch()

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
