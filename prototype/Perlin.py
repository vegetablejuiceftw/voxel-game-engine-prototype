import random
from math import floor, radians, cos, sin


class Noise:
    def __init__(self, grid_size, seed):
        self.grid_size = grid_size
        self.seed = seed
        self.perm_size = 256

        perm = list(range(self.perm_size))
        random.seed(self.seed)

        random.shuffle(perm)
        perm += perm
        random_vectors = []
        len_of_vectors = 16
        rounding = 4

        for x_vector in range(len_of_vectors):
            for y_vector in range(len_of_vectors):
                random_vectors.append((round(x_vector / (len_of_vectors - 1) - 0.5, rounding),
                                       round(y_vector / (len_of_vectors - 1) - 0.5, rounding)))

        random.shuffle(random_vectors)

        def rotate(self, theta):
            theta = radians(theta)
            for vector_index in range(len(self.random_vectors)):
                theta *= -1
                vect = self.random_vectors[vector_index]
                x, y = vect[0], vect[1]
                cs = cos(theta)
                sn = sin(theta)
                px = x * cs - y * sn
                py = x * sn + y * cs
                self.random_vectors[vector_index] = (px, py)

        self.perm = perm
        self.random_vectors = random_vectors
        self.len_of_vectors = len_of_vectors ** 2

    def get_value(self, x, y):

        cx = x / self.grid_size
        cy = y / self.grid_size
        ix, iy = floor(cx), floor(cy)
        perm_size = self.perm_size

        def corner(corner_x, corner_y):
            px = ix + corner_x
            py = iy + corner_y

            dx, dy = abs(cx - px), abs(cy - py)

            poly_x = 1 - 6 * dx ** 5 + 15 * dx ** 4 - 10 * dx ** 3
            poly_y = 1 - 6 * dy ** 5 + 15 * dy ** 4 - 10 * dy ** 3

            hashed = self.perm[self.perm[abs(px) % perm_size] + abs(py) % perm_size]

            vector = self.random_vectors[hashed % self.len_of_vectors]

            scalar = (cx - px) * vector[0] + (cy - py) * vector[1]

            return poly_x * poly_y * scalar

        return int((((corner(0, 0) + corner(1, 0) + corner(0, 1) + corner(1, 1)) * 16 + 16) / 1.3) * 1.3)
