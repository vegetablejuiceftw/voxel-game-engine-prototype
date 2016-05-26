from time import time
import heapq
import random
try:
    from mathutils import Vector
except:
    from vector import Vector

def shortest_path(startState, limit=10**5):

    def toPath(end,path):
        path.append(end)
        index = end[-1]
        if index != -1:
            return toPath(parents[index],path)
        return path
    
    start       = startState
    q           = [  (0,start)  ]    
    stateDict   = {}
    parents     = []
    pIndex      = 0

    for count in range(limit):
        F, node    = heapq.heappop(q) 
        key = node.to_tuple()
        cost    = key[0]
        oldCost = stateDict.get(key,999090)
        if oldCost<=cost:
            continue
        stateDict[ key ] = cost
        parents.append(key)
        
        if min(key) >=0 :#?isfinal
            print( "effort size", count )
            return toPath(node,[])      
        
        for action in actionList:    
            for x,y in zip(node,action):
                if x<0 and y>0 :        
                    childNode = node+action  
                    childNode[-1]   = pIndex

                    G = childNode[0]
                    H = sum(-i for i in childNode if i<0) * 10
                    F = G + H
                    heapq.heappush(q,(F,childNode)  )
                    break
        pIndex+=1
    print( "effort size", count )
    return []

# cost, cake, milk, egg, flour,sword
actionList = [
 Vector([2, 1,-1,-1,-1, 0]) # bake cake
,Vector([1, 0, 1, 0, 0, 0]) # get milk
,Vector([1, 0, 0, 1, 0, 0]) # get egg
,Vector([1, 0, 0, 0, 1, 0]) # get flour
,Vector([1,-1, 0, 0, 0, 0]) # eat cake 
,Vector([1, 0, 0, 0, 0, 1]) # take a sword
,Vector([2, 0, 0, 0, 0, 4]) # take a dozen swords
]
 
# state is cost, cake, milk, egg, flour, sword, Parent

def main():

    t = time()

    state = Vector([0, 0, 2, 5, 0, 0, -1])
    query = Vector([0, 3, 0, 0, 0, 3])
    startState = state - query

    print('State {}\nQuery {}\nstartState {}'.format(state,query,startState))

    
    result = shortest_path(startState,limit = 10**6)

    # print the result
    last = startState
    steps = []
    for action in reversed(result):
        action = Vector(action)
        dif = last - action
        steps.append(dif)
        print(action,dif)
        last = action
    

    print(state)
    for action in reversed(steps):
        state += action
        print(state[:-1])

    print( time()-t,'sec or',round((time()-t)*1000),'ms')
if __name__ == '__main__':
    main()

