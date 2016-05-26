from Chunk import *
from bge import logic,events,render
from mathutils import Vector
from time import time
from random import random,shuffle,choice,randint
from math import floor
from heapq import *
from collections import deque,Counter
from PathFinder import *
from animus import *


scene = logic.getCurrentScene()
logic.npc = []
logic.PathManager = PathManager()
logic.NPC_TICK_COUNTER = 0
logic.NPC_CURRENT_INDEX = 0
logic.NPC_TIME_CONSTANT = 0.01
logic.marker = (0,0,0)


class NPC(AnimusAlpha):
    POS_CHECK = None
    POSITIONS = {}
    ROOM_SIZE = 8
    COUNT = 0
    def __init__(self,obj):
        super(NPC, self).__init__()
        NPC.POS_CHECK = logic.chunks.checkRay

        pos = flooredTuple( obj.worldPosition )
        obj.worldPosition = Vector(pos)
        self._pos = obj.worldPosition
        # self.pos = obj.worldPosition

        self.lastVoxel = self.POS_CHECK(self.pos)[1]
        self.register(self.lastVoxel)
        self.obj = obj
        self.visual = obj.children.get(obj.name+'_visual')
        self.info = obj.children.get(obj.name+'_text')
        self.alive = True
        self.lastMove = Vector((0,0,0))

        self.target = None
        self.path = None

        self.stupid = True

        self.lastTick = time()
        self.energy = 0

        NPC.COUNT += 1
        self.name = 'NPC_BASIC'



    def __add__(self,other):
        if type(other) == Vector:
            return self.move(other)
    
    def __sub__(self,other):        
        if type(other) == Vector:
            relativeV = other-self.pos
            return self.move(relativeV)

    def roomIndex(self,pos):
        return tuple(int(i//NPC.ROOM_SIZE)*NPC.ROOM_SIZE for i in pos)

    def changeRoom(self,old):

        key = self.roomIndex(old)  
        room = NPC.POSITIONS.get(key)
        if room : room.discard(self)

        key = self.roomIndex(self.pos)
        if key in NPC.POSITIONS:
            NPC.POSITIONS[key].add(self)
        else:
            NPC.POSITIONS[key] = set([self])

        
    def dist(self,other):
        return (self.pos-other.pos).length

    def near(self,typeClass,quick=False):
        # print(self.name)
        key = self.roomIndex(self.pos)
        deltas = [(0, 0, 0), (-NPC.ROOM_SIZE, 0, 0), (0, -NPC.ROOM_SIZE, 0), (0, 0, -NPC.ROOM_SIZE), (0, 0, NPC.ROOM_SIZE), (0, NPC.ROOM_SIZE, 0), (NPC.ROOM_SIZE, 0, 0), (-NPC.ROOM_SIZE, -NPC.ROOM_SIZE, 0), (-NPC.ROOM_SIZE, 0, -NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, 0, NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, NPC.ROOM_SIZE, 0), (0, -NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (0, -NPC.ROOM_SIZE, NPC.ROOM_SIZE), (0, NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (0, NPC.ROOM_SIZE, NPC.ROOM_SIZE), (NPC.ROOM_SIZE, -NPC.ROOM_SIZE, 0), (NPC.ROOM_SIZE, 0, -NPC.ROOM_SIZE), (NPC.ROOM_SIZE, 0, NPC.ROOM_SIZE), (NPC.ROOM_SIZE, NPC.ROOM_SIZE, 0), (-NPC.ROOM_SIZE, -NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, -NPC.ROOM_SIZE, NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (-NPC.ROOM_SIZE, NPC.ROOM_SIZE, NPC.ROOM_SIZE), (NPC.ROOM_SIZE, -NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (NPC.ROOM_SIZE, -NPC.ROOM_SIZE, NPC.ROOM_SIZE), (NPC.ROOM_SIZE, NPC.ROOM_SIZE, -NPC.ROOM_SIZE), (NPC.ROOM_SIZE, NPC.ROOM_SIZE, NPC.ROOM_SIZE)]
        radar = []
        count = 0
        # print(typeClass,quick)
        for dV in deltas:
            checkKey = (key[0]+dV[0],key[1]+dV[1],key[2]+dV[2])
            neighbours = NPC.POSITIONS.get(checkKey,[])
            for other in neighbours:
                count += 1
                if not typeClass or isinstance(other,typeClass):
                    dist = self.dist(other)
                    if quick:                        
                        return [(dist,other)]
                    radar.append((dist,other))
        return sorted( radar, key=lambda x:x[0])

    @property
    def pos(self):
        return Vector(self._pos)

    def register(self,voxel):
        if self.lastVoxel:
            #self.lastVoxel.val = 0
            self.lastVoxel.NPC = None
        if voxel:            
            self.lastVoxel = voxel
            #voxel.val = -1
            voxel.NPC = self

    def recharge(self):
        #if random()>0.7:
        self.energy += (time()-self.lastTick)
        self.lastTick = time()

    def move(self,vector):
        if self.visual:
            if vector.length !=0:
                self.visual.alignAxisToVect(vector,1)
            else:
                self.visual.alignAxisToVect((0,1,0),1)
            self.visual.alignAxisToVect((0,0,1),2)
        
        airSpace = POSSIBLE_MOVES_DICT.get(flooredTuple(vector))

        if airSpace == None:
            return False

        for deltaAirVector in airSpace:
            newAirPos = (
                self.pos[0]+deltaAirVector[0],
                self.pos[1]+deltaAirVector[1],
                self.pos[2]+deltaAirVector[2]
            )
            _, voxel    =  logic.chunks.checkRay(newAirPos)
            if not isAir(voxel):
                # print('not air',newAirPos,voxel)
                break
        else:
            targetPos = self.pos + vector
            _, ground   =  logic.chunks.checkRay((targetPos[0],targetPos[1],targetPos[2]-1))
            if isSolid(ground):
                _, targetVoxel    =  self.POS_CHECK(targetPos)
                old = Vector(self._pos)
                self._pos +=  vector
                self.register(targetVoxel) 
                self.changeRoom(old)
                return True
            # else:
                # print('not ground')
        return False

    def tick(self):
        self.gravity()


    def gravity(self):
        standingPos = self.pos + Vector((0,0,-1))
        standingVox = self.POS_CHECK(standingPos)[1]
        if isAir(standingVox):
            old = Vector(self._pos)
            self._pos +=  Vector((0,0,-1))
            self.register(standingVox) 
            self.changeRoom(old)

        if self.pos.z< -100:
            self.alive = False

    def die(self):
        self.alive = False
        self.register(None)
        self.obj.endObject()

    """ Override this to chagne pathing algorithm"""
    def createPathGenerator(self):
        start   = flooredTuple(self.pos)
        return PathGenerator(start,logic.marker,self)


    def checkForPrey(self):
        pass

    def travel(self):        
        waiting = False

        while True:
            if not waiting:

                pathGenerator = self.createPathGenerator()
                logic.PathManager.append(pathGenerator)
                waiting = True
                self.path = None
            # path has arrived
            elif self.path!=None:
                # path is bad
                if self.path and not self.path.valid():
                    waiting = False
                    # print('path is bat',self.path.path )

                else:

                    pathObj = self.path.path.pop(-1)
                    pathObj.assign(self) 
                    state = pathObj.tick()
                    while state==PathObject.PATH_WAIT:
                        yield
                        state = pathObj.tick()

                    if state == PathObject.PATH_FAIL or not self.path.valid():
                        self.checkForPrey()
                        waiting = False

                        # print('path is state bad',self.path.path ,state == PathObject.PATH_FAIL , not self.path.valid())


            yield



class Sheep(NPC):
    """docstring for Sheep"""

    def __init__(self, arg):
        super(Sheep, self).__init__(arg)
        self.stupid = True
        self.name = str(NPC.COUNT) + 'SHEEP'

    def tick(self):
        if self.energy>0:
            self.brownianMotion()
            self.energy-=0.21
        self.gravity()
        self.recharge()

        if random() > 0.98:
            self.info.text = 'Baah'
        elif random() > 0.97:    
            self.info.text = ''

    def brownianMotion(self):

        dangerNPC = self.near(Wolf,quick=True) + self.near(StateWolf,quick=True) 

        if dangerNPC:
            dist,danger = dangerNPC[0] 
            direction   = Vector(danger.pos)-self.pos
            MAX = 60
            distance    = min(direction.length,MAX)
            valid = False
            while not valid:
                rV          = Vector(choice( list(POSSIBLE_MOVES_DICT.keys() )))
                valid       = direction.angle(rV,999) > random() * (MAX-distance)/MAX * 4
            render.drawLine(self.pos,self.pos+rV*5,(1,0.1,0.5))
            self + rV
            self.lastMove = rV
        else:
            deltaVector = choice( list(POSSIBLE_MOVES_DICT.keys() ))
            self + Vector(deltaVector)


class Wolf(NPC):
    """docstring for Sheep"""
    def __init__(self, arg):
        super(Wolf, self).__init__(arg)
        self.task = self.travel()
        self.stupid = False

    def tick(self):
        self.gravity() 
        self.recharge()
        #if self.energy>0:
            # print(self.energy)
        next(self.task)

    def checkForPrey(self):
        for dv in POSSIBLE_MOVES:
            checkPos = self.pos + Vector(dv)
            _, checkVoxel =  self.POS_CHECK(checkPos)
            if isNPC(checkVoxel):
                prey = checkVoxel.NPC
                if isinstance(prey,Sheep):
                    print("KILLED",prey)
                    prey.die()

    def createPathGenerator(self):
        start = flooredTuple(self.pos)
        return NearestTargetPathGenerator(start,Sheep,self,search_limit=200)




class Human(NPC):
    """docstring for Sheep"""
    def __init__(self, arg):
        super(Human, self).__init__(arg)
        self.task = self.travel()
        self.stupid = False
        self.info.text = 'I am Human.'

    def tick(self):
        self.gravity() 
        self.recharge()
        next(self.task)


    def createPathGenerator(self):
        # print('using destructo')
        start = flooredTuple(self.pos)
        # return PathGenerator(start,logic.marker,self, search_limit=9000)
        # return DestructMemoryPathGenerator(start,logic.marker,self, search_limit=9000)
        # return DestructPathGenerator(start,logic.marker,self, search_limit=9000)
        return HybridPathGenerator(start,logic.marker,self, search_limit=9000)

class StateWolf(NPC):
    """docstring for Sheep"""
    def __init__(self, arg):
        super(StateWolf, self).__init__(arg)
        self.task = self.travel()       


    def tick(self):
        self.gravity() 
        self.state = self.state.tick()
        self.info.text = self.status()
        # next(self.task)

    def getFood(self):
        for dv in POSSIBLE_MOVES:
            checkPos = self.pos + Vector(dv)
            _, checkVoxel =  self.POS_CHECK(checkPos)
            if isNPC(checkVoxel):
                prey = checkVoxel.NPC
                if isinstance(prey,Sheep):
                    return prey

    # def checkForPrey(self):
    #     for dv in POSSIBLE_MOVES:
    #         checkPos = self.pos + Vector(dv)
    #         _, checkVoxel =  self.POS_CHECK(checkPos)
    #         if isNPC(checkVoxel):
    #             prey = checkVoxel.NPC
    #             if isinstance(prey,Sheep):
    #                 print("KILLED",prey)
    #                 prey.die()

    def createPathGenerator(self):
        start = flooredTuple(self.pos)
        return NearestTargetPathGenerator(start,Sheep,self,search_limit=200)

    
def initNPC(npc):
    logic.npc.append(npc)

def initHuman(cont):
    logic.npc.append(Human(cont.owner))       

def initWolf(cont):
    logic.npc.append(StateWolf(cont.owner)) 

def init(cont):
    logic.npc.append(Sheep(cont.owner))

def initSheep(cont):
    init(cont)

def iteratePathGenerator():
    logic.PathManager.tick()

def iterateNPC(cont):
    NPC_COUNT = len(logic.npc)
    cont.owner['NPC_COUNT'] = NPC_COUNT
    if not NPC_COUNT: return

    EPOCH = time() // logic.NPC_TIME_CONSTANT

    if logic.NPC_TICK_COUNTER != EPOCH:

        if NPC_COUNT > logic.NPC_CURRENT_INDEX:
            startTime = time()    
            temp_counter = 0
            while time()-startTime<0.004 and NPC_COUNT > logic.NPC_CURRENT_INDEX and temp_counter<200: 
                temp_counter+=1
                npc = logic.npc[logic.NPC_CURRENT_INDEX] 
                if not npc.alive:
                    logic.npc.remove(npc)
                    del npc
                    NPC_COUNT = len(logic.npc)
                    continue
                npc.tick()
                logic.NPC_CURRENT_INDEX += 1

        else:
            logic.NPC_CURRENT_INDEX = 0
            logic.NPC_TICK_COUNTER = EPOCH
        
        # print('working',logic.NPC_CURRENT_INDEX/NPC_COUNT)


