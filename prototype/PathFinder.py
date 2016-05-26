from Chunk import *
from bge import logic,events,render
from mathutils import Vector
from time import time
from random import random,shuffle,choice,randint
from math import floor
from heapq import *
from collections import deque,Counter
from work import *

scene = logic.getCurrentScene()

# Close discovored
# Hybrid 6k
# Simple 2k
# Branching 20K+

# Medium dist, discovered
# Branching 20k
# Simple 2.5k
# Hybrid  2.9K




# POSSIBLE_MOVES = [  (-1, -1, 0), (-1, 0, 0), (-1, 1, 0), (0, -1, 0), (0, 1, 0), (1, -1, 0), (1, 0, 0), (1, 1, 0), 
#             (-1, 0, -1), (0, -1, -1), (0, 1, -1), (1, 0, -1), 
#             (-1, 0, 1), (0, -1, 1), (0, 1, 1), (1, 0, 1)]


POSSIBLE_MOVES_DICT = {
    (-1, -1, 0) :((0, -1, 0),(-1, 0, 0),(-1, -1, 0)),
    (-1, 0, 0)  :((-1, 0, 0),),
    (-1, 1, 0)  :((0, 1, 0),(-1, 0, 0),(-1, 1, 0)),
    (0, -1, 0)  :((0, -1, 0),),
    (0, 1, 0)   :((0, 1, 0),),
    (1, -1, 0)  :((0, -1, 0),(1, 0, 0),(1, -1, 0)),
    (1, 0, 0)   :((1, 0, 0),),
    (1, 1, 0)   :((0, 1, 0),(1, 0, 0),(1, 1, 0)),

    (-1, 0, -1) :((-1, 0, 0),(-1, 0, -1),), 
    (0, -1, -1) :((0, -1, 0),(0, -1, -1),), 
    (0, 1, -1)  :((0, 1, 0),(0, 1, -1),), 
    (1, 0, -1)  :((1, 0, 0),(1, 0, -1),), 
    (-1, 0, 1)  :((0, 0, 1),(-1, 0, 1),), 
    (0, -1, 1)  :((0, 0, 1),(0, -1, 1),), 
    (0, 1, 1)   :((0, 0, 1),(0, 1, 1),), 
    (1, 0, 1)   :((0, 0, 1),(1, 0, 1),)
}

POSSIBLE_MOVES = list( POSSIBLE_MOVES_DICT.keys() )


def isAir(voxel):
    return voxel and voxel.val == 0 and not voxel.NPC
def isSolid(voxel):
    return bool(voxel and voxel.val!=0)
def isNPC(voxel):
    return (voxel and voxel.NPC)


class PathMaster:   
    def __init__(self, path,success=True):        
        self.path = path
        self._success = success
    def valid(self):
        return bool(self.path)
    @property
    def success(self):
        return self._success

class PathObject(object):
    PATH_SUCCESS = 0
    PATH_WAIT    = 1
    PATH_FAIL    = 2

    """docstring for PathObject"""
    def __init__(self, pos):
        super(PathObject, self).__init__()
        self.pos = pos
        self.work = None

    def assign(self,worker):
        self.work = self.complete(worker)

    def tick(self):
        state = next(self.work)
        return state

    def complete(self,worker):
        yield PathObject.PATH_WAIT
        while True:
            if not worker.isTired():                
                validMove = worker - Vector(self.pos)  
                if validMove:
                    worker.walkExpend()
                    yield PathObject.PATH_SUCCESS
                    break
                else:
                    yield PathObject.PATH_FAIL
            yield PathObject.PATH_WAIT


class DestructivePathObject(PathObject):
    def __str__(self):
        return str(self.pos)

    def complete(self,worker):
        yield PathObject.PATH_WAIT
        # print('START')

        while True:
            if worker.energy > 0.3: 

                #TODO if floor exists:

                delta =  flooredTuple( Vector(self.pos) - Vector(worker.pos) ) 
                if not delta in POSSIBLE_MOVES_DICT:
                    # print("Non legit move O_O")
                    yield PathObject.PATH_FAIL

                for dv in POSSIBLE_MOVES_DICT[delta]:
                    checkPos = Vector(worker.pos) + Vector(dv)
                    chunk, voxel = logic.chunks.checkRay(checkPos)  
                    if isSolid(voxel):
                        logic.work.append(RemoveWork(checkPos,0))
                        for i in range(20):
                            if voxel.val != 0:
                                yield PathObject.PATH_WAIT
                            else:
                                break
                        #logic.chunks.update(chunk.pos, updateNeighbours=True)



                validMove = worker - Vector(self.pos)  
                if validMove:
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
        self.work = self.solvePaths()
    def append(self,path_generator):
        self.tasks.append(path_generator)

    def solvePaths(self):
        while True:            
            if not len(self.tasks): 
                yield True
                continue
            path_to_be_worked = self.tasks.popleft()
            path_generator = path_to_be_worked.solve()
            while next(path_generator):
                yield False
    
    def tick(self,limit = 0.005):
        start = time()
        while time()-start<limit:
            free = next(self.work)
            if free: return

class BestOf(object):
    """docstring for BestOf"""
    def __init__(self):
        self.item = None
        self.value = None
    def check(self,value,item):
        if self.value==None or self.value>=value:
            self.item,self.value = item,value

class RandomOf(object):
    """docstring for BestOf"""
    def __init__(self):
        self.item = None
        self.value = None
    def check(self,value,item):
        if self.value==None or random()>0.99:
            self.item,self.value = item,value
        
class PathGenerator:

    BEST_COMPARATOR = BestOf

    def __init__(self,start,end,client,search_limit=400):
        self.start = start
        self.end = end
        self.client = client
        self.search_limit = search_limit

    def visual(self,pos,color,time, scale = (1,1,1)):
        # return
        time = int(time * 20 + 1)
        # time = 1
        _, voxel = logic.chunks.checkRay(pos)
        if voxel:
            trace, last = voxel.trace
            obj = scene.addObject("aCube","Empty",time)
            obj.orientation = (0,0,0)
            obj.worldScale = scale
            obj.worldPosition = pos 
            obj.color = ((1-trace/40,color[1]*trace/40,color[2],color[3]))

    def dist(self,a,b):
        return abs(a[0]-b[0])+abs(a[1]-b[1])+abs(a[2]-b[2])
    
    def backTrack(self,nodeKey,costMap,success=True):

        if not nodeKey:
            print('really failed')
            return PathMaster(None)

        path = [PathObject(nodeKey)]
        _, parent = costMap[ nodeKey ] 
        while parent!=None:
            if len(path)>300:
                print("### a path larger than 300")
                # input()
                break
            path.append(PathObject(parent))
            _, parent = costMap[ parent ]

        for node in path:
            self.visual(node.pos,(0,0,0,0.3),80)
 
        path.pop(-1)        
        return PathMaster(path,success=success) 


    def heur(self,current,debug=False):        
        return  abs(self.end[0]-current[0])+abs(self.end[1]-current[1])+abs(self.end[2]-current[2])



    def solve(self):

        start,end,client = self.start,self.end,self.client
        q = [  (0,0,start,None ) ]  
        costMap = {}

        bestKey = None
        COUNTER_DISCOVERED = 0

        current_best = self.BEST_COMPARATOR()

        while len(q) and COUNTER_DISCOVERED<self.search_limit:
            # resting interval
            if not COUNTER_DISCOVERED % 15: 
                yield True                 

            currentCost, currentG, nodeKey, parent = heappop(q) 

            # search end criteria
            heur = self.heur(nodeKey)
            if heur<=1:   
                costMap[ nodeKey ] = (currentCost,parent)              
                client.path = self.backTrack(nodeKey,costMap)  
                break

            # has already been discovered?
            oldCost = costMap.get(nodeKey,(999090999090,))[0]
            if oldCost<=currentCost: continue

            costMap[ nodeKey ] = (currentCost,parent) 
            # atleast remember this
            current_best.check(heur,parent) 

            # search flood visual
            self.visual(nodeKey,(0.1,1,0.1,0.6),60)   
            
            # # voxel current voxel is occupied by a NPC
            # voxel = logic.chunks.checkRay(nodeKey)[1]
            # if voxel.NPC and COUNTER_DISCOVERED>1:
            #     continue

            COUNTER_DISCOVERED += 1

            for deltaVector,airSpace in POSSIBLE_MOVES_DICT.items():

                newPos = (nodeKey[0]+deltaVector[0],nodeKey[1]+deltaVector[1],nodeKey[2]+deltaVector[2])
                
                isValid = False

                H = self.heur(newPos)
                if H==0:
                    isValid = True
                else:
                    for deltaAirVector in airSpace:
                        newAirPos = (
                            nodeKey[0]+deltaAirVector[0],
                            nodeKey[1]+deltaAirVector[1],
                            nodeKey[2]+deltaAirVector[2]
                        )
                        _, voxel    =  logic.chunks.checkRay(newAirPos)
                        if not isAir(voxel): break
                    else:
                        _, ground   =  logic.chunks.checkRay((newPos[0],newPos[1],newPos[2]-1))
                        if isSolid(ground):
                            isValid = True

                if isValid:
                    G = currentG + 1
                    F = G + H 

                    neighbourCost = costMap.get(newPos,(999090999090,))[0]
                    if neighbourCost <= F: continue

                    heappush(q,(F,G,newPos,nodeKey))  
        else:   
            client.path = self.backTrack(current_best.item,costMap,success=False)  

            print("failed path,")

        yield False


class NearestTargetPathGenerator(PathGenerator):

    BEST_COMPARATOR = RandomOf

    def heur(self,current,debug=False):        
        voxel    =  logic.chunks.checkRay(current)[1]
        if not voxel:
            return 99999999
        if voxel.NPC and  isinstance(voxel.NPC,self.end):
            # print('self.end exists',voxel.NPC)
            return 0
        trace, caster = voxel.trace
        if caster and not issubclass(caster,self.end): 
            trace = 60
        dist = self.dist(current,self.start)
        if dist<10:
            dist = 0
        return 10  + dist + randint(0,1) + trace//2



class DestructPathGenerator(PathGenerator):

    def backTrack(self,nodeKey,costMap,success=True):

        if not nodeKey:
            print('really failed')
            return PathMaster(None)

        path = [DestructivePathObject(nodeKey)]
        _, parent = costMap[ nodeKey ] 
        while parent!=None:
            if len(path)>300:
                print("### a path larger than 300")
                # input()
                break
            path.append(DestructivePathObject(parent))
            _, parent = costMap[ parent ]

        for node in path:
            self.visual(node.pos,(1,1,1,1),380,scale=(0.5,0.5,0.5))
 
        path.pop(-1)   
        # print(*path)     
        return PathMaster(path,success=success) 

    def solve(self):

        start,end,client = self.start,self.end,self.client
        q = [  (0,0,start,None,set()) ]  
        costMap = {}

        bestKey = None
        COUNTER_DISCOVERED = 0

        current_best = BestOf()

        blastedDict = {None:set()}

        loopCounter = 1
        while len(q) and COUNTER_DISCOVERED<self.search_limit:

            loopCounter += 1
            # resting interval
            if not COUNTER_DISCOVERED % 15: 
                yield True                 

            currentCost, currentG, nodeKey, parent, removeList = heappop(q) 

            # search end criteria
            heur = self.heur(nodeKey)
            if heur<=1:   
                print('best path',len(q) , COUNTER_DISCOVERED,loopCounter)  
                print('nodecount', len(q)+loopCounter,'discovered',COUNTER_DISCOVERED)
                costMap[ nodeKey ] = (currentCost,parent)              
                client.path = self.backTrack(nodeKey,costMap)  
                break

            # has already been discovered?
            if nodeKey in costMap: continue

            costMap[ nodeKey ] = (currentCost,parent) 

            # currently removed blocks
            parentBlasted = blastedDict[parent]            
            currentBlasted = set(parentBlasted) 
            if removeList:
                currentBlasted |= set(removeList)                
            blastedDict[nodeKey] = currentBlasted

            # atleast remember this
            current_best.check(heur,parent) 

            # search flood visual
            self.visual(nodeKey,(0.1,1,0.1,0.6),60)   
 
            COUNTER_DISCOVERED += 1

            for deltaVector,airSpace in POSSIBLE_MOVES_DICT.items():

                newPos = (nodeKey[0]+deltaVector[0],nodeKey[1]+deltaVector[1],nodeKey[2]+deltaVector[2])
                if newPos in costMap :continue

                newGroundPos = (newPos[0],newPos[1],newPos[2]-1)
                if newGroundPos in currentBlasted:continue

                _, ground   =  logic.chunks.checkRay(newGroundPos)
                if not isSolid(ground): continue 

                _, voxel   =  logic.chunks.checkRay(newPos)
                H = self.heur(newPos)

                G = currentG + 1 

                remList = []

                deltaKey = (newPos[0]-nodeKey[0],newPos[1]-nodeKey[1],newPos[2]-nodeKey[2])
                for dv in POSSIBLE_MOVES_DICT[deltaKey]:
                    checkPos = (nodeKey[0]+dv[0],nodeKey[1]+dv[1],nodeKey[2]+dv[2])
                    _, curretVoxel = logic.chunks.checkRay(checkPos)

                    if isSolid(curretVoxel) and not checkPos in currentBlasted:
                        remList.append(checkPos)
                        G += 2

                F = G + H 
                heappush(q,(F,G,newPos,nodeKey,remList))  

        else:
            print('best effort path',len(q) , COUNTER_DISCOVERED,loopCounter)   
            client.path = self.backTrack(current_best.item,costMap,success=False)  

            # print("failed path,")

        yield False





class DestructMemoryPathGenerator(PathGenerator):

    def backTrack(self,currentIndex,parentChain,success=True):

        if not currentIndex:
            print('really failed')
            return PathMaster(None)

        path = []
        while currentIndex!=None:
            node, currentIndex = parentChain[ currentIndex ] 
            if len(path)>300:
                print("### a path larger than 300")
            path.append(DestructivePathObject(node))
            

        for node in path:
            self.visual(node.pos,(1,1,1,1),380,scale=(0.5,0.5,0.5))
 
        path.pop(-1)   
        return PathMaster(path,success=success) 

    def solve(self):

        start,end,client = self.start,self.end,self.client
        q = [  (0,0,start,None,0) ]  
        costMap = {}

        bestKey = None
        COUNTER_DISCOVERED = 0

        current_best = BestOf()

        blastMap = [[]]
        parentChain = []


        loopCounter = 1
        while len(q) and COUNTER_DISCOVERED<self.search_limit:

            loopCounter += 1

            # resting interval
            if not COUNTER_DISCOVERED % 15: 
                yield True                 

            currentCost, currentG, nodeKey, parentChainIndex, removeListIndex = heappop(q) 
            removeList = blastMap[removeListIndex]

            # search end criteria
            heur = self.heur(nodeKey)
            if heur<=1:   
                print('best path',len(q) , COUNTER_DISCOVERED,loopCounter)  
                print('nodecount', len(q)+loopCounter,'discovered',COUNTER_DISCOVERED)
                parentChain.append( (nodeKey,parentChainIndex) )    
                print('parentChainSize',len(parentChain))         
                client.path = self.backTrack(len(parentChain)-1,parentChain)  
                break

            costMapKey = (nodeKey,tuple(removeList) )

            # has already been discovered?
            oldCost = costMap.get(costMapKey,999090999090)
            if oldCost<=currentCost: continue
            costMap[ costMapKey ] = currentCost

            parentChain.append( (nodeKey,parentChainIndex) )
            nodeChainIndex = len(parentChain)-1
            
            # atleast remember this
            current_best.check(heur,nodeChainIndex) 

            # search flood visual
            self.visual(nodeKey,(0.1,1,0.1,0.6),60)   
 
            COUNTER_DISCOVERED += 1

            for deltaVector,airSpace in POSSIBLE_MOVES_DICT.items():

                newPos = (nodeKey[0]+deltaVector[0],nodeKey[1]+deltaVector[1],nodeKey[2]+deltaVector[2])
                if newPos in costMap :continue

                newGroundPos = (newPos[0],newPos[1],newPos[2]-1)
                if newGroundPos in removeList:continue

                _, ground   =  logic.chunks.checkRay(newGroundPos)
                if not isSolid(ground): continue 

                _, voxel   =  logic.chunks.checkRay(newPos)
                H = self.heur(newPos)

                G = currentG + 1 

                remList = list(removeList)

                deltaKey = (newPos[0]-nodeKey[0],newPos[1]-nodeKey[1],newPos[2]-nodeKey[2])
                for dv in POSSIBLE_MOVES_DICT[deltaKey]:
                    checkPos = (nodeKey[0]+dv[0],nodeKey[1]+dv[1],nodeKey[2]+dv[2])
                    _, curretVoxel = logic.chunks.checkRay(checkPos)

                    if isSolid(curretVoxel) and not checkPos in removeList:
                        remList.append(checkPos)
                        G += 2

                newRemoveListIndex = len(blastMap)
                blastMap.append(remList)

                F = G + H 
                heappush(q,(F,G,newPos,nodeChainIndex,newRemoveListIndex))  

        else:
            print('best effort path',len(q) , COUNTER_DISCOVERED,loopCounter)   
            client.path = self.backTrack(current_best.item,parentChain,success=False)  

            # print("failed path,")

        yield False


#best path 914 181 581
#best path 254 26 32
#best path 227 26 28


class HybridPathGenerator(PathGenerator):

    SPLIT_RATIO = 0.2

    def backTrack(self,nodeKey,costMap,success=True):

        if not nodeKey:
            print('really failed')
            return PathMaster(None)

        path = [DestructivePathObject(nodeKey)]
        _, parent = costMap[ nodeKey ] 
        while parent!=None:
            if len(path)>300:
                print("### a path larger than 300")
                # input()
                break
            path.append(DestructivePathObject(parent))
            _, parent = costMap[ parent ]

        for node in path:
            self.visual(node.pos,(1,1,1,1),380,scale=(0.5,0.5,0.5))
 
        path.pop(-1)   
        # print(*path)     
        return PathMaster(path,success=success) 

    def solve(self):

        start,end,client = self.start,self.end,self.client
        q = [  (0,0,start,None ) ]  
        costMap = {}

        bestKey = None
        COUNTER_DISCOVERED = 0

        current_best = BestOf()

        blockedNodes = []

        loopCounter = 1
        while len(q) and COUNTER_DISCOVERED<self.search_limit*self.SPLIT_RATIO:
            loopCounter += 1
            # resting interval
            if not COUNTER_DISCOVERED % 15: 
                yield True                 

            currentCost, currentG, nodeKey, parent = heappop(q) 

            # search end criteria
            heur = self.heur(nodeKey)
            if heur<=1:   
                print('hybrid stage 1 resuls',len(q) , COUNTER_DISCOVERED,loopCounter)  
                print('nodecount', len(q)+loopCounter,'discovered',COUNTER_DISCOVERED)
                costMap[ nodeKey ] = (currentCost,parent)              
                client.path = self.backTrack(nodeKey,costMap)  
                yield False
                return

            # has already been discovered?
            oldCost = costMap.get(nodeKey,(999090999090,))[0]
            if oldCost<=currentCost: continue

            costMap[ nodeKey ] = (currentCost,parent) 
            # atleast remember this
            current_best.check(heur,parent) 

            # search flood visual
            self.visual(nodeKey,(0.1,1,0.1,0.6),60)   

            COUNTER_DISCOVERED += 1

            for deltaVector,airSpace in POSSIBLE_MOVES_DICT.items():

                newPos = (nodeKey[0]+deltaVector[0],nodeKey[1]+deltaVector[1],nodeKey[2]+deltaVector[2])
                
                isValid = False

                H = self.heur(newPos)
                if H==0:
                    isValid = True
                else:
                    for deltaAirVector in airSpace:
                        newAirPos = (
                            nodeKey[0]+deltaAirVector[0],
                            nodeKey[1]+deltaAirVector[1],
                            nodeKey[2]+deltaAirVector[2]
                        )
                        _, voxel    =  logic.chunks.checkRay(newAirPos)
                        if not isAir(voxel): break
                    else:
                        _, ground   =  logic.chunks.checkRay((newPos[0],newPos[1],newPos[2]-1))
                        if isSolid(ground):
                            isValid = True
                G = currentG + 1
                F = G + H   
                if isValid:
                    

                    neighbourCost = costMap.get(newPos,(999090999090,))[0]
                    if neighbourCost <= F: continue

                    heappush(q,(F,G,newPos,nodeKey))  
                else:
                    blockedNodes.append((F,G,newPos,nodeKey))
        
        # else try option two
        print(loopCounter,'mid stage',len(q) , COUNTER_DISCOVERED, 'blockedListSize', len(blockedNodes) )  
        print('mid_nodecount', len(q)+loopCounter,'discovered',COUNTER_DISCOVERED)

        blastedDict = {None:set()}


        # re-activate blocked nodes
        for i,blockedNode in enumerate(blockedNodes):
            if not i % 100:
                yield True

            F,G,newPos,nodeKey = blockedNode       

            blastedDict[nodeKey] = set()     

            deltaKey = (newPos[0]-nodeKey[0],newPos[1]-nodeKey[1],newPos[2]-nodeKey[2])
            airSpace = POSSIBLE_MOVES_DICT[deltaKey]

            newGroundPos = (newPos[0],newPos[1],newPos[2]-1) 

            _, ground   =  logic.chunks.checkRay(newGroundPos)
            if not isSolid(ground): continue 

            H = self.heur(newPos) 
            G = currentG + 1 

            remList = []
            for dv in airSpace:
                checkPos = (nodeKey[0]+dv[0],nodeKey[1]+dv[1],nodeKey[2]+dv[2])
                _, curretVoxel = logic.chunks.checkRay(checkPos)

                if isSolid(curretVoxel):
                    remList.append(checkPos)
                    G += 2

            F = G + H 
            heappush(q,(F,G,newPos,nodeKey,remList))

        
        # COUNTER_DISCOVERED = 0 SPLIT_RATIO


        while len(q) and COUNTER_DISCOVERED<self.search_limit:
            loopCounter += 1

            # resting interval
            if not COUNTER_DISCOVERED % 15: yield True

            # stich together
            current = heappop(q)
            removeList = None   
            if len(current) == 5:
                currentCost, currentG, nodeKey, parent, removeList = current
            else:
                currentCost, currentG, nodeKey, parent = current

            # search end criteria
            heur = self.heur(nodeKey)
            if heur<=1:   
                print(loopCounter,'stage two path',len(q) , COUNTER_DISCOVERED)  
                print('nodecount', len(q)+loopCounter,'discovered',COUNTER_DISCOVERED)
                costMap[ nodeKey ] = (currentCost,parent)              
                client.path = self.backTrack(nodeKey,costMap)  
                yield False
                return

            # has already been discovered?
            if nodeKey in costMap: continue

            costMap[ nodeKey ] = (currentCost,parent) 

            # currently removed blocks
            parentBlasted = blastedDict[parent]            
            currentBlasted = set(parentBlasted) 
            if removeList:
                currentBlasted |= set(removeList)                
            blastedDict[nodeKey] = currentBlasted

            # atleast remember this
            current_best.check(heur,parent) 

            # search flood visual
            self.visual(nodeKey,(0.1,1,0.1,0.6),60)   
 
            COUNTER_DISCOVERED += 1

            for deltaVector,airSpace in POSSIBLE_MOVES_DICT.items():

                newPos = (nodeKey[0]+deltaVector[0],nodeKey[1]+deltaVector[1],nodeKey[2]+deltaVector[2])
                if newPos in costMap :continue

                newGroundPos = (newPos[0],newPos[1],newPos[2]-1)
                if newGroundPos in currentBlasted:continue

                _, ground   =  logic.chunks.checkRay(newGroundPos)
                if not isSolid(ground): continue 

                # _, voxel   =  logic.chunks.checkRay(newPos)
                H = self.heur(newPos) 

                G = currentG + 1 

                remList = []

                deltaKey = (newPos[0]-nodeKey[0],newPos[1]-nodeKey[1],newPos[2]-nodeKey[2])
                for dv in POSSIBLE_MOVES_DICT[deltaKey]:
                    checkPos = (nodeKey[0]+dv[0],nodeKey[1]+dv[1],nodeKey[2]+dv[2])
                    _, curretVoxel = logic.chunks.checkRay(checkPos)

                    if isSolid(curretVoxel) and not checkPos in currentBlasted:
                        remList.append(checkPos)
                        G += 2

                F = G + H 
                heappush(q,(F,G,newPos,nodeKey,remList))  

        

        print('best effort path',len(q) , COUNTER_DISCOVERED,loopCounter)   
        client.path = self.backTrack(current_best.item,costMap,success=False)  


        yield False