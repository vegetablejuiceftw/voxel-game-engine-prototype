import random
from math import floor


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

        self.perm = perm
        self.random_vectors = random_vectors
        self.len_of_vectors = len_of_vectors ** 2

    def get_value(self, x, y):
        cx = x / self.grid_size
        cy = y / self.grid_size
        ix, iy = floor(cx), floor(cy)
        perm_size = self.perm_size
        len_of_vectors = self.len_of_vectors
        random_vectors = self.random_vectors
        perm = self.perm

        corner_sum = 0
        for px, py in ((ix, iy), (ix + 1, iy), (ix, iy + 1), (ix + 1, iy + 1)):
            dx, dy = abs(cx - px), abs(cy - py)

            poly_x = 1 - 6 * dx ** 5 + 15 * dx ** 4 - 10 * dx ** 3
            poly_y = 1 - 6 * dy ** 5 + 15 * dy ** 4 - 10 * dy ** 3

            hashed = perm[perm[abs(px) % perm_size] + abs(py) % perm_size]

            vx, vy = random_vectors[hashed % len_of_vectors]

            scalar = (cx - px) * vx + (cy - py) * vy

            corner_sum += poly_x * poly_y * scalar

        return int(((corner_sum * 16 + 16) / 1.3) * 1.3)
