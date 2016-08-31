'''
@author: Merijn de Bakker, Utrecht University 2016
'''


def initialize(setup):
    setup.initialize(1)
    print 'model initialized'


def run(model, nr_of_timesteps):
    print 'model running for', nr_of_timesteps, 'timesteps'
    print 'model running ...'

    model.run(nr_of_timesteps)


# for future use
def finalize():
    print 'model finished'
