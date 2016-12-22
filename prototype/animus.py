class AnimusAlpha:
    def __init__(self):
        self.hunger = 0
        self.health = 100
        self.energy = 100
        self.danger = None
        self.state = ExploreState(self)
        self.pathing = None

    def tick(self):
        self.state = self.state.tick()

    def is_hungry(self):
        return self.hunger > 50

    def is_tired(self):
        return self.energy < 20

    def is_rested(self):
        return self.energy > 70

    def is_healthy(self):
        return self.health > 90

    def can_fight(self):
        return self.health > 30

    def in_danger(self):
        return bool(self.danger)

    def has_food(self):
        return self.get_food()

    def get_food(self):
        raise NotImplementedError

    def eat(self):
        food = self.get_food()
        if food:
            food.die()
            self.hunger = max(self.hunger - 20, 0)

    def regenerate(self):

        self.energy = min(self.energy + 1, 100)
        self.health = min(self.health + 1, 100)

        if self.hunger < 50 and (self.energy < 90 or self.health < 90):
            self.energy = min(self.energy + 2, 100)
            self.health = min(self.health + 2, 100)
            self.hunger = min(self.hunger + 2, 100)

        else:
            self.hunger = min(self.hunger + 0.5, 100)

    def explore(self):
        if not self.is_tired():
            if self.pathing:
                next(self.pathing)

    def walk_and_expend(self):
        self.energy = max(self.energy - 3, 0)

    def suffer_damage(self, damage, cause):
        self.health = max(self.health - damage, 0)

    def __str__(self):
        return "hunger {} health {} energy {} danger {}".format(self.hunger, self.health, self.energy, self.danger)

    def status(self):
        return "{}\nhunger {}\nhealth {}\nenergy {}\ndanger {}".format(
            self.state.__class__.__name__, self.hunger, self.health, self.energy, self.danger,
        )


class StateNode:
    def __init__(self, actor):
        self.transitions = dict(self.extract_transitions())
        self.actor = actor

    def extract_transitions(self):
        return [vec for vec in self.__class__.__dict__.items() if 'VEC' in vec[0]]

    def transition(self):
        for name, vector in self.transitions.items():
            result = vector(self)
            if result:
                print('\n', name, '->', result.__class__.__name__)
                return result
        return self

    def animate(self):
        raise NotImplementedError

    def tick(self):
        self.animate()
        return self.transition()


class EatState(StateNode):
    def animate(self):
        self.actor.eat()
        self.actor.regenerate()

    def VEC_NO_FOOD(self):
        actor = self.actor
        if not actor.has_food():
            return ExploreState(actor)

    def VEC_ATTACKED(self):
        actor = self.actor
        if actor.in_danger():
            if not actor.can_fight():
                return ExploreState(actor)
            else:
                print('should fight')


class IdleState(StateNode):
    def animate(self):
        self.actor.regenerate()

    def VEC_FOOD(self):
        actor = self.actor
        if actor.has_food() and actor.is_hungry():
            return EatState(actor)

    def VEC_ATTACKED(self):
        actor = self.actor
        if actor.in_danger():
            if not actor.can_fight():
                return ExploreState(actor)
            else:
                print('should fight')

    def VEC_RESTED_AND_HUNGRY(self):
        actor = self.actor
        if actor.is_rested() and actor.is_hungry():
            return ExploreState(actor)


class ExploreState(StateNode):
    def __init__(self, actor):
        super(ExploreState, self).__init__(actor)
        self.actor.pathing = self.actor.travel()

    def animate(self):
        self.actor.regenerate()
        self.actor.explore()

    def VEC_FOOD_AND_HUNGRY(self):
        actor = self.actor
        if actor.is_hungry() and actor.has_food():
            return EatState(actor)

    def VEC_TIRED(self):
        if self.actor.is_tired():
            return IdleState(self.actor)

    def VEC_LAZY(self):
        if not self.actor.is_hungry():
            return IdleState(self.actor)

    def VEC_ATTACKED(self):
        actor = self.actor
        if actor.in_danger():
            if not actor.can_fight():
                return ExploreState(actor)
            else:
                print('should fight')
