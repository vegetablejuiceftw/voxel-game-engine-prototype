from bge import logic
from mathutils import Vector
from time import time
from random import random, randint
from heapq import *
from collections import deque

from work import RemoveWork
from chunk import floored_tuple

scene = logic.getCurrentScene()

# POSSIBLE_MOVES = [  (-1, -1, 0), (-1, 0, 0), (-1, 1, 0), (0, -1, 0), (0, 1, 0), (1, -1, 0), (1, 0, 0), (1, 1, 0), 
#             (-1, 0, -1), (0, -1, -1), (0, 1, -1), (1, 0, -1), 
#             (-1, 0, 1), (0, -1, 1), (0, 1, 1), (1, 0, 1)]

POSSIBLE_MOVES_DICT = {
    (-1, -1, 0): ((0, -1, 0), (-1, 0, 0), (-1, -1, 0)),
    (-1, 0, 0): ((-1, 0, 0),),
    (-1, 1, 0): ((0, 1, 0), (-1, 0, 0), (-1, 1, 0)),
    (0, -1, 0): ((0, -1, 0),),
    (0, 1, 0): ((0, 1, 0),),
    (1, -1, 0): ((0, -1, 0), (1, 0, 0), (1, -1, 0)),
    (1, 0, 0): ((1, 0, 0),),
    (1, 1, 0): ((0, 1, 0), (1, 0, 0), (1, 1, 0)),

    (-1, 0, -1): ((-1, 0, 0), (-1, 0, -1),),
    (0, -1, -1): ((0, -1, 0), (0, -1, -1),),
    (0, 1, -1): ((0, 1, 0), (0, 1, -1),),
    (1, 0, -1): ((1, 0, 0), (1, 0, -1),),
    (-1, 0, 1): ((0, 0, 1), (-1, 0, 1),),
    (0, -1, 1): ((0, 0, 1), (0, -1, 1),),
    (0, 1, 1): ((0, 0, 1), (0, 1, 1),),
    (1, 0, 1): ((0, 0, 1), (1, 0, 1),)
}

POSSIBLE_MOVES = list(POSSIBLE_MOVES_DICT.keys())


def is_air(voxel):
    return voxel and voxel.val == 0 and not voxel.NPC


def is_solid(voxel):
    return bool(voxel and voxel.val != 0)


def is_npc(voxel):
    return voxel and voxel.NPC


class PathMaster:
    def __init__(self, path, success=True):
        self.path = path
        self._success = success

    def valid(self):
        return bool(self.path)

    @property
    def success(self):
        return self._success


class PathObject(object):
    PATH_SUCCESS = 0
    PATH_WAIT = 1
    PATH_FAIL = 2

    def __init__(self, pos):
        super(PathObject, self).__init__()
        self.pos = pos
        self.work = None

    def assign(self, worker):
        self.work = self.complete(worker)

    def tick(self):
        state = next(self.work)
        return state

    def complete(self, worker):
        yield PathObject.PATH_WAIT
        while True:
            if worker.energy > 0.01:
                valid_move = worker.relative_move(Vector(self.pos))
                if valid_move:
                    worker.walk_and_expend()
                    yield PathObject.PATH_SUCCESS
                    break
                else:
                    yield PathObject.PATH_FAIL
            yield PathObject.PATH_WAIT


class DestructivePathObject(PathObject):
    def __str__(self):
        return str(self.pos)

    def complete(self, worker):
        yield PathObject.PATH_WAIT

        while True:
            if worker.energy > 0.3:
                delta = floored_tuple(Vector(self.pos) - Vector(worker.pos))
                if not delta in POSSIBLE_MOVES_DICT:
                    yield PathObject.PATH_FAIL

                for dv in POSSIBLE_MOVES_DICT[delta]:
                    check_pos = Vector(worker.pos) + Vector(dv)
                    chunk, voxel = logic.chunks.raycast(check_pos)
                    if is_solid(voxel):
                        logic.work.append(RemoveWork(check_pos, 0))
                        for i in range(20):
                            if voxel.val != 0:
                                yield PathObject.PATH_WAIT
                            else:
                                break

                valid_move = worker.relative_move(Vector(self.pos))
                if valid_move:
                    worker.energy -= 0.3
                    yield PathObject.PATH_SUCCESS
                    break
                else:
                    print("BROKE")
                    yield PathObject.PATH_FAIL
            yield PathObject.PATH_WAIT


class PathManager:
    def __init__(self):
        self.tasks = deque([])
        self.work = self.solve_paths()

    def append(self, path_generator):
        self.tasks.append(path_generator)

    def solve_paths(self):
        while True:
            if not self.tasks:
                yield True
                continue
            path_to_be_worked = self.tasks.popleft()
            path_generator = path_to_be_worked.solve()
            while next(path_generator):
                yield False

    def tick(self, limit=0.005):
        # TODO: move time management into task
        start = time()
        while time() - start < limit:
            free = next(self.work)
            if free:
                return


class BestOf(object):
    def __init__(self):
        self.item = None
        self.value = None

    def check(self, value, item):
        if self.value is None or self.value >= value:
            self.item, self.value = item, value


class RandomOf(BestOf):
    def check(self, value, item):
        if self.value is None or random() > 0.99:
            self.item, self.value = item, value


class PathGenerator:
    BEST_COMPARATOR = BestOf

    def __init__(self, start, end, client, search_limit=400):
        self.start = start
        self.end = end
        self.client = client
        self.search_limit = search_limit

    @staticmethod
    def visual(pos, color, time, scale=(1, 1, 1)):
        return
        _, voxel = logic.chunks.raycast(pos)
        if voxel:
            trace, last = voxel.trace
            obj = scene.addObject("PathCube", "sun", time)
            obj.orientation = 0, 0, 0
            obj.worldScale = scale
            obj.worldPosition = pos
            obj.color = 1 - trace / 40, color[1] * trace / 40, color[2], color[3]

    @staticmethod
    def dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])

    def back_track(self, node_key, cost_map, success=True):

        if not node_key:
            print('really failed')
            return PathMaster(None)

        path = [PathObject(node_key)]
        _, parent = cost_map[node_key]
        while parent is not None:
            if len(path) > 300:
                print("### a path larger than 300")  # TODO lets not generate a path that big to begin with
                break
            path.append(PathObject(parent))
            _, parent = cost_map[parent]

        for node in path:
            self.visual(node.pos, (0, 0, 0, 0.3), 80)

        path.pop(-1)
        return PathMaster(path, success=success)

    def heur(self, current, debug=False):
        return abs(self.end[0] - current[0]) + abs(self.end[1] - current[1]) + abs(self.end[2] - current[2])

    def solve(self):
        start, end, client = self.start, self.end, self.client
        q = [(0, 0, start, None)]
        cost_map = {}

        counter_discovered = 0
        current_best = self.BEST_COMPARATOR()

        while q and counter_discovered < self.search_limit:
            # resting interval
            if not counter_discovered % 15:
                yield True

            current_cost, current_g, node_key, parent = heappop(q)

            # search end criteria
            heur = self.heur(node_key)
            if heur <= 1:
                cost_map[node_key] = (current_cost, parent)
                client.path = self.back_track(node_key, cost_map)
                break

            # has already been discovered?
            old_cost = cost_map.get(node_key, (999090999090,))[0]
            if old_cost <= current_cost:
                continue

            cost_map[node_key] = (current_cost, parent)
            current_best.check(heur, parent)

            # search flood visual
            self.visual(node_key, (0.1, 1, 0.1, 0.6), 60)

            counter_discovered += 1

            for delta_vector, airspace in POSSIBLE_MOVES_DICT.items():

                new_pos = (node_key[0] + delta_vector[0], node_key[1] + delta_vector[1], node_key[2] + delta_vector[2])

                is_valid = False

                H = self.heur(new_pos)
                if H == 0:
                    is_valid = True
                else:
                    for delta_air_vector in airspace:
                        new_air_pos = (
                            node_key[0] + delta_air_vector[0],
                            node_key[1] + delta_air_vector[1],
                            node_key[2] + delta_air_vector[2]
                        )
                        _, voxel = logic.chunks.raycast(new_air_pos)
                        if not is_air(voxel): break
                    else:
                        _, ground = logic.chunks.raycast((new_pos[0], new_pos[1], new_pos[2] - 1))
                        if is_solid(ground):
                            is_valid = True

                if is_valid:
                    G = current_g + 1
                    F = G + H

                    neighbour_cost = cost_map.get(new_pos, (999090999090,))[0]
                    if neighbour_cost <= F:
                        continue

                    heappush(q, (F, G, new_pos, node_key))
        else:
            client.path = self.back_track(current_best.item, cost_map, success=False)
            print("failed path,")
        yield False


class NearestTargetPathGenerator(PathGenerator):
    BEST_COMPARATOR = RandomOf

    def heur(self, current, debug=False):
        voxel = logic.chunks.raycast(current)[1]
        if not voxel:
            return 99999999
        if voxel.NPC and isinstance(voxel.NPC, self.end):
            return 0
        trace, caster = voxel.trace
        if caster and not issubclass(caster, self.end):
            trace = 60
        dist = self.dist(current, self.start)
        if dist < 10:
            dist = 0
        return 10 + dist + randint(0, 1) + trace // 2


class DestructPathGenerator(PathGenerator):
    def back_track(self, node_key, cost_map, success=True):
        if not node_key:
            print('really failed')
            return PathMaster(None)

        path = [DestructivePathObject(node_key)]
        _, parent = cost_map[node_key]
        while parent is not None:
            if len(path) > 300:
                print("### a path larger than 300")
                break
            path.append(DestructivePathObject(parent))
            _, parent = cost_map[parent]

        for node in path:
            self.visual(node.pos, (1, 1, 1, 1), 380, scale=(0.5, 0.5, 0.5))

        path.pop(-1)
        return PathMaster(path, success=success)

    def solve(self):
        start, end, client = self.start, self.end, self.client
        q = [(0, 0, start, None, set())]
        cost_map = {}

        counter_discovered = 0

        current_best = BestOf()

        blasted_dict = {None: set()}

        loop_counter = 1
        while q and counter_discovered < self.search_limit:

            loop_counter += 1
            # resting interval
            if not counter_discovered % 15:
                yield True

            current_cost, current_g, node_key, parent, remove_list = heappop(q)

            # search end criteria
            heur = self.heur(node_key)
            if heur <= 1:
                print('best path', len(q), counter_discovered, loop_counter)
                print('nodecount', len(q) + loop_counter, 'discovered', counter_discovered)
                cost_map[node_key] = (current_cost, parent)
                client.path = self.back_track(node_key, cost_map)
                break

            # has already been discovered?
            if node_key in cost_map:
                continue

            cost_map[node_key] = (current_cost, parent)

            # currently removed blocks
            parent_blasted = blasted_dict[parent]
            current_blasted = set(parent_blasted)
            if remove_list:
                current_blasted |= set(remove_list)
            blasted_dict[node_key] = current_blasted

            current_best.check(heur, parent)

            # search flood visual
            self.visual(node_key, (0.1, 1, 0.1, 0.6), 60)

            counter_discovered += 1

            for delta_vector, airspace in POSSIBLE_MOVES_DICT.items():

                new_pos = (node_key[0] + delta_vector[0], node_key[1] + delta_vector[1], node_key[2] + delta_vector[2])
                if new_pos in cost_map:
                    continue

                new_ground_pos = (new_pos[0], new_pos[1], new_pos[2] - 1)
                if new_ground_pos in current_blasted:
                    continue

                _, ground = logic.chunks.raycast(new_ground_pos)
                if not is_solid(ground):
                    continue

                _, voxel = logic.chunks.raycast(new_pos)
                H = self.heur(new_pos)
                G = current_g + 1

                rem_list = []

                delta_key = (new_pos[0] - node_key[0], new_pos[1] - node_key[1], new_pos[2] - node_key[2])
                for dv in POSSIBLE_MOVES_DICT[delta_key]:
                    check_pos = (node_key[0] + dv[0], node_key[1] + dv[1], node_key[2] + dv[2])
                    _, current_voxel = logic.chunks.raycast(check_pos)

                    if is_solid(current_voxel) and not check_pos in current_blasted:
                        rem_list.append(check_pos)
                        G += 2

                F = G + H
                heappush(q, (F, G, new_pos, node_key, rem_list))

        else:
            print('best effort path', len(q), counter_discovered, loop_counter)
            client.path = self.back_track(current_best.item, cost_map, success=False)

        yield False


class DestructMemoryPathGenerator(PathGenerator):
    def back_track(self, currentIndex, parentChain, success=True):
        if not currentIndex:
            print('really failed')
            return PathMaster(None)

        path = []
        while currentIndex != None:
            node, currentIndex = parentChain[currentIndex]
            if len(path) > 300:
                print("### a path larger than 300")
            path.append(DestructivePathObject(node))

        for node in path:
            self.visual(node.pos, (1, 1, 1, 1), 380, scale=(0.5, 0.5, 0.5))

        path.pop(-1)
        return PathMaster(path, success=success)

    def solve(self):

        start, end, client = self.start, self.end, self.client
        q = [(0, 0, start, None, 0)]
        cost_map = {}

        counter_discovered = 0

        current_best = BestOf()

        blast_map = [[]]
        parentChain = []

        loop_counter = 1
        while q and counter_discovered < self.search_limit:

            loop_counter += 1

            # resting interval
            if not counter_discovered % 15:
                yield True

            current_cost, current_g, node_key, parentChainIndex, remove_listIndex = heappop(q)
            remove_list = blast_map[remove_listIndex]

            # search end criteria
            heur = self.heur(node_key)
            if heur <= 1:
                print('best path', len(q), counter_discovered, loop_counter)
                print('nodecount', len(q) + loop_counter, 'discovered', counter_discovered)
                parentChain.append((node_key, parentChainIndex))
                print('parentChainSize', len(parentChain))
                client.path = self.back_track(len(parentChain) - 1, parentChain)
                break

            cost_map_key = (node_key, tuple(remove_list))

            # has already been discovered?
            old_cost = cost_map.get(cost_map_key, 999090999090)
            if old_cost <= current_cost:
                continue
            cost_map[cost_map_key] = current_cost

            parentChain.append((node_key, parentChainIndex))
            node_chain_index = len(parentChain) - 1

            # atleast remember this
            current_best.check(heur, node_chain_index)

            # search flood visual
            self.visual(node_key, (0.1, 1, 0.1, 0.6), 60)

            counter_discovered += 1

            for delta_vector, airspace in POSSIBLE_MOVES_DICT.items():

                new_pos = (node_key[0] + delta_vector[0], node_key[1] + delta_vector[1], node_key[2] + delta_vector[2])
                if new_pos in cost_map:
                    continue

                new_ground_pos = (new_pos[0], new_pos[1], new_pos[2] - 1)
                if new_ground_pos in remove_list:
                    continue

                _, ground = logic.chunks.raycast(new_ground_pos)
                if not is_solid(ground):
                    continue

                _, voxel = logic.chunks.raycast(new_pos)
                H = self.heur(new_pos)

                G = current_g + 1

                rem_list = list(remove_list)

                delta_key = (new_pos[0] - node_key[0], new_pos[1] - node_key[1], new_pos[2] - node_key[2])
                for dv in POSSIBLE_MOVES_DICT[delta_key]:
                    check_pos = (node_key[0] + dv[0], node_key[1] + dv[1], node_key[2] + dv[2])
                    _, current_voxel = logic.chunks.raycast(check_pos)

                    if is_solid(current_voxel) and not check_pos in remove_list:
                        rem_list.append(check_pos)
                        G += 2

                new_remove_list_index = len(blast_map)
                blast_map.append(rem_list)

                F = G + H
                heappush(q, (F, G, new_pos, node_chain_index, new_remove_list_index))

        else:
            print('best effort path', len(q), counter_discovered, loop_counter)
            client.path = self.back_track(current_best.item, parentChain, success=False)
        yield False


class HybridPathGenerator(PathGenerator):
    SPLIT_RATIO = 0.2

    def back_track(self, node_key, cost_map, success=True):

        if not node_key:
            print('really failed')
            return PathMaster(None)

        path = [DestructivePathObject(node_key)]
        _, parent = cost_map[node_key]
        while parent is not None:
            if len(path) > 300:
                print("### a path larger than 300")
                break
            path.append(DestructivePathObject(parent))
            _, parent = cost_map[parent]

        for node in path:
            self.visual(node.pos, (1, 1, 1, 1), 380, scale=(0.5, 0.5, 0.5))

        path.pop(-1)
        return PathMaster(path, success=success)

    def solve(self):

        start, end, client = self.start, self.end, self.client
        q = [(0, 0, start, None)]
        cost_map = {}

        counter_discovered = 0

        current_best = BestOf()

        blocked_nodes = []

        loop_counter = 1
        while q and counter_discovered < self.search_limit * self.SPLIT_RATIO:
            loop_counter += 1
            # resting interval
            if not counter_discovered % 15:
                yield True

            current_cost, current_g, node_key, parent = heappop(q)

            # search end criteria
            heur = self.heur(node_key)
            if heur <= 1:
                print('hybrid stage 1 resuls', len(q), counter_discovered, loop_counter)
                print('nodecount', len(q) + loop_counter, 'discovered', counter_discovered)
                cost_map[node_key] = (current_cost, parent)
                client.path = self.back_track(node_key, cost_map)
                yield False
                return

            # has already been discovered?
            old_cost = cost_map.get(node_key, (999090999090,))[0]
            if old_cost <= current_cost:
                continue

            cost_map[node_key] = (current_cost, parent)
            # at least remember this
            current_best.check(heur, parent)

            # search flood visual
            self.visual(node_key, (0.1, 1, 0.1, 0.6), 60)

            counter_discovered += 1

            for delta_vector, airspace in POSSIBLE_MOVES_DICT.items():

                new_pos = (node_key[0] + delta_vector[0], node_key[1] + delta_vector[1], node_key[2] + delta_vector[2])

                is_valid = False

                H = self.heur(new_pos)
                if H == 0:
                    is_valid = True
                else:
                    for delta_air_vector in airspace:
                        new_air_pos = (
                            node_key[0] + delta_air_vector[0],
                            node_key[1] + delta_air_vector[1],
                            node_key[2] + delta_air_vector[2]
                        )
                        _, voxel = logic.chunks.raycast(new_air_pos)
                        if not is_air(voxel):
                            break
                    else:
                        _, ground = logic.chunks.raycast((new_pos[0], new_pos[1], new_pos[2] - 1))
                        if is_solid(ground):
                            is_valid = True
                G = current_g + 1
                F = G + H
                if is_valid:
                    neighbour_cost = cost_map.get(new_pos, (999090999090,))[0]
                    if neighbour_cost <= F:
                        continue
                    heappush(q, (F, G, new_pos, node_key))
                else:
                    blocked_nodes.append((F, G, new_pos, node_key))

        # else try option two
        print(loop_counter, 'mid stage', len(q), counter_discovered, 'blockedListSize', len(blocked_nodes))
        print('mid_nodecount', len(q) + loop_counter, 'discovered', counter_discovered)

        blasted_dict = {None: set()}

        # re-activate blocked nodes
        for i, blockedNode in enumerate(blocked_nodes):
            if not i % 100:
                yield True

            F, G, new_pos, node_key = blockedNode

            blasted_dict[node_key] = set()

            delta_key = (new_pos[0] - node_key[0], new_pos[1] - node_key[1], new_pos[2] - node_key[2])
            airspace = POSSIBLE_MOVES_DICT[delta_key]

            new_ground_pos = (new_pos[0], new_pos[1], new_pos[2] - 1)

            _, ground = logic.chunks.raycast(new_ground_pos)
            if not is_solid(ground):
                continue

            H = self.heur(new_pos)
            G = current_g + 1

            rem_list = []
            for dv in airspace:
                check_pos = (node_key[0] + dv[0], node_key[1] + dv[1], node_key[2] + dv[2])
                _, current_voxel = logic.chunks.raycast(check_pos)

                if is_solid(current_voxel):
                    rem_list.append(check_pos)
                    G += 2

            F = G + H
            heappush(q, (F, G, new_pos, node_key, rem_list))

        while q and counter_discovered < self.search_limit:
            loop_counter += 1

            # resting interval
            if not counter_discovered % 15:
                yield True

            current = heappop(q)
            remove_list = None
            if len(current) == 5:
                current_cost, current_g, node_key, parent, remove_list = current
            else:
                current_cost, current_g, node_key, parent = current

            # search end criteria
            heur = self.heur(node_key)
            if heur <= 1:
                print(loop_counter, 'stage two path', len(q), counter_discovered)
                print('nodecount', len(q) + loop_counter, 'discovered', counter_discovered)
                cost_map[node_key] = (current_cost, parent)
                client.path = self.back_track(node_key, cost_map)
                yield False
                return

            # has already been discovered?
            if node_key in cost_map:
                continue

            cost_map[node_key] = (current_cost, parent)

            # currently removed blocks
            parent_blasted = blasted_dict[parent]
            current_blasted = set(parent_blasted)
            if remove_list:
                current_blasted |= set(remove_list)
            blasted_dict[node_key] = current_blasted

            current_best.check(heur, parent)

            # search flood visual
            self.visual(node_key, (0.1, 1, 0.1, 0.6), 60)

            counter_discovered += 1

            for delta_vector, airspace in POSSIBLE_MOVES_DICT.items():

                new_pos = (node_key[0] + delta_vector[0], node_key[1] + delta_vector[1], node_key[2] + delta_vector[2])
                if new_pos in cost_map:
                    continue

                new_ground_pos = (new_pos[0], new_pos[1], new_pos[2] - 1)
                if new_ground_pos in current_blasted:
                    continue

                _, ground = logic.chunks.raycast(new_ground_pos)
                if not is_solid(ground):
                    continue

                H = self.heur(new_pos)
                G = current_g + 1

                rem_list = []

                delta_key = (new_pos[0] - node_key[0], new_pos[1] - node_key[1], new_pos[2] - node_key[2])
                for dv in POSSIBLE_MOVES_DICT[delta_key]:
                    check_pos = (node_key[0] + dv[0], node_key[1] + dv[1], node_key[2] + dv[2])
                    _, current_voxel = logic.chunks.raycast(check_pos)

                    if is_solid(current_voxel) and check_pos not in current_blasted:
                        rem_list.append(check_pos)
                        G += 2

                F = G + H
                heappush(q, (F, G, new_pos, node_key, rem_list))

        print('best effort path', len(q), counter_discovered, loop_counter)
        client.path = self.back_track(current_best.item, cost_map, success=False)
        yield False


class SimplePathGenerator:
    BEST_COMPARATOR = BestOf

    def __init__(self, start, end, client, search_limit=100, time_factor=0.005, enable_visual=False):
        self.start = tuple(start)
        self.end = tuple(end)
        self.client = client
        self.search_limit = search_limit
        self.time_factor = time_factor
        self.enable_visual = enable_visual or True

    @staticmethod
    def visual(pos, color, time, scale=(1, 1, 1)):
        voxel = logic.chunks.quick_voxel(pos)
        if voxel:
            trace, last = voxel.trace
            obj = scene.addObject("PathCube", "sun", time)
            obj.orientation = 0, 0, 0
            obj.worldScale = scale
            obj.worldPosition = pos
            obj.color = 1 - trace / 40, color[1] * trace / 40, color[2], color[3]

    def back_track(self, node_key, cost_map, success=True):
        if not node_key:
            print('no node_key')
            return PathMaster(None)

        path = [PathObject(node_key)]
        _, parent = cost_map[node_key]
        while parent is not None:
            self.visual(parent, (0, 0, 0, 0.3), 80)
            path.append(PathObject(parent))
            _, parent = cost_map[parent]

        print("Path generated, size {}".format(len(path) - 1))
        return PathMaster(path[:-1], success=success)

    def solve(self):
        time_start = time()

        current_best = self.BEST_COMPARATOR()
        possible_moves = POSSIBLE_MOVES_DICT.items()
        chunks_manager = logic.chunks

        start, end, client = self.start, self.end, self.client
        end_x, end_y, end_z = end

        walk_queue = [(0, 0, 0, -1, start, None, [])]
        dig_queue = []
        cost_map = {}

        counter_discovered = 0
        tick_start = time()
        while walk_queue and counter_discovered < self.search_limit:
            # resting interval
            if time() - tick_start > self.time_factor:
                yield True
                tick_start = time()

            current_score, current_cost, current_destruction, current_heur, node_key, parent, to_be_removed = heappop(walk_queue)

            # search end criteria
            # if not current_heur:
            #     cost_map[node_key] = current_score, parent
            #     client.path = self.back_track(node_key, cost_map)
            #     break

            # has already been discovered?
            old_cost = cost_map.get(node_key, (999090999090,))[0]
            if old_cost <= current_score:
                continue

            cost_map[node_key] = current_score, parent
            # at least remember this
            current_best.check(current_heur, parent)

            # search flood visual
            # if self.enable_visual:
            #     self.visual(node_key, (0.1, 1, 0.1, 0.6), 60)

            counter_discovered += 1

            node_x, node_y, node_z = node_key
            for delta_vector, airspace in possible_moves:
                new_x, new_y, new_z = node_x + delta_vector[0], node_y + delta_vector[1], node_z + delta_vector[2]

                ground = chunks_manager.quick_voxel((new_x, new_y, new_z - 1))
                if not is_solid(ground):
                    continue

                for delta_air_x, delta_air_y, delta_air_z in airspace:
                    new_air_pos = (
                        node_x + delta_air_x,
                        node_y + delta_air_y,
                        node_z + delta_air_z
                    )
                    if not is_air(chunks_manager.quick_voxel(new_air_pos)):
                        break
                else:
                    H = abs(end_x - new_x) + abs(end_y - new_y) + abs(end_z - new_z)
                    G = current_cost + 1
                    F = G + H
                    new_pos = new_x, new_y, new_z
                    if cost_map.get(new_pos, (999090999090,))[0] > F:
                        heappush(walk_queue, (F, G, 0, H, new_pos, node_key, []))

        else:
            client.path = self.back_track(current_best.item, cost_map, success=False)
            print("failed path")
        print(time() - time_start, "path time", counter_discovered)

        yield False
