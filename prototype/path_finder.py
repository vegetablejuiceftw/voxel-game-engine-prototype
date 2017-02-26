from bge import logic
from mathutils import Vector
from time import time
from random import random, randint
from heapq import *
from collections import deque

from work import RemoveWork
from chunk import floored_tuple

scene = logic.getCurrentScene()

DEBUG_NORMAL = lambda: logic.debug != 0
DEBUG_HEAVY = lambda: logic.debug > 1

# TODO: different moves for different creatures
POSSIBLE_MOVES_DICT = {
    # (-1, -1, 0): ((0, -1, 0), (-1, 0, 0), (-1, -1, 0)),
    (-1, 0, 0): ((-1, 0, 0),),
    # (-1, 1, 0): ((0, 1, 0), (-1, 0, 0), (-1, 1, 0)),
    (0, -1, 0): ((0, -1, 0),),
    (0, 1, 0): ((0, 1, 0),),
    # (1, -1, 0): ((0, -1, 0), (1, 0, 0), (1, -1, 0)),
    (1, 0, 0): ((1, 0, 0),),
    # (1, 1, 0): ((0, 1, 0), (1, 0, 0), (1, 1, 0)),

    (-1, 0, -1): ((-1, 0, 0), (-1, 0, -1),),
    (0, -1, -1): ((0, -1, 0), (0, -1, -1),),
    (0, 1, -1): ((0, 1, 0), (0, 1, -1),),
    (1, 0, -1): ((1, 0, 0), (1, 0, -1),),
    (-1, 0, 1): ((0, 0, 1), (-1, 0, 1),),
    (0, -1, 1): ((0, 0, 1), (0, -1, 1),),
    (0, 1, 1): ((0, 0, 1), (0, 1, 1),),
    (1, 0, 1): ((0, 0, 1), (1, 0, 1),)
}


POSSIBLE_MOVES = tuple(POSSIBLE_MOVES_DICT.keys())
POSSIBLE_MOVES_VECTORS = tuple(map(Vector, POSSIBLE_MOVES))


def is_air(voxel):
    return voxel and voxel.val == 0 and not voxel.NPC


def is_solid(voxel):
    return voxel and voxel.val != 0


def is_npc(voxel):
    return voxel and voxel.NPC


class PathMaster:
    def __init__(self, path, success=True):
        self.path = path
        self.success = success

    def valid(self):
        return bool(self.path)


class PathObject:
    PATH_SUCCESS = 0
    PATH_WAIT = 1
    PATH_FAIL = 2

    def __init__(self, pos, destructible):
        self.pos = pos
        self.work = None
        self.destructible = destructible

    def __str__(self):
        return str(self.pos)

    def assign(self, worker):
        self.work = self.complete(worker)

    def tick(self):
        return next(self.work)

    def complete(self, worker):
        yield PathObject.PATH_WAIT
        while True:
            if worker.energy > 0.3:
                if self.destructible:
                    delta = floored_tuple(Vector(self.pos) - Vector(worker.pos))
                    if not delta in POSSIBLE_MOVES_DICT:
                        yield PathObject.PATH_FAIL

                    for dv in POSSIBLE_MOVES_DICT[delta]:
                        check_pos = Vector(worker.pos) + Vector(dv)
                        voxel = logic.chunks.quick_voxel(check_pos)
                        if is_solid(voxel):
                            logic.work.append(RemoveWork(check_pos, 0))
                            for i in range(20):
                                if voxel.val != 0:
                                    yield PathObject.PATH_WAIT
                                else:
                                    break

                valid_move = worker.relative_move(Vector(self.pos))
                if valid_move:
                    worker.walk_expend()
                    yield PathObject.PATH_SUCCESS
                    break
                else:
                    if DEBUG_NORMAL():
                        print("PathObject: path has changed")
                    voxel = logic.chunks.quick_voxel(self.pos)
                    if is_npc(voxel):
                        for i in range(20):
                            if is_npc(voxel):
                                yield PathObject.PATH_WAIT
                            else:
                                if DEBUG_NORMAL():
                                    print("PathObject: path recovered")
                                for i in range(4):
                                    yield PathObject.PATH_WAIT
                                break
                        else:
                            if DEBUG_NORMAL():
                                print("PathObject: path timed out")
                            yield PathObject.PATH_FAIL
                        continue
                    yield PathObject.PATH_FAIL
            yield PathObject.PATH_WAIT


class PathManager:
    def __init__(self):
        self.tasks = deque([])
        self.task = None

    def append(self, path_generator):
        self.tasks.append(path_generator)

    def tick(self):
        if not self.task:
            if not self.tasks:
                return
            path_to_be_worked = self.tasks.popleft()
            self.task = path_to_be_worked.solve()

        if not next(self.task):
            self.task = None


class BestOf(object):
    def __init__(self):
        self.item = None
        self.value = None

    def check(self, value, item):
        if self.value is None or self.value >= value:
            self.item, self.value = item, value


class RandomOf(BestOf):
    def check(self, value, item):
        if self.value is None or self.value * random() > value:
            self.item, self.value = item, value


class SimplePathGenerator:
    BEST_COMPARATOR = BestOf

    def __init__(self, start, end, client, search_limit=100, time_factor=0.005, enable_visual=True, destructive=True):
        self.start = tuple(start)
        self.end = tuple(end) if not isinstance(end, type) else end
        self.client = client
        self.search_limit = search_limit
        self.time_factor = time_factor
        self.enable_visual = enable_visual
        self.destructive = destructive

    @staticmethod
    def visual(pos, color, time, scale=(1, 1, 1)):
        voxel = logic.chunks.quick_voxel(pos)
        if voxel:
            trace, last = voxel.trace
            obj = scene.addObject("PathCube", "sun", time)
            obj.orientation = 0, 0, 0
            obj.worldScale = scale
            obj.worldPosition = pos
            obj.color = 1 - trace / 100, color[1] * trace / 100, color[2], color[3]

    def back_track(self, node_key, cost_map, success=True):
        if not node_key:
            if DEBUG_NORMAL():
                print('no node_key')
            return PathMaster(None)

        path = [PathObject(node_key, self.destructive)]
        _, parent = cost_map[node_key]
        while parent is not None:
            if DEBUG_NORMAL():
                self.visual(parent, (0, 0, 0, 0.3), 80)
            path.append(PathObject(parent, self.destructive))
            _, parent = cost_map[parent]
            if len(path) > 1000:
                if DEBUG_NORMAL():
                    print("\n\nI have a bad case of diarrhea\n\n")
                break
        return PathMaster(path[:-1], success=success)

    def heur(self, new_x, new_y, new_z):
        end_x, end_y, end_z = self.end
        return abs(end_x - new_x) + abs(end_y - new_y) + abs(end_z - new_z)

    def solve(self):
        time_start = time()
        tick_start = time()

        current_best = self.BEST_COMPARATOR()
        heuristic = self.heur
        possible_moves = POSSIBLE_MOVES_DICT.items()
        chunks_manager = logic.chunks

        start, client, destructive = self.start, self.client, self.destructive

        walk_queue = [(0, 1, 0, heuristic(*start), start, None, set())]
        dig_queue = []
        cost_map = {}
        blasted_dict = {None: set()}

        counter_discovered = 0
        debug = DEBUG_HEAVY()

        while (walk_queue or dig_queue) and counter_discovered < self.search_limit:
            # resting interval
            if time() - tick_start > self.time_factor:
                yield True
                tick_start = time()

            queue = dig_queue if not counter_discovered % 4 and dig_queue else (walk_queue or dig_queue)
            current_score, current_cost, current_destruction, current_heur, node_key, parent, to_be_removed = heappop(queue)

            # search end criteria
            if not current_heur:
                cost_map[node_key] = current_cost, parent
                client.path = self.back_track(node_key, cost_map)
                break

            # has already been discovered?
            if current_destruction and node_key in cost_map:
                continue

            old_cost = cost_map.get(node_key, (999090999090,))[0]
            if old_cost <= current_cost:
                continue

            current_blasted = blasted_dict[parent] | to_be_removed
            blasted_dict[node_key] = current_blasted

            cost_map[node_key] = current_cost, parent

            # at least remember this
            current_best.check(current_heur ** 2 / current_cost, parent)

            # search flood visual
            if self.enable_visual and debug:
                self.visual(node_key, (0.1, 1, 0.1, 0.6), 25)

            counter_discovered += 1

            node_x, node_y, node_z = node_key
            for delta_vector, airspace in possible_moves:

                new_x, new_y, new_z = node_x + delta_vector[0], node_y + delta_vector[1], node_z + delta_vector[2]
                new_pos = new_x, new_y, new_z
                if current_destruction and new_pos in cost_map and random() < 0.9:
                    continue

                new_ground_pos = new_x, new_y, new_z - 1
                if new_ground_pos in current_blasted:
                    continue

                ground = chunks_manager.quick_voxel(new_ground_pos)
                if not is_solid(ground):
                    continue

                rem_list = set()
                D = current_destruction
                N = 0

                for delta_air_x, delta_air_y, delta_air_z in airspace:
                    new_air_pos = (
                        node_x + delta_air_x,
                        node_y + delta_air_y,
                        node_z + delta_air_z,
                    )
                    current_voxel = chunks_manager.quick_voxel(new_air_pos)
                    if is_npc(current_voxel):
                        N += 5

                    if not destructive:
                        # not air?
                        if is_solid(current_voxel):
                            break
                    elif is_solid(current_voxel) and new_air_pos not in current_blasted:
                        rem_list.add(new_air_pos)
                        D += 2
                else:
                    H = heuristic(new_x, new_y, new_z)
                    if H:
                        H += N

                    G = current_cost + 1 + N
                    F = G + H + D

                    if cost_map.get(new_pos, (999090999090,))[0] > G:
                        queue = dig_queue if D else walk_queue
                        heappush(queue, (F, G, D, H, new_pos, node_key, rem_list))

        else:
            client.path = self.back_track(current_best.item, cost_map, success=False)
        if DEBUG_NORMAL():
            print("Path generated, size {}".format(len(client.path.path or []) - 1), "\n", time() - time_start,
                  "path time", counter_discovered)
        yield False


class NearestTargetPathGenerator(SimplePathGenerator):
    BEST_COMPARATOR = RandomOf

    def __init__(self, start, end, client, search_limit=100, time_factor=0.005, enable_visual=True, destructive=False):
        super().__init__(start, end, client, search_limit, time_factor, enable_visual, destructive)
        start_x, start_y, start_z = self.start
        new_x, new_y, new_z = [randint(-search_limit * 3, search_limit * 3) for _ in range(3)]
        self.random_target = start_x - new_x, start_y - new_y, start_z - new_z

    def heur(self, new_x, new_y, new_z):
        end = self.end
        current = new_x, new_y, new_z
        voxel = logic.chunks.quick_voxel(current)

        if voxel.NPC and isinstance(voxel.NPC, end):
            return 0

        trace, caster = voxel.trace
        if caster and not issubclass(caster, end):
            trace = 120

        target_x, target_y, target_z = self.random_target
        return (abs(target_x - new_x) + abs(target_y - new_y) + abs(target_z - new_z)) / 4 + trace / 7
