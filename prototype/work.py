from time import time
from bge import logic
from mathutils import Vector

from chunk import floored_tuple, CHUNK_SIZE

scene = logic.getCurrentScene()
cont = logic.getCurrentController()
own = cont.owner

logic.RADIUS = 2
logic.BLAST_DELTA = []


def do_work():
    t = time()
    index = 0

    for work in logic.work:

        if type(work) == WaitWork:
            if work.step():
                index += 1
                break
            return

        while time() - t < 0.004:
            if work.step():
                index += 1
                break
        else:
            if (time() - t) > 0.01:
                wait = WaitWork((time() - t) // 0.018)
                logic.work = [wait] + logic.work
                print("too much", time() - t)
            break

    logic.work = logic.work[index:]


class Work:
    def __init__(self):
        self.tool = None
        self.work = None
        self.done = False

    def step(self):
        if not self.work:
            self.work = self.tool()
        if self.done:
            return True
        self.done = next(self.work)
        return self.done


class WaitWork(Work):
    def __init__(self, arg):
        super(WaitWork, self).__init__()
        self.arg = arg
        self.tool = self.wait

    def wait(self):
        while self.arg > 0:
            self.arg -= 1
            yield False
        yield True


class ChangeWork(Work):
    def __init__(self, add_pos, work_type):
        super(ChangeWork, self).__init__()
        self.add_pos = add_pos
        self.type = work_type
        self.tool = self.change_iterator

    def change_iterator(self):
        pos = floored_tuple(self.add_pos)

        refresh = set()

        new_pos = Vector(pos)
        for dv in logic.BLAST_DELTA:
            chunk, voxel = logic.chunks.raycast(new_pos + dv)
            if voxel and voxel.val != self.type:
                voxel.val = self.type
                refresh.add(chunk.get_key())

            if dv.length >= 0.93 * logic.RADIUS:
                obj = scene.addObject("Explosion", own, 5)
                obj.orientation = 0, 0, 0
                obj.worldPosition = new_pos + dv
            yield False

        to_spawn = set()
        for key in refresh:
            c = logic.chunks.get(key)
            if c:
                for i in range((CHUNK_SIZE + 1) * 3):
                    c.generate_faces_by_index(i)
                    yield False
                yield False
                to_spawn |= set(logic.chunks.update(key, gen_faces=False))
                yield False
        for key in to_spawn:
            c = logic.chunks[key]
            for i in range((CHUNK_SIZE + 1) * 3):
                c.generate_faces_by_index(i)
                yield False
            yield False
            logic.chunks.update(key, gen_faces=False)
            yield False
        yield True


class RemoveWork(Work):
    def __init__(self, remove_pos, work_type):
        super(RemoveWork, self).__init__()
        self.remove_pos = floored_tuple(remove_pos)
        self.type = work_type
        self.tool = self.change_iterator

    def change_iterator(self):
        chunk, voxel = logic.chunks.raycast(self.remove_pos)

        if voxel and voxel.val != type and not voxel.NPC:
            voxel.val = self.type
            obj = scene.addObject("Explosion", own, 5)
            obj.worldPosition = self.remove_pos

        to_spawn = set()
        if chunk:
            for i in range((CHUNK_SIZE + 1) * 3):
                chunk.generate_faces_by_index(i)
            to_spawn |= set(logic.chunks.update(chunk.get_key(), gen_faces=False))
        yield True
