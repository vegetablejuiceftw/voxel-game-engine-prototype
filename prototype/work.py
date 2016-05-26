from Chunk import *
from bge import logic,events
from mathutils import Vector
from time import time
from random import random,shuffle
from math import floor,sin

scene = logic.getCurrentScene()
cont = logic.getCurrentController()
own = cont.owner

logic.RADIUS = 2
logic.BLAST_DELTA = []

def doWork():
    t = time()
    index = 0

    for work in logic.work:

        if type(work) == WaitWork:
            if work.workStep():
                index += 1
                break
            return

        while  time()-t<0.004:
            if work.workStep():
                index += 1
                # print("work Done")#,type(work))
                break
        else:
            if (time()-t)>0.01:
                wait = WaitWork( (time()-t)//0.018 )
                logic.work = [wait]+logic.work
                print("too much",time()-t)
            break
            
    logic.work = logic.work[index:]

class Work:
    def __init__(self):
        self.tool = None
        self.work = None        
        self.done = False

    def workStep(self):
        if not self.work:
            self.work = self.tool()
        if self.done:
            return True
        self.done = next(self.work)
        return self.done

class WaitWork(Work):
    """docstring for ClassName"""
    def __init__(self, arg):
        super(WaitWork, self).__init__()
        self.arg = arg
        self.tool = self.wait
    def wait(self):
        while self.arg > 0:
            self.arg -= 1
            yield False
        yield True 

# class ChunkWork(Work)        

class ChangeWork(Work):
    def __init__(self,addPos,type):
        super(ChangeWork, self).__init__()
        self.addPos = addPos
        self.type = type
        self.tool = self.changeIterator

    def changeIterator(self):
        pos = flooredTuple(self.addPos)     

        refresh = set() 
        
        newPos = Vector(pos)
        for dv in logic.BLAST_DELTA:
            chunk,voxel = logic.chunks.checkRay(newPos+dv)
            if voxel and voxel.val!=self.type:
                voxel.val = self.type
                refresh.add(chunk.getKey())

            if dv.length>=0.93*logic.RADIUS:
                obj = scene.addObject("Cube",own,5)
                obj.orientation = (0,0,0)
                obj.worldPosition = newPos+dv
            yield False

        toSpawn = set()
        for key in refresh:
            c = logic.chunks.get(key)
            if c:
                for i in range((CHUNK_SIZE+1)*3):
                    c.generateFacesByStep(i) 
                    yield False                
                yield False
                toSpawn |= set( logic.chunks.update(key,genFaces=False) )
                yield False
        for key in toSpawn:
            c = logic.chunks[key]
            for i in range((CHUNK_SIZE+1)*3):
                c.generateFacesByStep(i) 
                yield False                
            yield False
            logic.chunks.update(key,genFaces=False)
            yield False
        yield True


class RemoveWork(Work):
    def __init__(self,remPos,givenType):
        super(RemoveWork, self).__init__()
        self.remPos = flooredTuple(remPos)
        self.type = givenType
        self.tool = self.changeIterator        

    def changeIterator(self):
        chunk,voxel = logic.chunks.checkRay(self.remPos)

        if voxel and voxel.val!=type and not voxel.NPC:
            voxel.val = self.type
            obj = scene.addObject("Cube",own,5)
            obj.worldPosition = self.remPos

        toSpawn = set()
        if chunk:
            for i in range((CHUNK_SIZE+1)*3):
                chunk.generateFacesByStep(i) 
            toSpawn |= set( logic.chunks.update(chunk.getKey(),genFaces=False) )
        yield True

        