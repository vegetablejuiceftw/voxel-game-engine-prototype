from time import time
import heapq

try:
    from mathutils import Vector
except:
    from vector import Vector


def shortest_path(start_state, limit=10 ** 5):
    def to_path(end, path):
        path.append(end)
        index = end[-1]
        if index != -1:
            return to_path(parents[index], path)
        return path

    start = start_state
    q = [(0, start)]
    state_dict = {}
    parents = []
    p_index = 0

    for count in range(limit):
        F, node = heapq.heappop(q)
        key = node.to_tuple()
        cost = key[0]
        old_cost = state_dict.get(key, 999090)
        if old_cost <= cost:
            continue
        state_dict[key] = cost
        parents.append(key)

        if min(key) >= 0:
            print("effort size", count)
            return to_path(node, [])

        for action in actionList:
            for x, y in zip(node, action):
                if x < 0 < y:
                    child_node = node + action
                    child_node[-1] = p_index

                    G = child_node[0]
                    H = sum(-i for i in child_node if i < 0) * 10
                    F = G + H
                    heapq.heappush(q, (F, child_node))
                    break
        p_index += 1
    print("effort size", count)
    return []


# cost, cake, milk, egg, flour,sword
actionList = [
    Vector([2, 1, -1, -1, -1, 0]),  # bake cake
    Vector([1, 0, 1, 0, 0, 0]),  # get milk
    Vector([1, 0, 0, 1, 0, 0]),  # get egg
    Vector([1, 0, 0, 0, 1, 0]),  # get flour
    Vector([1, -1, 0, 0, 0, 0]),  # eat cake
    Vector([1, 0, 0, 0, 0, 1]),  # take a sword
    Vector([2, 0, 0, 0, 0, 4])  # take a dozen swords
]

# state is cost, cake, milk, egg, flour, sword, Parent

if __name__ == '__main__':
    t = time()

    state = Vector([0, 0, 2, 5, 0, 0, -1])
    query = Vector([0, 3, 0, 0, 0, 3])
    start_state = state - query

    print('State {}\nQuery {}\nstart_state {}'.format(state, query, start_state))

    result = shortest_path(start_state, limit=10 ** 6)

    # print the result
    last = start_state
    steps = []
    for action in reversed(result):
        action = Vector(action)
        dif = last - action
        steps.append(dif)
        print(action, dif)
        last = action

    print(state)
    for action in reversed(steps):
        state += action
        print(state[:-1])

    print(time() - t, 'sec or', round((time() - t) * 1000), 'ms')
