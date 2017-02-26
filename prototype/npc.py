from bge import logic
from mathutils import Vector
from time import time
from random import random, choice, shuffle, randint

from path_finder import (
    POSSIBLE_MOVES_DICT, is_air, is_solid, is_npc, PathObject, POSSIBLE_MOVES, POSSIBLE_MOVES_VECTORS,
    NearestTargetPathGenerator,
    SimplePathGenerator
)
from animus import AnimusAlpha
from chunk import floored_tuple

scene = logic.getCurrentScene()
logic.npc = []
logic.NPC_TICK_COUNTER = 0
logic.NPC_CURRENT_INDEX = 0
logic.marker = None
logic.epoch = 1


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
        return (
            pos[0] // NPC.ROOM_SIZE * NPC.ROOM_SIZE,
            pos[1] // NPC.ROOM_SIZE * NPC.ROOM_SIZE,
            pos[2] // NPC.ROOM_SIZE * NPC.ROOM_SIZE
        )

    def change_room(self, old):
        if not old:
            NPC.POSITIONS.get(self.room_index(self.pos), set()).discard(self)
            return
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
        x, y, z = self.room_index(self.pos)
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
        shuffle(deltas)

        for dx, dy, dz in deltas:
            check_key = x + dx, y + dy, z + dz
            neighbours = NPC.POSITIONS.get(check_key, [])
            if quick and neighbours:
                c = choice(tuple(neighbours))
                if not c.alive:  # TODO: checkout is broken
                    print("DERPSA SAASAS ASAS")
                    neighbours.remove(c)
                    return None
                return c if c != self else None
            elif not quick:
                for other in neighbours:
                    if other != self and (not type_class or isinstance(other, type_class)):
                        radar.append((self.dist(other), other))
        return sorted(radar, key=lambda k: k[0])

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, vector):
        self.obj.worldPosition = floored_tuple(vector)
        self._pos = self.obj.worldPosition.copy()
        return self._pos

    def register(self, voxel):
        if self.last_voxel:
            self.last_voxel.NPC = None
        if voxel:
            self.old_trace = voxel.trace
            self.last_voxel = voxel
            voxel.NPC = self

    def check_move(self, vector):
        x, y, z = self.pos
        air_space = POSSIBLE_MOVES_DICT.get(floored_tuple(vector))
        if air_space is None:
            return False

        ground = logic.chunks.quick_voxel((x, y, z - 1))
        if is_air(ground):
            return False

        for dx, dy, dz in air_space:
            if not is_air(logic.chunks.quick_voxel((x + dx, y + dy, z + dz))):
                return False
        return True

    def move(self, vector):
        if self.check_move(vector):
            target_pos = self.pos + vector
            ground = logic.chunks.quick_voxel((target_pos[0], target_pos[1], target_pos[2] - 1))
            if is_solid(ground) or self.stupid and not vector.z:
                target = logic.chunks.quick_voxel(target_pos)
                old = Vector(self._pos)
                self.pos += vector
                self.register(target)
                self.change_room(old)

                if self.visual:
                    if vector and vector.length != 0:
                        self.visual.alignAxisToVect(vector, 1)
                    else:
                        self.visual.alignAxisToVect((0, 1, 0), 1)
                    self.visual.alignAxisToVect((0, 0, 1), 2)

                return True
        return False

    def tick(self):
        self.info.visible = logic.debug != 0
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
        self.change_room(None)
        if not self.obj.invalid:
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
                if path_generator:
                    logic.path_manager.append(path_generator)
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
        up = logic.chunks.quick_voxel(self.pos + Vector((0, 0, 1)))
        if is_air(up):
            self.maturity = 0
            self.hunger = 50
            child = scene.addObject(self.obj.name, "World_manager")
            child.worldPosition = self.pos + Vector((0, 0, 1))
            logic.npc.append(self.__class__(child))


class Sheep(NPC):
    def __init__(self, arg):
        super(Sheep, self).__init__(arg)
        self.stupid = True
        self.name = str(NPC.COUNT) + 'SHEEP'
        self.last_move_timeout = 0
        self.last_move = Vector((0, 0, 0))
        self.last_bump = logic.epoch
        self.last_plan = []

    def can_breed(self):
        return self.maturity >= 100

    def tick(self):
        super(Sheep, self).tick()

        self.stupid = random() > 0.97

        if self.energy > 1:
            self.brownian_motion()

        if random() > 0.98:
            self.info.text = 'Baah %.1f' % self.maturity
        elif random() > 0.97:
            self.info.text = '%.2f' % self.maturity

        trace = self.old_trace[0]

        if logic.epoch - self.last_bump > 7 and trace > 93:
            self.maturity = min(self.maturity + trace * 0.006, 100)

    def closest_move(self, direction):
        largest_number, random_vec, vecs = 0, None, list(POSSIBLE_MOVES_VECTORS)
        shuffle(vecs)
        for temp_random_vec in vecs:
            angle = direction.angle(temp_random_vec, 0)
            if angle > largest_number - random() * 1 and self.check_move(temp_random_vec):
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
            direction = too_close_npc.pos - self.pos
            random_vec = self.closest_move(direction)
            if not random_vec:
                return
            self.last_bump = logic.epoch
            self.last_plan = random_vec
        else:
            for i in range(5):
                random_vec = choice(POSSIBLE_MOVES_VECTORS)
                if self.check_move(random_vec):
                    break

        if random_vec and self.move(random_vec):
            self.walk_expend()
            self.last_move = random_vec
            self.last_move_timeout = 3


class Human(NPC):
    def __init__(self, arg, path_generator=SimplePathGenerator):
        super(Human, self).__init__(arg)
        self.task = self.travel()
        self.stupid = False
        self.info.text = 'I am Human.'
        self.path_generator = path_generator

    def tick(self):
        super(Human, self).tick()
        if self.pos == logic.marker:
            from game import remove_marker
            remove_marker()
        next(self.task)

    def path_generator_factory(self):
        if logic.marker:
            node_x, node_y, node_z = self.pos
            broken = False
            for delta_vector, airspace in POSSIBLE_MOVES_DICT.items():
                new_x, new_y, new_z = node_x + delta_vector[0], node_y + delta_vector[1], node_z + delta_vector[2]
                new_ground_pos = new_x, new_y, new_z - 1
                ground = logic.chunks.quick_voxel(new_ground_pos)
                if not is_solid(ground):
                    continue
                broken = False
                for delta_air_x, delta_air_y, delta_air_z in airspace:
                    new_air_pos = (
                        node_x + delta_air_x,
                        node_y + delta_air_y,
                        node_z + delta_air_z,
                    )
                    current_voxel = logic.chunks.quick_voxel(new_air_pos)
                    if is_npc(current_voxel) and current_voxel.NPC != self:
                        broken = True
                        break
                if not broken:
                    break
            if broken:
                return

            start = floored_tuple(self.pos)
            return self.path_generator(start, logic.marker, self, search_limit=4000, destructive=randint(0, 1))


class Wolf(NPC):
    def __init__(self, arg):
        super(Wolf, self).__init__(arg)
        self.task = self.travel()
        self.energy = 100
        self.hunger = 25

    def tick(self):
        super(Wolf, self).tick()
        self.state = self.state.tick()
        self.info.text = self.status()

    def get_food(self):
        for dv in POSSIBLE_MOVES_VECTORS:
            check_pos = self.pos + dv
            check_voxel = logic.chunks.quick_voxel(check_pos)
            if is_npc(check_voxel):
                prey = check_voxel.NPC
                if isinstance(prey, Sheep):
                    return prey

    def path_generator_factory(self):
        start = floored_tuple(self.pos)
        return NearestTargetPathGenerator(start, Sheep, self, search_limit=70 + int(self.hunger))


def init_human(obj):
    logic.npc.append(Human(obj))


def init_wolf(obj):
    logic.npc.append(Wolf(obj))


def init_sheep(obj):
    logic.npc.append(Sheep(obj))


def iterate_npc(cont):
    npc_count = len(logic.npc)
    cont.owner['NPC_COUNT'] = npc_count

    if not npc_count:
        return

    start_time = time()
    epoch = logic.epoch
    if logic.NPC_TICK_COUNTER != epoch:
        if not logic.path_manager.tasks:
            if npc_count > logic.NPC_CURRENT_INDEX:
                while time() - start_time < 0.004 and npc_count > logic.NPC_CURRENT_INDEX:
                    npc = logic.npc[logic.NPC_CURRENT_INDEX]
                    if not npc.alive:
                        npc.die()
                        logic.npc.remove(npc)
                        npc_count = len(logic.npc)
                        continue
                    npc.tick()
                    logic.NPC_CURRENT_INDEX += 1
            else:
                logic.NPC_CURRENT_INDEX = 0
                logic.NPC_TICK_COUNTER = epoch
                logic.epoch += 1
                cont.owner['SHEEP_COUNT'] = 0
                cont.owner['WOLF_COUNT'] = 0
                for npc in logic.npc:
                    cont.owner['SHEEP_COUNT'] += type(npc) == Sheep
                    cont.owner['WOLF_COUNT'] += type(npc) == Wolf
