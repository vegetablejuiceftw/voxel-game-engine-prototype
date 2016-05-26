from random import shuffle,random

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

    def isHungry(self):
        return self.hunger > 50

    def isTired(self):
        return self.energy < 20

    def isRested(self):
        return self.energy > 70

    def isHealthy(self):
        return self.health > 90

    def canFight(self):
        return self.health > 30

    def inDanger(self):
        return bool(self.danger)

    def hasFood(self):
        return self.getFood()

    def eat(self):
        food = self.getFood()
        if food:
            food.die()
            self.hunger = max(self.hunger - 20, 0)

    def regenerate(self):

        self.energy = min(self.energy+1,100)
        self.health = min(self.health+1,100)

        if self.hunger < 50 and (self.energy < 90 or self.health < 90):
            self.energy = min(self.energy+2,100)
            self.health = min(self.health+2,100) 
            self.hunger = min(self.hunger+2,100)

        else:
            self.hunger = min(self.hunger+0.5,100)

     
    def explore(self):
        if not self.isTired():
            if self.pathing:
                next(self.pathing)   

    def walkExpend(self):
        self.energy = max(self.energy-3,0)


        
    def sufferDamage(self,damage,cause):
        self.health = max(self.health-damage,0)

    def __str__(self):
        return "(hunger {}) (health {}) (energy {}) (danger {})".format(self.hunger,self.health,self.energy,self.danger)

    def status(self):
        return "{}\nhunger {}\nhealth {}\nenergy {}\ndanger {}".format(self.state.__class__.__name__,self.hunger,self.health,self.energy,self.danger)


class StateNode:
    def __init__(self,actor):
        self.transitions = dict(self.exctract_transistions())
        self.actor = actor
        # print(self.transitions)

    def exctract_transistions(self):
        return [i for i in self.__class__.__dict__.items() if 'VEC' in i[0] ]

    def transition(self):        
        for name, vector in self.transitions.items():
            result = vector(self)
            if result:
                print('\n',name,'->',result.__class__.__name__)
                return result
        return self

    def animate(self):
        print("I exist")

    def tick(self):
        self.animate()
        return self.transition()


class EatState(StateNode):
    def animate(self):
        #("I Eat")
        self.actor.eat()
        self.actor.regenerate()

    def VEC_NO_FOOD(self):
        actor = self.actor
        if not actor.hasFood():
            return ExploreState(actor)

    def VEC_ATTACKED(self):
        actor = self.actor
        if actor.inDanger():
            if not actor.canFight():
                return ExploreState(actor)
            else:
                print('should fight')

class IdleState(StateNode):
    def animate(self):
        #("I rest")
        self.actor.regenerate()

    def VEC_FOOD(self):
        actor = self.actor
        if actor.hasFood() and actor.isHungry():
            return EatState(actor)

    def VEC_ATTACKED(self):
        actor = self.actor
        if actor.inDanger():
            if not actor.canFight():
                return ExploreState(actor)
            else:
                print('should fight')

    def VEC_RESTED_AND_HUNGRY(self):
        actor = self.actor
        if actor.isRested() and actor.isHungry():
            return ExploreState(actor)

class ExploreState(StateNode):

    def __init__(self, actor):
        super(ExploreState, self).__init__(actor)
        self.actor.pathing = self.actor.travel() 

    def animate(self):
        #("I explr")        
        self.actor.regenerate()
        self.actor.explore()


    def VEC_FOOD_AND_HUNGRY(self):
        actor = self.actor
        if actor.isHungry() and actor.hasFood():
            return EatState(actor)

    def VEC_TIRED(self):
        if self.actor.isTired():
            return IdleState(self.actor)

    def VEC_LAZY(self):
        if not self.actor.isHungry():
            return IdleState(self.actor)

    def VEC_ATTACKED(self):
        actor = self.actor
        if actor.inDanger():
            if not actor.canFight():
                return ExploreState(actor)
            else:
                print('should fight')


class ClassName(object):
    """docstring for ClassName"""
    def __init__(self, arg):
        super(ClassName, self).__init__()
        self.arg = arg
        

# actor = AnimusAlpha('Dummy')

# for i in range(30):

#     actor.tick()
#     print(actor)
