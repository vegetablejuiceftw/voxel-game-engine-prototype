import random
from math import tanh

random.seed("13.10.2013 ~~2.00")


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def dtanh(y):
    return 1.0 - y ** 2


class Node:
    def __init__(self):
        self.input = 0
        self.error = 0.5
        self.path_down = {}
        self.path_up = {}

    def connect(self, other):
        # have a weight vector with bias
        v = Vector(random.random() * 2 - 1, random.random() - 0.5)
        self.path_down[other] = v
        other.path_up[self] = v

    def get_flow(self):
        # get from all left nodes input*weigh -> this
        buffer = 0
        for node, weigh in self.path_up.items():
            buffer += node.input * weigh.x + weigh.y
        self.input = tanh(buffer)

    def get_error_flow(self):
        # propagate error from right to left 
        buffer = 0
        for right_node, weigh in self.path_down.items():
            buffer += right_node.error * weigh.x
        self.error = dtanh(self.input) * buffer

    def set_flow(self, factor=0.135):
        for left_node, weigh in self.path_up.items():
            change = self.error * left_node.input
            weigh.x += factor * change


class Net:
    def __init__(self):
        self.net = []
        self.dataset = []

    def create(self, layers):
        nodes = [[Node() for _ in range(size)] for size in layers]
        for layer_index in range(len(nodes) - 1):
            this_layer = nodes[layer_index]
            next_layer = nodes[layer_index + 1]
            for node in this_layer:
                for child in next_layer:
                    node.connect(child)
        self.net = nodes
        return self.net

    def think(self, args):
        net = self.net

        for left_node, val in zip(net[0], args):
            left_node.input = val

            # input is asked from one layer up/left
        for layer in net[1:]:
            for right_node in layer:
                right_node.get_flow()

        return [right_node.input for right_node in layer]

    def learn(self, expected):
        net = self.net
        # inital error calc
        for node, e in zip(net[-1], expected):
            error = e - node.input
            node.error = dtanh(node.input) * error

        # propagate the error from down to up / right to left
        for layer in reversed(net[1:-1]):
            for right_node in layer:
                right_node.get_error_flow()

        # propagate the changing from down to up / right to left
        for layer in reversed(net[1:]):
            for right_node in layer:
                right_node.set_flow()

    def immerse(self, examples, escape_factor=1000, limit=25000):
        self.dataset += examples
        dataset = self.dataset
        dataset_len = len(dataset)
        escape = dataset_len * escape_factor

        for i in range(int(limit / 2)):
            case_r = random.choice(dataset)
            case_i = dataset[i % dataset_len]

            for inp, out in [case_r, case_i]:

                res = brain.think(inp)
                dif = [1 for a, b in zip(out, res) if a != int(round(b, 0))]

                if not len(dif):
                    win += 1
                else:
                    win = 0

                brain.learn(out)
            if not i * 2 % 500:
                print(i * 2)
            if win > escape:
                print(i * 2)
                return True
        else:
            return False


def xo(arr, string=""):
    for i in arr:
        string += ["-", "o", "x"][int(round(i, 0))]
    return string


cases = [[(1, 1), [-1]], [(1, -1), [1]], [(-1, 1), [1]], [(-1, -1), [-1]]]

cases = []
for A in [0, 1]:
    for B in [0, 1]:
        for C in [0, 1]:
            val = A and B or (C and not (A and not B))
            cases.append([(A, B, C), (int(val) * 2 - 1, (int((val + 1) % 2 + int(C)) % 2) * 2 - 1)])

print("tere")
brain = Net()
sA, sB = len(cases[0][0]), len(cases[0][1])
brain.create([sA, 5, sB])

brain.immerse(cases)

for i in range(1):
    for case in cases:
        inp, out = case
        res = brain.think(inp)

        print(inp, xo(out), xo(res))

        print()
