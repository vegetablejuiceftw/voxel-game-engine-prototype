from Perlin import Noise
from time import time
from random import randint,shuffle
from math import floor
CHUNK_SEED = "temp2"
CHUNK_SIZE = 8
CHUNK_AREA = CHUNK_SIZE**2
CHUNK_VOLUME = CHUNK_SIZE**3

IGNORE_BLOCK = -99999
#up down left right front back
VOXEL_MAP = {   -1:[-1,-1,-1,-1,-1,-1],
                0:[0,0,0,0,0,0],
                1:[2,2,2,2,2,2],
                2:[1,2,2,2,2,2],
                3:[3,3,3,3,3,3],
                4:[4,4,4,4,4,4],
                5:[5,5,5,5,5,5],
}
GREEN = (0.0,0.7,0.0,1)
DARK_GREEN = (0.0,0.25,0.0,1)
BROWN = (0.6,0.3,0.0,1)
GRAY  = (0.3,0.3,0.3,1)
DARK_BROWN = (0.3,0.1,0.0,1)

COLORS = [None,GREEN,BROWN,GRAY,DARK_BROWN,DARK_GREEN]

bogo = list(range(CHUNK_AREA))
shuffle(bogo)       

def tupleToIndex(givenTuple):
        x,y,z = givenTuple
        return x+y*CHUNK_SIZE+z*CHUNK_AREA

def tupleToChunkKey(pos):
    return tuple(floor(i/CHUNK_SIZE)*CHUNK_SIZE for i in pos)

def flooredTuple(givenTuple):
    return tuple(floor(i) for i in givenTuple)
#####    
from ctypes import *
class Point(Structure):
    _fields_ = [("val", c_int8)]
Voxel_array = Point*CHUNK_VOLUME
#####

class Voxel:

    """docstring for Vector"""
    def __init__(self, val):
        self.val     = val
        self._NPC    = None
        self._trace  = 0
        self._last   = None
    
    @property
    def hasNPC(self):
        return boolean( self._NPC )

    @property
    def NPC(self):
        return self._NPC
    @NPC.setter
    def NPC(self, value):
        #print("derp")
        self._NPC = value
        if value: #!=None
            self._last = value.__class__
        self._trace = time()

    @property
    def trace(self):
        #print(self._last)
        if not self._last:
            return (40,None)
        trace = min(time()-self._trace,40)
        if trace == 40:
            return (40,None)
        return ( trace ,self._last)

    def __str__(self):
        return str(self.val)

    def __hash__(self):        
        return hash(self.val)

    def __lt__(a, b):
        return a.val  <   b.val
    def __le__(a, b):
        return a.val  <=  b.val
    def __ge__(a, b):
        return a.val  >=  b.val
    def __gt__(a, b):
        return a.val  >   b.val

class VoxelPlane:
    def __init__(self, plane, axis):
        self.map = plane
        self.axis = axis*2

    def __getitem__(self, i):

        valA,valB = self.map[i]
        # if not(valA and valB):
        #     return 0
        A = 0
        B = 0
        if valA: A = VOXEL_MAP[valA.val][self.axis]        
        if valB: B = VOXEL_MAP[valB.val][self.axis+1]

        result = 0 

        if (A!=0 and B!=0):
            result = IGNORE_BLOCK 
        elif B: 
            result = B
        else:
            result = A
        return result


    def __len__(self):
        return len(self.map)

    def __str__(self):
        return ",".join([str(i) for i in self.map])

    def __str__(self):
        result = ",".join([ str((str(i),str(j))) for i,j in self.map])+"\n"

        s = "{} "*CHUNK_SIZE+"\n"

        for y in range(CHUNK_SIZE):
            row = []
            for x in range(CHUNK_SIZE):
                T = self[x+y*CHUNK_SIZE]
                if T ==  IGNORE_BLOCK: T = '.'
                row.append( T )
            result += ( s.format(*row))
        result += "\n"
        return result

class VoxelMap:

    def __init__(self, val,size):
        self.map = [Voxel(val) for i in range(size)]
        #self.map = Voxel_array()#[Voxel(val) for i in range(size)]

        self.planes = []
        self.planeMapper()

    def __iter__(self):
        return iter(self.map)

    def __getitem__(self, i):
        return self.map[i].val

    def get(self, i):
        return self.map[i]

    def __setitem__(self, key, value):
        self.map[key].val = value

    def __len__(self):
        return len(self.map)

    def __str__(self):
        return ",".join([str(i) for i in self.map])

    def planeMapper(self):  
        if self.planes:
            return        
        for planeDir in range(3):
            self.planes.append([])
            for A in range(CHUNK_SIZE+1): 
                plane = [None]*CHUNK_AREA  
                for B in range(CHUNK_SIZE):
                    for C in range(CHUNK_SIZE):
                        down, up = None,None
                        if planeDir==0:
                            x,y,z = B,C,A
                            indexA,indexB = (x,y,z-1),(x,y,z)      
                            indexL,indexR = (x,y,CHUNK_SIZE-1),(x,y,0)                     

                        if planeDir==1:
                            x,y,z = A,C,B
                            indexA,indexB = (x-1,y,z),(x,y,z)
                            indexL,indexR = (CHUNK_SIZE-1,y,z),(0,y,z)
                           
                        if planeDir==2:
                            x,y,z = B,A,C
                            indexA,indexB = (x,y-1,z),(x,y,z)
                            indexL,indexR = (x,CHUNK_SIZE-1,z),(x,0,z)
                            

                        if A!=0:
                            down = self.map[tupleToIndex(indexA)]
                        if A!=CHUNK_SIZE:
                            up = self.map[tupleToIndex(indexB)]

                        # if A==0:
                        #     if planeDir==0:
                        #         neighbourVoxels = neighbours[(0,0,-1)].voxels
                        #     if planeDir==1:
                        #         neighbourVoxels = neighbours[(-1,0,0)].voxels
                        #     if planeDir==2:
                        #         neighbourVoxels = neighbours[(0,-1,0)].voxels

                        #     down = neighbourVoxels.get(tupleToIndex(indexL))


                        plane[B+C*CHUNK_SIZE] = (down,up)
                self.planes[-1].append(VoxelPlane(plane,planeDir))
        #print("done")
# 4sec 12k 8x8
class ChunkManager:

    def __init__(self,objBuilder,drawBuilder):
        self._map = dict()
        self._phantoms = dict() ## TODO: will cache those as new candidates
        self.objBuilder = objBuilder
        self.drawBuilder = drawBuilder

    def __getitem__(self, key):
        key = tupleToChunkKey(key)
        chunk = self._map.get(key)   
        if chunk:            
            return chunk
        return self.initChunk(key)

    def get(self,key):
        key = tupleToChunkKey(key)

        if key[2]>CHUNK_SIZE: 
            return self._map.get(key)

        return self[key]
        #return self._map.get(key)

    def initPhantom(self,key):
        if key in self._map:
            return self._map[key]
        if key in self._phantoms:
            return self._phantoms[key]
        chunk = Chunk(*key,genFaces=False)
        self._phantoms[key] = chunk
        return chunk

    def initChunk(self,key):
        if key in self._map:
            chunk = self._map[key]
        else:
            if key in self._phantoms:
                chunk = self._phantoms.pop(key)
            else:
                chunk = Chunk(*key,genFaces=False)  
            self._map[key] = chunk

            s  =  time()

            chunk.generateFaces()
           

            obj = self.objBuilder(len(chunk.faces),key)
            chunk.obj = obj
            self.drawBuilder(chunk,chunk.faces)

            # print('meshing time', round(time()-s,2))

        return chunk


    def update(self,key,genFaces = True, updateNeighbours=False):
        key = tupleToChunkKey(key)
        if key in self._map:
            chunk = self.initChunk(key)
            if genFaces:
                chunk.generateFaces()
            self.drawBuilder(chunk,chunk.faces)
        x,y,z = key
        delta = CHUNK_SIZE
        chunksOfInterest = [(x+delta,y,z),(x-delta,y,z),(x,y+delta,z),(x,y-delta,z),(x,y,z+delta),(x,y,z-delta)]
        
        if updateNeighbours:
            for chunkKey in chunksOfInterest:
                print(chunkKey)
                self.update(chunkKey)
                
        chunksOfInterest = [key for key in chunksOfInterest if key not in self._map]
        return chunksOfInterest

    def checkRay(self,checkPos):
        checkPos = flooredTuple(checkPos)
        chunkKey = tupleToChunkKey(checkPos)
        #chunk = self._map.get(chunkKey)
        
        if chunkKey in self._map:
            chunk = self.initChunk(chunkKey)
            localPos = (checkPos[0]-chunkKey[0],checkPos[1]-chunkKey[1],checkPos[2]-chunkKey[2])

            voxelIndex = tupleToIndex(localPos)
            return (chunk, chunk.voxels.get(voxelIndex))

        return (None,None)



class Chunk:
    """docstring for Chunk"""

    perlin = Noise(16,CHUNK_SEED)

    def __init__(self, posX, posY, posZ, obj = None,genFaces = True):
        
        self.posX = posX
        self.posY = posY
        self.posZ = posZ
        self.pos  = (posX,posY,posZ)
        self.voxels = VoxelMap(0,CHUNK_VOLUME)
        self.faces = []

        self.cache = {} # TODO

        self.cutCounter = 0
        self.hMapCounter = 0
        self.timeCounters = [0]*3

        #self.plane = [0]*CHUNK_AREA

        self.obj = obj

        self.fillVoxels()
        if genFaces:
            self.generateFaces()

    def __len__(self):
        C = 0
        for i in range(CHUNK_VOLUME):
            if self.voxels[i] != 0:
                C += 1
        return C

        

    def getKey(self):
        return flooredTuple((self.posX,self.posY,self.posZ))    
    
    def tupleToIndex(self,tuple):
        x,y,z = tuple
        return x+y*CHUNK_SIZE+z*CHUNK_AREA

    def indexToTuple(self,index):
        z = index//CHUNK_AREA
        index -= z*CHUNK_AREA
        y = index//CHUNK_SIZE
        x = index - y*CHUNK_SIZE
        return (x,y,z)

    def fillVoxels(self):

        for x in range(CHUNK_SIZE):
            for y in range(CHUNK_SIZE):
                cX,cY = self.posX+x,self.posY+y
                cZ = self.perlin.get_value(cX,cY)
                tree = self.posX%16 == 0 and self.posY%16 == 0
                for z in range(CHUNK_SIZE):
                    index = self.tupleToIndex((x,y,z))
                    gZ = self.posZ+z

                    if tree and gZ>cZ and gZ<=cZ+3 and (x==1 and y==1):
                        self.voxels[index] = 4

                    elif tree and gZ>cZ+3 and gZ<cZ+6 and (x<3 and y<3):
                        self.voxels[index] = 5

                    elif gZ<cZ : # below surface
                        self.voxels[index] = 1

                    elif gZ==cZ : # surface
                        self.voxels[index] = 2                   

                    if randint(1,11) == 1 and (gZ<=cZ+1 and x!=0 and y != 0 and x!=CHUNK_SIZE-1 and y!=CHUNK_SIZE-1 and z!=0 and (z!=CHUNK_SIZE-1 or gZ>cZ)):
                       self.voxels[index] = 3
                        


    def printPlane(self,plane):
        s = "{} "*CHUNK_SIZE
        for y in range(CHUNK_SIZE):
            row = []
            for x in range(CHUNK_SIZE):
                T = plane[x+y*CHUNK_SIZE]
                if T ==  IGNORE_BLOCK: T = '.'
                row.append( T )
            print( s.format(*row))
        print()

    def minimize(self,faces,plane,orientation):

        
        hMap = [None]*CHUNK_AREA    
        

        visited = set()
        result = [0]*(CHUNK_SIZE * 8) 

        count = 0
        
        for i in range(CHUNK_AREA):
                     
            T = plane[i] 
            if i in visited: continue
            if  T==0 or T==IGNORE_BLOCK : continue
            if  T<=0: continue

            result[0] = 0

            self.cut(i,plane,visited,result)

            y = i//CHUNK_SIZE
            x = i-y*CHUNK_SIZE
            

            for k in range(1,result[0]+1):
                di = result[k]

                cy = di//CHUNK_SIZE
                cx = di-cy*CHUNK_SIZE                

                A = [min(x,cx),min(y,cy)]
                B = [max(x,cx)+1,max(y,cy)+1]
                SIZE = (B[0]-A[0])*(B[1]-A[1])
                for dx in range(A[0],B[0]):
                    for dy in range(A[1],B[1]):
                        wipeIndex = dx+dy*CHUNK_SIZE
                        visited.add(wipeIndex)

                        last = hMap[wipeIndex]
                        if not last or last[0]<SIZE:
                            hMap[wipeIndex] = (SIZE,T,A[0],A[1],B[0],B[1])   
                            count += int(not last)

            #if count >= CHUNK_AREA:
                # print(i,count)
                #break

        visited = set()
        for face in hMap:
            if face and not face in visited:
                visited.add(face)
                T = face[1]
                H = max(orientation)
                A = list(face[2:4])+[H]
                C = list(face[4:6])+[H]
                B = [C[0],A[1],H]
                D = [A[0],C[1],H]

                if orientation[2]!=-1: #up-down 
                    rotated = (T,A,B,C,D,(0,0,1))
                if orientation[0]!=-1: #left-right 
                    A = [A[2],A[1],A[0]]
                    B = [B[2],B[1],B[0]]
                    C = [C[2],C[1],C[0]]
                    D = [D[2],D[1],D[0]]
                    rotated = (T,D,C,B,A,(1,0,0))

                if orientation[1]!=-1: #back-front 
                    A = [A[0],A[2],A[1]]
                    B = [B[0],B[2],B[1]]
                    C = [C[0],C[2],C[1]]
                    D = [D[0],D[2],D[1]]
                    rotated = (T,A,B,C,D,(0,-1,0))

                faces.append(rotated)

    def cut(self,index,plane,visited,result):  


        T = plane[index]

        Y = index // CHUNK_SIZE
        X = index - Y*CHUNK_SIZE

        for dirX in [-1,1]:
            for dirY in [-1,1]:

                lastDelta   = CHUNK_SIZE + 16
                lastSize    = result[0]
                currentSize = lastSize
                
                x = X
                while x!=-1 and x!=CHUNK_SIZE:
                   
                    if plane[x+Y*CHUNK_SIZE]  not in (T,IGNORE_BLOCK) or x+Y*CHUNK_SIZE in visited:
                        break
                   
                    y = Y+dirY
                    while True:
                        di = x+y*CHUNK_SIZE
                        if y == lastDelta or y == -1 or y == CHUNK_SIZE or di in visited or plane[di] not in [T,IGNORE_BLOCK]:

                            currentIndex = di - CHUNK_SIZE*dirY
                            if (y == lastDelta and currentSize != lastSize): # // same height
                                result[currentSize] = currentIndex
                           
                            else:
                                result[0]+=1
                                currentSize+=1
                                result[currentSize] = currentIndex
                            
                            lastDelta = y
                            break
                        y += dirY
                    x += dirX

        # return result            
    def generateFacesByStep(self,index):
        if index ==0:

            self.faces = []  
        planeDir = index//(CHUNK_SIZE+1)
        A = index - planeDir*(CHUNK_SIZE+1)

        # plane = [0]*CHUNK_AREA
        # planeTemp = self.voxels.planes[planeDir][A]
        # for i in range(CHUNK_AREA):
        #     plane[i] = planeTemp[i]
        plane = self.voxels.planes[planeDir][A]

        if planeDir==0:
            self.minimize(self.faces,plane,(-1,-1,A))
        if planeDir==1:
            self.minimize(self.faces,plane,(A,-1,-1))
        if planeDir==2:
            self.minimize(self.faces,plane,(-1,A,-1))

    def generateFaces(self):
        self.faces = []  


        for A in range(CHUNK_SIZE+1):
            for planeDir in range(3):

                plane = self.voxels.planes[planeDir][A]
                # planeTemp = self.voxels.planes[planeDir][A]
                # for i in range(CHUNK_AREA):
                #     plane[i] = planeTemp[i]

                if planeDir==0:
                    self.minimize(self.faces,plane,(-1,-1,A))
                if planeDir==1:
                    self.minimize(self.faces,plane,(A,-1,-1))
                if planeDir==2:
                    self.minimize(self.faces,plane,(-1,A,-1))


if __name__ == '__main__':
    
    c = Chunk(0,0,CHUNK_SIZE*10)

    from ctypes import *
    class POINT(Structure):
        _fields_ = [("val", c_int8)]

    POINTS = POINT*(32**3)
    t = time()
    array = POINTS()
    # array = [POINT(0)]*(32**3)
    print( time()-t)
    print(array[0].val)
    array[33].val = 123
    print(array[2].val)


    t = time()
    array = [Voxel(0) for i in range(32**3)]
    print( time()-t)

    t = time()
    array = [0]*(32**3)
    print( time()-t)

    mem = c_int8*(32**3)
    t = time()
    
    array = mem()
    # array2 = [poiner(i) for i in array]

    print( time()-t)



