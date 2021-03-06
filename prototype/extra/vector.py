class Vector:
    def __init__(self, arr):
        self.arr = arr

    def __add__(self, other):
        return self.array_merge(other, 1)

    def __sub__(self, other):
        return self.array_merge(other, -1)

    def array_merge(self, other, sign):
        max_arr, min_arr = (self.arr, other.arr) if len(self.arr) > len(other.arr) else (other.arr, self.arr)
        arr = list(max_arr)
        for i, n in enumerate(min_arr):
            arr[i] += sign * n
        return Vector(arr)

    def __str__(self):
        return "(" + ",".join(" " + str(x) if x >= 0 else str(x) for x in self.arr) + ")"

    def size(self):
        return sum(x ** 2 for x in self.arr) ** 0.5

    def dimension(self):
        return len(self.arr)

    def __hash__(self):
        return hash(tuple(self.arr))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def to_tuple(self):
        return tuple(self.arr)

    def __iter__(self):
        return iter(self.arr)

    def __getitem__(self, i):
        return self.arr[i]

    def __setitem__(self, key, value):
        self.arr[key] = value

    def __len__(self):
        return self.dimension()

    def __lt__(self, other):
        for x, y in zip(self.arr, other.arr):
            if x != y:
                return x < y
        return False


A = Vector([1, 2, 3, 4, 5, 6, 7, 8, 9])
B = Vector([(-1) ** x * x for x in range(9)])

if __name__ == '__main__':
    print(A + B)
