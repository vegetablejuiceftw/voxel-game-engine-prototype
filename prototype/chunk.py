from random import randint
from math import floor
from collections import Counter
from bge import logic

from perlin import Noise

MAP_SIZE = 4
CHUNK_SEED = "Cupcakes1"
CHUNK_SIZE = 16
CHUNK_AREA = CHUNK_SIZE ** 2
CHUNK_VOLUME = CHUNK_SIZE ** 3

IGNORE_BLOCK = -99999
# up down left right front back
VOXEL_MAP = {-1: [-1, -1, -1, -1, -1, -1],
             0: [0, 0, 0, 0, 0, 0],
             1: [2, 2, 2, 2, 2, 2],
             2: [1, 2, 2, 2, 2, 2],
             3: [3, 3, 3, 3, 3, 3],
             4: [4, 4, 4, 4, 4, 4],
             5: [5, 5, 5, 5, 5, 5],
             }
GREEN = (0, 0.8, 0, 1)
DARK_GREEN = (0, 0.3, 0, 1)
BROWN = (0.6, 0.3, 0.0, 1)
GRAY = (0.3, 0.3, 0.3, 1)
DARK_BROWN = (0.3, 0.1, 0.0, 1)

COLORS = [None, GREEN, BROWN, GRAY, DARK_BROWN, DARK_GREEN]


def tuple_to_index(local_position):
    x, y, z = local_position
    return x + y * CHUNK_SIZE + z * CHUNK_AREA


def tuple_to_chunk_key(global_position):
    return tuple(floor(i / CHUNK_SIZE) * CHUNK_SIZE for i in global_position)


def floored_tuple(position):
    return tuple(floor(i) for i in position)


class Voxel:
    def __init__(self, val):
        self.val = val
        self._NPC = None
        self._trace = 0
        self._last = None

    @property
    def NPC(self):
        return self._NPC

    @NPC.setter
    def NPC(self, npc):
        self._NPC = npc
        if npc:
            self._last = npc.__class__
        self._trace = logic.epoch

    @property
    def trace(self):
        if not self._last:
            return 100, None
        trace = min(logic.epoch - self._trace, 100)
        if trace == 100:
            self._last = None
        return trace, self._last

    def __str__(self):
        return str(self.val)

    def __lt__(self, other):
        return self.val < other.val

    def __le__(self, other):
        return self.val <= other.val

    def __ge__(self, other):
        return self.val >= other.val

    def __gt__(self, other):
        return self.val > other.val


class VoxelPlane:
    def __init__(self, plane, axis):
        self.map = plane
        self.axis = axis * 2

    def __getitem__(self, i):
        val_A, val_B = self.map[i]
        A = B = 0

        if val_A:
            A = VOXEL_MAP[val_A.val][self.axis]
        if val_B:
            B = VOXEL_MAP[val_B.val][self.axis + 1]

        if A != 0 and B != 0:
            return IGNORE_BLOCK
        return B or A

    def __len__(self):
        return len(self.map)


class VoxelMap:
    def __init__(self, val, size):
        self.map = [Voxel(val) for _ in range(size)]
        self.planes = []
        self.plane_mapper()

    def get(self, i):
        return self.map[i]

    def __getitem__(self, i):
        return self.map[i].val

    def __setitem__(self, key, value):
        self.map[key].val = value

    def __len__(self):
        return len(self.map)

    def plane_mapper(self):
        for plane_dir in range(3):
            self.planes.append([])
            for plane_index in range(CHUNK_SIZE + 1):
                plane = [None] * CHUNK_AREA
                for rX in range(CHUNK_SIZE):
                    for rY in range(CHUNK_SIZE):
                        local_A = local_B = (0, 0, 0)
                        if plane_dir == 0:
                            x, y, z = rX, rY, plane_index
                            local_A, local_B = (x, y, z - 1), (x, y, z)

                        if plane_dir == 1:
                            x, y, z = plane_index, rY, rX
                            local_A, local_B = (x - 1, y, z), (x, y, z)

                        if plane_dir == 2:
                            x, y, z = rX, plane_index, rY
                            local_A, local_B = (x, y - 1, z), (x, y, z)

                        down, up = None, None
                        if plane_index != 0:
                            down = self.map[tuple_to_index(local_A)]
                        if plane_index != CHUNK_SIZE:
                            up = self.map[tuple_to_index(local_B)]

                        plane[rX + rY * CHUNK_SIZE] = (down, up)

                self.planes[-1].append(VoxelPlane(plane, plane_dir))


class ChunkManager:
    FACE_COUNTS = Counter()

    def __init__(self, obj_builder, draw_builder):
        self._map = dict()
        self._phantoms = dict()
        self.obj_builder = obj_builder
        self.draw_builder = draw_builder

    def __getitem__(self, key):
        key = tuple_to_chunk_key(key)
        chunk = self._map.get(key)
        return chunk or self.init_chunk(key)

    def get(self, key):
        key = tuple_to_chunk_key(key)
        if key[2] > CHUNK_SIZE:
            return self._map.get(key)
        return self[key]

    def init_chunk(self, key):
        if key in self._map:
            chunk = self._map[key]
        else:
            if key in self._phantoms:
                chunk = self._phantoms.pop(key)
            else:
                chunk = Chunk(*key, gen_faces=False)

            self._map[key] = chunk
            chunk.generate_faces()
            chunk.obj = self.obj_builder(chunk.face_count, key)
            self.draw_builder(chunk, chunk.faces)
        return chunk

    def update(self, key, gen_faces=True, update_neighbours=False):
        key = tuple_to_chunk_key(key)
        if key in self._map:
            chunk = self.init_chunk(key)
            if gen_faces:
                chunk.generate_faces()
            self.draw_builder(chunk, chunk.faces)

        x, y, z = key
        delta = CHUNK_SIZE
        touched_chunks = [
            (x + delta, y, z), (x - delta, y, z), (x, y + delta, z),
            (x, y - delta, z), (x, y, z + delta), (x, y, z - delta),
        ]

        if update_neighbours:
            for chunk_key in touched_chunks:
                self.update(chunk_key)

        touched_chunks = [key for key in touched_chunks if key not in self._map]
        return touched_chunks

    def raycast(self, position):
        position = floored_tuple(position)
        chunk_key = tuple_to_chunk_key(position)

        if chunk_key in self._map:
            chunk = self.init_chunk(chunk_key)
            local_pos = position[0] - chunk_key[0], position[1] - chunk_key[1], position[2] - chunk_key[2]

            voxel_index = tuple_to_index(local_pos)
            return chunk, chunk.voxels.get(voxel_index)
        return None, None

    def quick_voxel(self, position):
        position = floored_tuple(position)
        chunk_key = tuple_to_chunk_key(position)
        if chunk_key not in self._map:
            return
        chunk = self._map[chunk_key]
        local_pos = position[0] - chunk_key[0], position[1] - chunk_key[1], position[2] - chunk_key[2]
        voxel_index = tuple_to_index(local_pos)
        return chunk.voxels.get(voxel_index)


class Chunk:
    MAP_FUNCTION = Noise(16, CHUNK_SEED)

    def __init__(self, x, y, z, obj=None, gen_faces=True):
        self.x = x
        self.y = y
        self.z = z
        self.pos = (x, y, z)
        self.voxels = VoxelMap(0, CHUNK_VOLUME)
        self.faces = []
        self.obj = obj

        self.fill_voxels()
        if gen_faces:
            self.generate_faces()

    def __len__(self):
        return sum(map(bool, self.voxels))

    def get_key(self):
        return floored_tuple(self.pos)

    def fill_voxels(self):
        X, Y, Z = self.pos
        fill_range = range(CHUNK_SIZE)
        get_value = self.MAP_FUNCTION.get_value
        voxels = self.voxels
        tree = X % 16 == 0 and Y % 16 == 0
        for x in fill_range:
            for y in fill_range:
                cZ = get_value(X + x, Y + y)
                for z in fill_range:
                    # tuple_to_index
                    index = tuple_to_index((x, y, z))
                    gZ = Z + z

                    if gZ < cZ:  # below surface
                        voxels[index] = 1

                    elif gZ == cZ:  # surface
                        voxels[index] = 2

                    elif tree and cZ < gZ <= cZ + 3 and x == 1 and y == 1:
                        voxels[index] = 4

                    elif tree and cZ + 3 < gZ < cZ + 6 and x < 3 and y < 3:
                        voxels[index] = 5

                    elif gZ <= cZ + 1 and randint(1, 11) == 1:
                        voxels[index] = 3

    @property
    def face_count(self):
        return len(self.faces)

    @staticmethod
    def index_to_tuple(index):
        z = index // CHUNK_AREA
        index -= z * CHUNK_AREA
        y = index // CHUNK_SIZE
        x = index - y * CHUNK_SIZE
        return x, y, z

    @staticmethod
    def print_plane(plane):
        s = "{} " * CHUNK_SIZE
        for y in range(CHUNK_SIZE):
            row = []
            for x in range(CHUNK_SIZE):
                T = plane[x + y * CHUNK_SIZE]
                row.append(T if T == IGNORE_BLOCK else '.')
            print(s.format(*row))
        print()

    @staticmethod
    def minimize(faces, plane, orientation):
        h_map = [None] * CHUNK_AREA
        visited = set()
        result = [0] * (CHUNK_SIZE * 8)
        count = 0

        for i in range(CHUNK_AREA):
            T = plane[i]

            if i in visited or T <= 0 or T == IGNORE_BLOCK:
                continue

            result[0] = 0
            Chunk.cut(i, plane, visited, result)

            y = i // CHUNK_SIZE
            x = i - y * CHUNK_SIZE

            for k in range(1, result[0] + 1):
                di = result[k]

                cy = di // CHUNK_SIZE
                cx = di - cy * CHUNK_SIZE

                A = [min(x, cx), min(y, cy)]
                B = [max(x, cx) + 1, max(y, cy) + 1]
                size = (B[0] - A[0]) * (B[1] - A[1])
                for dx in range(A[0], B[0]):
                    for dy in range(A[1], B[1]):
                        wipe_index = dx + dy * CHUNK_SIZE
                        visited.add(wipe_index)

                        last = h_map[wipe_index]
                        if not last or last[0] < size:
                            h_map[wipe_index] = (size, T, A[0], A[1], B[0], B[1])
                            count += int(not last)

        visited = set()
        for face in h_map:
            if face and face not in visited:
                visited.add(face)
                T = face[1]
                H = max(orientation)
                A = list(face[2:4]) + [H]
                C = list(face[4:6]) + [H]
                B = [C[0], A[1], H]
                D = [A[0], C[1], H]

                if orientation[2] != -1:  # up-down
                    rotated = (T, A, B, C, D, (0, 0, 1))
                if orientation[0] != -1:  # left-right
                    A = [A[2], A[1], A[0]]
                    B = [B[2], B[1], B[0]]
                    C = [C[2], C[1], C[0]]
                    D = [D[2], D[1], D[0]]
                    rotated = (T, D, C, B, A, (1, 0, 0))

                if orientation[1] != -1:  # back-front
                    A = [A[0], A[2], A[1]]
                    B = [B[0], B[2], B[1]]
                    C = [C[0], C[2], C[1]]
                    D = [D[0], D[2], D[1]]
                    rotated = (T, A, B, C, D, (0, -1, 0))

                faces.append(rotated)

    @staticmethod
    def cut(index, plane, visited, result):
        T = plane[index]
        Y = index // CHUNK_SIZE
        X = index - Y * CHUNK_SIZE

        for dirX in [-1, 1]:
            for dirY in [-1, 1]:

                last_delta = CHUNK_SIZE + 16
                last_size = result[0]
                last_size = last_size

                x = X
                while x != -1 and x != CHUNK_SIZE:

                    if plane[x + Y * CHUNK_SIZE] not in (T, IGNORE_BLOCK) or x + Y * CHUNK_SIZE in visited:
                        break

                    y = Y + dirY
                    while True:
                        di = x + y * CHUNK_SIZE
                        if y in (last_delta, -1, CHUNK_SIZE) or di in visited or plane[di] not in (T, IGNORE_BLOCK):

                            current_index = di - CHUNK_SIZE * dirY
                            if y == last_delta and last_size != last_size:  # // same height
                                result[last_size] = current_index

                            else:
                                result[0] += 1
                                last_size += 1
                                result[last_size] = current_index

                            last_delta = y
                            break
                        y += dirY
                    x += dirX

    def generate_faces_by_index(self, index):
        if index == 0:
            self.faces = []
        plane_dir = index // (CHUNK_SIZE + 1)
        A = index - plane_dir * (CHUNK_SIZE + 1)
        self.generate_faces_by_plane(plane_dir, A)

    def generate_faces_by_plane(self, plane_dir, A):
        plane = self.voxels.planes[plane_dir][A]
        if plane_dir == 0:
            Chunk.minimize(self.faces, plane, (-1, -1, A))
        if plane_dir == 1:
            Chunk.minimize(self.faces, plane, (A, -1, -1))
        if plane_dir == 2:
            Chunk.minimize(self.faces, plane, (-1, A, -1))

    def generate_faces(self):
        self.faces = []
        for A in range(CHUNK_SIZE + 1):
            for plane_dir in range(3):
                self.generate_faces_by_plane(plane_dir, A)
