'''
@author: Merijn de Bakker, Utrecht University 2016
'''

from mapalgebra.mapalgebra import read, write, gaussian_move, maximum, minimum, \
        window, create_image

grass_datapath = '../data/grass.hdf5'
cows_datapath = '../data/cows.hdf5'


def run(nr_of_timesteps):

    growth_rate = 0.02
    carrying_capacity = 10.0
    d = 0.01

    grass = read(grass_datapath)
    cows = read(cows_datapath)

    grass.area.nr_neighbours = window(grass.area.biomass, 'count', 'manhattan')

    create_image(grass.area.biomass, cows.location, 0)

    for t in range(1, nr_of_timesteps):

        grass.area.capacity = 1 - grass.area.biomass / carrying_capacity
        grass.area.growth = grass.area.capacity * growth_rate * \
                grass.area.biomass
        grass.area.biomass = grass.area.biomass + grass.area.growth

        grass.area.diffusion = d * (window(grass.area.biomass, 'sum',
                                           'manhattan') -
                                    grass.area.nr_neighbours *
                                    grass.area.biomass)

        grass.area.biomass = grass.area.biomass + grass.area.diffusion

        grass.area.biomass = maximum(0.01, grass.area.biomass -
                                    (cows.location.weight * 0.0008))

        grass.area.enough_food = grass.area.biomass > 0.5

        cows.location.weight = minimum(750, cows.location.weight * 1.003)

        cows.location = gaussian_move(cows.location, grass.area.enough_food, 30)

        create_image(grass.area.biomass, cows.location, t)

        write(grass, grass_datapath, t)
        write(cows, cows_datapath, t)

if __name__ == "__main__":
    run(100)
