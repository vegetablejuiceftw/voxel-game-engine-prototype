from Chunk import *
from bge import logic,events
from mathutils import Vector
from time import time
from random import random,shuffle
from math import floor,sin
from work import *
from npc import Sheep, initNPC

scene = logic.getCurrentScene()
cont = logic.getCurrentController()
own = cont.owner
logic.counter = 0
logic.faceCounter = 0

MAP_SIZE = 5


def createUniqueMesh(request_size, position):
    obj = scene.addObject("Cube{}".format(CHUNK_SIZE),own)
    obj.worldPosition = position
    obj.replaceMesh(newMesh(request_size),True) 
    return obj

def resizeMesh(obj,request_size):
    obj.replaceMesh(newMesh(request_size),True) 

def newMesh(request_size):
    sizes= [32,64,96,128,192,256,384,512,768]
    size = next(x for x in sizes if x>request_size)
    logic.counter +=  1
    pre = logic.LibNew("GEN_"+str(time()+random()+ logic.counter ), "Mesh", ["Donor"+str(size)])
    handle = pre[0].name
    return handle


def draw(chunk,faces):    

    # if chunk.obj == None:
    #     chunk.obj = createUniqueMesh(len(chunk.faces),chunk.pos)
    obj = chunk.obj


    mesh = obj.meshes[0] 

    faceCount = len(faces)
    currentFaces = mesh.numPolygons
    if (faceCount>currentFaces or (faceCount<=currentFaces/2.2 and faceCount>=16)):
        resizeMesh(obj,faceCount)
        print("resize0",faceCount,currentFaces,obj.meshes[0].numPolygons)
    mesh = obj.meshes[0]
    
    for index in range(faceCount):
        T, A, B, C, D, N = faces[index]                    

        face = [A,B,C,D]                                        

        for v_index in range(4):
            vertex = mesh.getVertex(0, index*4+v_index)
            
            vertex.setXYZ(face[v_index])  
            if T == 1:
                c = list(COLORS[T])
                c[1] = c[1]/2 + abs(sin(vertex.z)/2)*0.25 + 0.12
                vertex.color = c
            else:
                vertex.color = COLORS[T]            

            vertex.setNormal(N)

    for index in range(faceCount,mesh.numPolygons):        
        
        for v_index in range(4):
            vertex = mesh.getVertex(0, index*4+v_index)
            if vertex.z < -10:
                index = None
                break
            else:
                vertex.setXYZ( (0,0,-99) )
        if index==None: break

    #obj.reinstancePhysicsMesh()

def main():

    import os
    os.system("cls")

    START = time()

    logic.chunks = ChunkManager(createUniqueMesh,draw)

    logic.work = []

    R = MAP_SIZE

    FACE_COUNT = 0
    VOXEL_COUNT = 0
    CHUNK_COUNT = 0

    MAX_TIME = 0
    for cX in range(-R*CHUNK_SIZE,(R+1)*CHUNK_SIZE,CHUNK_SIZE):
        for cY in range(-R*CHUNK_SIZE,(R+1)*CHUNK_SIZE,CHUNK_SIZE):
            for cZ in range(-CHUNK_SIZE*0,CHUNK_SIZE*8,CHUNK_SIZE):                

                # c = logic.chunks[(cX,cY,cZ)] 
                cTime = time()
                c = logic.chunks.initChunk((cX,cY,cZ))
                MAX_TIME = max( (time()-cTime), MAX_TIME)
                
                logic.faceCounter += (len(c.faces))
                VOXEL_COUNT += len(c)
                FACE_COUNT += len(c.faces)
                if len(c):
                    CHUNK_COUNT += 1

                    # print(len(c.faces)/len(c))


        print(logic.faceCounter,VOXEL_COUNT)
    
    print(logic.faceCounter)
                   
    print( "FULL time ",time()-START , 'sec', 'MAX_TIME of 1 chunk',MAX_TIME)
    print( 'FACE_COUNT',FACE_COUNT,' VOXEL_COUNT', VOXEL_COUNT,' CHUNK_COUNT' ,CHUNK_COUNT,)

def inputEvents(cont):

    if not cont.sensors['Always'].positive:
        return

    own     = cont.owner
    mouse       = logic.mouse
    keyboard    = logic.keyboard
    JUST_ACTIVATED = logic.KX_INPUT_JUST_ACTIVATED

    move(cont)
    if mouse.events[events.RIGHTMOUSE] == JUST_ACTIVATED:    
        build(cont)
    if mouse.events[events.LEFTMOUSE] == JUST_ACTIVATED:    
        blast(cont)  
    if mouse.events[events.MIDDLEMOUSE] == JUST_ACTIVATED:    
        mark(cont)  

    # print(cont.sensors,cont.sensors['Always'].positive,cont.sensors['Over'].positive)
    if mouse.events[events.WHEELUPMOUSE] :    
        logic.RADIUS = min(10,logic.RADIUS+0.15)
    if mouse.events[events.WHEELDOWNMOUSE] :    
        logic.RADIUS = max(0,logic.RADIUS-0.15)
    
    if not own.get('select'):
        own['select'] = 1
    if keyboard.events[events.F1KEY]:
        own['select'] = 1
    if keyboard.events[events.F2KEY]:
        own['select'] = 2
    if keyboard.events[events.F3KEY]:
        own['select'] = 3

    logic.BLAST_DELTA = blastSphere((logic.RADIUS))
    own     = cont.owner
    own['radious'] = logic.RADIUS

    
def move(cont):
    own     = cont.owner
    keyboard = logic.keyboard
    JUST_ACTIVATED = logic.KX_INPUT_JUST_ACTIVATED

    SPEED = 0.3
    if keyboard.events[events.LEFTSHIFTKEY]:  
        SPEED *= 9
    if keyboard.events[events.WKEY]:        
        own.applyMovement((0,0,-SPEED),True)
    if keyboard.events[events.SKEY]:
        own.applyMovement((0,0,SPEED),True)
    if keyboard.events[events.AKEY]:
        own.applyMovement((-SPEED,0,0),True)
    if keyboard.events[events.DKEY]:
        own.applyMovement((SPEED,0,0),True)
    if keyboard.events[events.SPACEKEY]:
        own.applyMovement((0,0,SPEED),False)

def generateBlockRay(start, vector, distance):  
    dx,dy,dz = vector
    start = Vector(start)
    pos = Vector(start)
    positions = []

    while (pos-start).length < distance:

        x,y,z = pos
        x,y,z = x-floor(x),y-floor(y),z-floor(z)

        x = x if dx<0 else 1-x
        y = y if dy<0 else 1-y
        z = z if dz<0 else 1-z

        x += 0.001
        y += 0.001
        z += 0.001

        if dx!=0:
            vx = pos+vector*abs(x/dx)
            positions.append( vx )
        if dy!=0:    
            vy = pos+vector*abs(y/dy)
            positions.append( vy )
        if dz!=0:
            vz = pos+vector*abs(z/dz)
            positions.append( vz )       

        pos += vector

        # print(pos,vector)   
    
    positions = sorted(positions,key = lambda x: (start-x).length)  

    
    result = []
    visited = set()
    last = None
    for V in positions:
        newPos = (floor(V[0]),floor(V[1]),floor(V[2])) 
        if newPos in visited: 
            continue        
        if result and (last-Vector(newPos)).length > 1.8: # bigger than cube diagonal
            continue
        visited.add(newPos)
        result.append(newPos)
        last = Vector(newPos)
   
    return result

def checkRay(checkPos):
    chunkKey = tupleToChunkKey(checkPos)
    chunk = logic.chunks.get(chunkKey)
    
    if chunk:
        localPos = flooredTuple(Vector(checkPos)-Vector(chunkKey))

        voxelIndex = tupleToIndex(localPos)
        if chunk.voxels[voxelIndex]:
            return (chunk,voxelIndex)
        return(chunk,None)
    return (None,None)

def blastSphere(R):
    casuality = []
    bR = int(R)
    for x in range(-bR,bR+1):
        for y in range(-bR,bR+1):
            for z in range(-bR,bR+1):
                v = Vector((x,y,z))
                # if v.length <= R:
                casuality.append(v)
    return casuality




def getRayHit(position,direction):
    # chunk TODO
    if not direction.length:
        return
    pos = Vector(position)
    
    cubes = generateBlockRay(pos,direction,10)
    last = cubes[0]
    for index in range(500):
   
        if len(cubes)==index:
            pos += direction * 9
            cubes += generateBlockRay(pos,direction,10)

        newPos = cubes[index]

        chunk, voxel =  logic.chunks.checkRay(newPos)
        normal = Vector(last)-Vector(newPos)
        last = newPos
        if voxel and voxel.val:
            return (chunk,voxel,newPos,normal)

    return (None,None,None,None)


def blast(cont):    
    own         = cont.owner
    direction   = cont.sensors["Over"].rayDirection
    position    = Vector(own.worldPosition)     
    if  not direction.length:
        return
    chunk, voxel, hitPos,normal = getRayHit(position,direction)
    if voxel:
        if own.get('select') == 1:
            logic.work.append(ChangeWork(Vector(hitPos),0))
        elif own.get('select') == 2:
            logic.work.append(RemoveWork(hitPos,0))
        elif own.get('select') == 3:
            _, voxel    =  logic.chunks.checkRay(Vector(hitPos)+normal)
            if voxel.NPC:
                voxel.NPC.die()

def build(cont):    
    own         = cont.owner
    direction   = cont.sensors["Over"].rayDirection
    position    = Vector(own.worldPosition) 
    if  not direction.length:
        return 
    chunk, voxel, hitPos,normal = getRayHit(position,direction)
    if voxel:
        if own.get('select') == 1:
            logic.work.append(ChangeWork(Vector(hitPos)+normal*logic.RADIUS,3))
            
        elif own.get('select') == 2:
            logic.work.append(RemoveWork(Vector(hitPos)+normal,4))
        elif own.get('select') == 3:
            freePos = Vector(hitPos)+normal
            obj = scene.addObject('Sheep','Npc_manager')
            obj.worldPosition = freePos
            





def mark(cont):
    own         = cont.owner
    direction   = cont.sensors["Over"].rayDirection
    position    = Vector(own.worldPosition) 
    if  not direction.length:
        return 
    chunk, voxel, hitPos,normal = getRayHit(position,direction)
    if voxel:        
        logic.marker = Vector(hitPos)+normal
        print('marker',logic.marker,chunk.pos)

def filterManager(cont):
    try:
        logic.shaders
    except:
        logic.shaders = {1:False,2:False,3:False,4:False}
    shaders = logic.shaders    

    keyboard = logic.keyboard
    JUST_ACTIVATED = logic.KX_INPUT_JUST_ACTIVATED

    for i,keyEvent in enumerate([events.ONEKEY,events.TWOKEY,events.THREEKEY,events.FOURKEY]):

        if keyboard.events[keyEvent] == JUST_ACTIVATED:
            key = i+1
            if not shaders[key]: 
                cont.activate('F'+str(key))
            else:
                cont.activate('R'+str(key))
            shaders[key] = not shaders[key]
