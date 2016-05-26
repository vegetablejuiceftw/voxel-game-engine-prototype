import random 
from math import pow
class Noise:
    #Perlin noise
    #read some papers on how it works
    #I barely managed to rotate the vectors
    # and hash negative coords correctly
    def __init__(self, grid_size,SEED):
        self.grid_size = grid_size
        self.SEED = SEED
        self.perm_size = 256
        
        perm = list(range(self.perm_size))
        random.seed(self.SEED)
        
        random.shuffle(perm)
        perm += perm
        random_vectors = []        
        len_of_vectors = 16
        rounding = 4
       
        for x_vector in range(len_of_vectors):
           for y_vector in range(len_of_vectors):
                random_vectors.append((round(x_vector/(len_of_vectors-1)-0.5,rounding),round(y_vector/(len_of_vectors-1)-0.5,rounding)))
        
        random.shuffle(random_vectors)

        def rotate(self,theta):
            theta = math.radians(theta)            
            for vector_index in range(len(self.random_vectors)):
                theta *= -1
                vect = self.random_vectors[vector_index]
                x,y = vect[0],vect[1]
                cs = math.cos(theta)
                sn = math.sin(theta)                
                px = x * cs - y * sn
                py = x * sn + y * cs
                self.random_vectors[vector_index] = (px,py)
                
        self.perm = perm
        self.random_vectors = random_vectors
        self.len_of_vectors = len_of_vectors

    def grid(self,n):
        return int(n/self.grid_size)

    def get_value(self,x,y):
        
        cx = (x/self.grid_size)
        cy = (y/self.grid_size)
        perm_size   =   self.perm_size
        
        
        def corner(corner_x,corner_y):
            
            px          =   int(cx)+corner_x
            py          =   int(cy)+corner_y
            
            if x<0      :   px -= 1
            if y<0      :   py -= 1
                        
            distX, distY = abs((cx)-px), abs((cy)-py)
            
            polyX = 1 - 6*distX**5 + 15*distX**4 - 10*distX**3
            polyY = 1 - 6*distY**5 + 15*distY**4 - 10*distY**3
            
            h_x,h_y = abs(px)%perm_size,abs(py)%perm_size
            
            hashed = self.perm[self.perm[h_x] + h_y]
            
            vector = self.random_vectors[hashed%self.len_of_vectors**2]
            
            scalar = ( ((cx)-px)*vector[0] +  ((cy)-py)*vector[1]  )

            return polyX * polyY * scalar
        
        return int( int( ((corner(0, 0) + corner(1, 0) + corner(0, 1) + corner(1,1))  * 16 * 1.0 + 8) /1.3) * 1.3) 