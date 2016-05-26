import random
import heapq
import math
from math import tanh
#13.10.2013 ~~2.00
random.seed("derp")

class Vector:
    def __init__(self,x,y):
        self.x = x
        self.y = y

def dtanh(y):
    return 1.0-y*y

class Node:
    def __init__(self):        
        self.input      = 0
        self.error      = 0.5
        self.pathD      = {}
        self.pathU      = {}
 
    def connect(self,other):
        # have a weight vector with bias
        v                    = Vector(random.random()*2-1,random.random()-0.5)
        self.pathD[other]    = v
        other.pathU[self]    = v      
    
    def getFlow(self):
        # get from all left nodes input*weigh -> this
        buffer      = 0
        for node,weigh in self.pathU.items():            
            buffer += node.input * weigh.x + weigh.y
        self.input  = tanh(buffer)        
    
    def getErrorFlow(self):
        # propagate error from right to left 
        buffer      = 0
        for rightNode,weigh in self.pathD.items():            
            buffer += rightNode.error       * weigh.x 
        self.error  = dtanh(self.input )    * buffer        

    def setFlow(self,N = 0.135):
        for leftNode,weigh in self.pathU.items():  
            change      = self.error*leftNode.input
            weigh.x    += N*change

class Net:
    def __init__(self):
        self.net        = []
        self.dataset    = []

    def create(self,layers):
        nodes = [[Node() for n in range(size)] for size in layers]        
        for layerIndex in range(len(nodes)-1):
            thisLayer   =   nodes[layerIndex]
            nextLayer   =   nodes[layerIndex+1]
            for node in thisLayer:
                for child in nextLayer:
                    node.connect(child)
        self.net = nodes
        return self.net
   
    def think(self,input):
        net     = self.net          

        for leftNode,val in zip(net[0],input):
            leftNode.input  = val 

        # input is asked from one layer up/left
        for layer in net[1:]:
            for rightNode in layer:
                rightNode.getFlow()

        return [ rightNode.input for rightNode in  layer ]


    def learn(self,expected):
        net     = self.net
        # inital error calc
        for node,e in zip(net[-1],expected):
            error       = e-node.input       
            node.error  = dtanh(node.input)*error

        # propagete the error from down to up / right to left
        for layer in reversed(net[1:-1]):
            for rightNode in layer:
                rightNode.getErrorFlow()

        # propagete the changing from down to up / right to left
        for layer in reversed(net[1:]):
             for rightNode in layer:
                rightNode.setFlow()

    def immerse(self,examples,escapeFactor=1000,limit = 25000):
        self.dataset   += examples
        dataset         = self.dataset
        datasetLen      = len(dataset)
        escape          = datasetLen*escapeFactor

        
        for i in range(int(limit/2)):
            caseR    = random.choice(dataset)
            caseI    = dataset[ i % datasetLen ]

            for inp,out in [caseR,caseI]:

                res = brain.think(inp) 
                dif = [1 for a, b in zip(out, res) if a!=int(round(b,0))]  

                if not len(dif): win+=1
                else:            win =0

                brain.learn(out)
            if not i*2 % 500:   print( i*2 )
            if win>escape:
                print( i*2 )
                return True

        else:
            return False
    

def xo(arr,string=""):     
    for i in arr:
        string += ["-","o","x"][int(round(i,0))]
    return string


cases = [[(1,1),[-1]],[(1,-1),[1]],[(-1,1),[1]],[(-1,-1),[-1]]]

cases = []
for A in [0,1]:
    for B in [0,1]:
        for C in [0,1]:
            val = A and B or ( C and not( A and not B))
            cases.append( [ (A,B,C),(int(val)*2-1,  (int(  (val+1)%2  + int(C) )%2 )*2-1    )   ]   )
         

print("tere")
brain = Net()
sA,sB = len(cases[0][0]), len(cases[0][1])
brain.create([sA,5,sB])

brain.immerse(cases)

for i in range(1):
    for case in cases:
        
        inp,out = case
        res = brain.think(inp)          
        
        print(inp, xo(out),xo(res))
      
        print()