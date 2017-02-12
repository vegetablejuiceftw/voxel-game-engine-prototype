import os
from time import time
from math import floor, sin
from bge import logic, events
from mathutils import Vector

from work import ChangeWork, RemoveWork
from chunk import ChunkManager, MAP_SIZE, CHUNK_SIZE, COLORS, tuple_to_chunk_key, floored_tuple, tuple_to_index

scene = logic.getCurrentScene()
own = "World_manager"
logic.counter = 0


def init_game():
    # clear console
    os.system("cls")

    start = time()
    logic.chunks = ChunkManager(create_unique_mesh, draw)
    logic.work = []
    face_count = voxel_count = chunk_count = 0

    max_time = 0
    for x in range(-MAP_SIZE, MAP_SIZE + 1):
        for y in range(-MAP_SIZE, MAP_SIZE + 1):
            for z in range(32 // CHUNK_SIZE + 1):
                cX, cY, cZ = x * CHUNK_SIZE, y * CHUNK_SIZE, z * CHUNK_SIZE
                print("chunk being spawned", (cX, cY, cZ))

                t = time()
                c = logic.chunks.init_chunk((cX, cY, cZ))
                max_time = max(time() - t, max_time)

                chunk_faces, chunk_voxels = c.face_count, len(c)
                voxel_count += chunk_voxels
                face_count += chunk_faces
                chunk_count += bool(chunk_voxels)
        print("face_count {}  voxel_count {}".format(face_count, voxel_count))

    print('face_count', face_count, ' voxel_count', voxel_count, ' filled-chunk_count', chunk_count)
    print("FULL time {:.2f} sec, max_time of a chunk {:.2}".format(time() - start, max_time))


def create_unique_mesh(request_size, position):
    obj = scene.addObject("Cube{}".format(CHUNK_SIZE), own)
    obj.worldPosition = position
    obj.replaceMesh(new_mesh(request_size), True)
    return obj


def resize_mesh(obj, request_size):
    obj.replaceMesh(new_mesh(request_size), True)


def new_mesh(request_size):
    sizes = [32, 64, 96, 128, 192, 256, 384, 512, 768]
    size = "Donor{}".format(next(x for x in sizes if x > request_size))
    logic.counter += 1
    pre = logic.LibNew("GEN_{}".format(time()), "Mesh", [size])
    handle = pre[0].name
    return handle


def draw(chunk, faces):
    obj = chunk.obj
    mesh = obj.meshes[0]
    face_count = len(faces)
    current_faces = mesh.numPolygons
    if face_count > current_faces or 16 <= face_count <= current_faces / 2.2:
        resize_mesh(obj, face_count)
        print("draw::resize -> chamge of donor mesh. face counts: {} -> {}".format(face_count, current_faces))
    mesh = obj.meshes[0]

    for index in range(face_count):
        T, A, B, C, D, N = faces[index]
        face = A, B, C, D

        for v_index in range(4):
            vertex = mesh.getVertex(0, index * 4 + v_index)

            vertex.setXYZ(face[v_index])
            if T == 1:
                c = list(COLORS[T])
                c[1] = abs(sin(vertex.z)) * 0.35 + 0.4
                vertex.setRGBA(c)
            else:
                vertex.setRGBA(COLORS[T])
            vertex.setNormal(N)

    for index in range(face_count, mesh.numPolygons):
        for v_index in range(4):
            vertex = mesh.getVertex(0, index * 4 + v_index)
            if vertex.z < -10:
                index = None
                break
            vertex.setXYZ((0, 0, -99))
        if index is None:
            break


def input_events(cont):
    if not cont.sensors['Always'].positive:
        return

    own = cont.owner
    mouse = logic.mouse
    keyboard = logic.keyboard
    JUST_ACTIVATED = logic.KX_INPUT_JUST_ACTIVATED

    move(cont)

    if mouse.events[events.RIGHTMOUSE] == JUST_ACTIVATED:
        build(cont)
    if mouse.events[events.LEFTMOUSE] == JUST_ACTIVATED:
        blast(cont)
    if mouse.events[events.MIDDLEMOUSE] == JUST_ACTIVATED or keyboard.events[events.F12KEY] == JUST_ACTIVATED:
        mark(cont)

    radius = logic.RADIUS or 2
    if mouse.events[events.WHEELUPMOUSE]:
        radius = min(10, logic.RADIUS + 0.10)
    if mouse.events[events.WHEELDOWNMOUSE]:
        radius = max(0, logic.RADIUS - 0.10)
    if logic.RADIUS != radius:
        logic.RADIUS = radius
        logic.BLAST_DELTA = blast_sphere(logic.RADIUS)

    if not own.get('select'):
        own['select'] = 1
    if keyboard.events[events.F1KEY]:
        own['select'] = 1
    if keyboard.events[events.F2KEY]:
        own['select'] = 2
    if keyboard.events[events.F3KEY]:
        own['select'] = 3

    own = cont.owner
    own['radious'] = logic.RADIUS


def move(cont):
    own = cont.owner
    keyboard = logic.keyboard

    SPEED = 0.2
    if keyboard.events[events.LEFTSHIFTKEY]:
        SPEED *= 6
    if keyboard.events[events.WKEY]:
        own.applyMovement((0, 0, -SPEED), True)
    if keyboard.events[events.SKEY]:
        own.applyMovement((0, 0, SPEED), True)
    if keyboard.events[events.AKEY]:
        own.applyMovement((-SPEED, 0, 0), True)
    if keyboard.events[events.DKEY]:
        own.applyMovement((SPEED, 0, 0), True)
    if keyboard.events[events.SPACEKEY]:
        own.applyMovement((0, 0, SPEED), False)


def generate_block_ray(start, vector, distance):
    dx, dy, dz = vector
    start = Vector(start)
    pos = Vector(start)
    positions = []

    while (pos - start).length < distance:
        x, y, z = pos
        x, y, z = x - floor(x), y - floor(y), z - floor(z)

        x = x if dx < 0 else 1 - x
        y = y if dy < 0 else 1 - y
        z = z if dz < 0 else 1 - z

        x += 0.001
        y += 0.001
        z += 0.001

        if dx:
            vx = pos + vector * abs(x / dx)
            positions.append(vx)
        if dy:
            vy = pos + vector * abs(y / dy)
            positions.append(vy)
        if dz:
            vz = pos + vector * abs(z / dz)
            positions.append(vz)
        pos += vector

    positions = sorted(positions, key=lambda current: (start - current).length)

    result = []
    visited = set()
    last = None
    for V in positions:
        new_pos = floor(V[0]), floor(V[1]), floor(V[2])  # TODO
        if new_pos in visited or result and (last - Vector(new_pos)).length > 1.8:  # bigger than cube diagonal
            continue
        visited.add(new_pos)
        result.append(new_pos)
        last = Vector(new_pos)
    return result


def raycast(checkPos):
    chunkKey = tuple_to_chunk_key(checkPos)
    chunk = logic.chunks.get(chunkKey)

    if chunk:
        localPos = floored_tuple(Vector(checkPos) - Vector(chunkKey))

        voxelIndex = tuple_to_index(localPos)
        if chunk.voxels[voxelIndex]:
            return chunk, voxelIndex
        return chunk, None
    return None, None


def blast_sphere(radius):
    unit_sized = round(radius, 1) == int(radius)
    print("SPHERE", unit_sized)
    # cube if radius is integer
    casualty = []
    bR = int(radius)
    for x in range(-bR, bR + 1):
        for y in range(-bR, bR + 1):
            for z in range(-bR, bR + 1):
                v = Vector((x, y, z))
                if unit_sized or v.length <= radius:
                    casualty.append(v)
    return casualty


def get_ray_hit(position, direction):
    #  chunk TODO
    if not direction.length:
        return
    pos = Vector(position)

    cubes = generate_block_ray(pos, direction, 10)
    last = cubes[0]
    for index in range(500):
        if len(cubes) == index:
            pos += direction * 9
            cubes += generate_block_ray(pos, direction, 10)

        new_pos = cubes[index]

        chunk, voxel = logic.chunks.raycast(new_pos)
        normal = Vector(last) - Vector(new_pos)
        last = new_pos
        if voxel and voxel.val:
            return chunk, voxel, new_pos, normal
    return None, None, None, None


def blast(cont):
    own = cont.owner
    direction = cont.sensors["Over"].rayDirection
    position = Vector(own.worldPosition)
    if not direction.length:
        return
    chunk, voxel, hit_pos, normal = get_ray_hit(position, direction)
    if voxel:
        if own.get('select') == 1:
            logic.work.append(ChangeWork(Vector(hit_pos), 0))
        elif own.get('select') == 2:
            logic.work.append(RemoveWork(hit_pos, 0))
            print("REMOVE")
        elif own.get('select') == 3:
            voxel = logic.chunks.quick_voxel(Vector(hit_pos) + normal)
            if voxel.NPC:
                voxel.NPC.die()


def build(cont):
    own = cont.owner
    direction = cont.sensors["Over"].rayDirection
    position = Vector(own.worldPosition)
    if not direction.length:
        return
    chunk, voxel, hit_pos, normal = get_ray_hit(position, direction)
    if voxel:
        if own.get('select') == 1:
            logic.work.append(ChangeWork(Vector(hit_pos) + normal * logic.RADIUS, 3))

        elif own.get('select') == 2:
            logic.work.append(RemoveWork(Vector(hit_pos) + normal, 4))
        elif own.get('select') == 3:
            free_pos = Vector(hit_pos) + normal
            obj = scene.addObject('Sheep', "World_manager")
            obj.worldPosition = free_pos


def mark(cont):
    own = cont.owner
    direction = cont.sensors["Over"].rayDirection
    position = Vector(own.worldPosition)
    if not direction.length:
        return
    chunk, voxel, hit_pos, normal = get_ray_hit(position, direction)
    if voxel:
        logic.marker = Vector(hit_pos) + normal
        print('marker', logic.marker, chunk.pos)

        if not getattr(logic, "marker_object", None):
            logic.marker_object = scene.addObject("Marker", "World_manager")
        logic.marker_object.worldPosition = logic.marker
