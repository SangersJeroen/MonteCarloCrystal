from gettext import find
import numpy as np
import matplotlib.pyplot as plt
from random import uniform, choice
"""global parameters"""
kb = 1.380649e-23


class Simulation:
    """ Wrapping object for the saved simulations
    """
    def __init__(self, file_string):

        data = np.load(file_string)
        (L,L,steps) = data.shape

        param_string = file_string[:-4].split('\\')[-1]
        params = param_string.split('_')

        parameters = {}
        for i in params:
            pos = i.find('=')
            parameters[i[:pos]] = float(i[pos+1:])

        parameters['steps'] = steps
        parameters['L'] = L
        self.parameters = parameters
        self.data = data


def init_crystal(dims):
    """Create the initial crystal surface
    Creates a N x M surface with all lattice points occupied

    Parameter
    ---------
    dims : Tulple or nd.array
        The dimensions of the initial cristal surface

    Return
    ------
    surface : nd.array
        The occupied crystal latticle points
    """
    surface = np.ones(dims)
    return surface


def nearest_neighbours(surface):
    """Identifying the number of neighbours of each surface atom using periodic boundary
    conditions.

    Parameter
    ---------
    surface : nd.array
        An N x N matrix representing the surface of a crystal

    Return
    ------
    neighbours : nd.array
        An N x N matrix representing the number of neighbouring spaces of location (i, j)
        of the crystal surface that are occupied by an atom
    """
    dims = surface.shape
    neighbours = np.ones(dims)
    for i in range(dims[0]):
        for j in range(dims[1]):
            if surface[i,j] <= surface[int(i+1-dims[0]*np.floor((i+1)/dims[0])),j]:
                neighbours[i,j] += 1
            if surface[i,j] <= surface[i,int(j+1-dims[1]*np.floor((j+1)/dims[1]))]:
                neighbours[i,j] += 1
            if surface[i,j] <= surface[int(i-1-dims[0]*np.floor((i-1)/dims[0])),j]:
                neighbours[i,j] += 1
            if surface[i,j] <= surface[i,int(j-1-dims[1]*np.floor((j-1)/dims[1]))]:
                neighbours[i,j] += 1
    return neighbours


def evaporation_rate(n, T):
    """The evaporation rate based on the number of neighbours and temperature

    Parameter
    ---------
    n : int
        Number of nearest neigbours
    T : float
        Dimensionless temperature

    Return
    ------
    k_minus : float/nd.array
        Dimensionless evaporation rate
    """
    k_minus = np.exp(-n*T)
    return k_minus


def impingement_rate(mu, T):
    """The impingement rate based on the chemical potential and temperature

    Parameter
    ---------
    mu : float
        Dimensionless chemical potential
    T : float
        Dimensionless temperature

    Return
    ------
    k_plus : float
        Dimensionless impingement rate
    """

    k_3 = evaporation_rate(3, T)
    k_plus = np.exp(mu)*k_3
    return k_plus


def surface_migration_rate(n, m, T):
    """
    Parameter
    ---------
    n : int
        Number of neighbours of the selected atom
    m : int
        Number of neighbours of the neighbour of the selected particle
    T : float
        Dimensionless temperature

    Return
    ------
    k_nm : float
        Dimensionless migration rate
    """

    if n == 1 or m == 1:
        Esd = 1/2
    elif n == 2 or m == 2:
        Esd = 3/2
    else:
        Esd = 5/2

    if m <= n:
        DeltaE = n-m
    else:
        DeltaE = 0

    k_nm = 1/8*np.exp(-(Esd+DeltaE)*T)
    return k_nm


def choose_subset(surface, T, mu):
    """choose the number of neighbours each atom in the subset will have in which interaction will occur

    Parameter
    ---------
    surface : nd.array
        An N x N matrix representing the surface of a crystal
    T : float
        Dimensionless temperature
    mu : float
        Dimensionless chemical potential

    Return
    ------
    subset :

    """
    counts = dict(zip([1, 2, 3, 4, 5], [0, 0, 0, 0, 0]))
    neigh = nearest_neighbours(surface)
    unique, counting = np.unique(neigh, return_counts = True)
    index = 0
    for number in unique:
        counts[number] = counting[index]
        index += 1

    denom = 0
    for i in range(1,6):
        denom += counts[i]*(evaporation_rate(i,T)+impingement_rate(mu, T)+surface_migration_rate(i,i,T))

    prob = np.zeros(5)
    for i in range(5):
        prob[i] = counts[i+1]*(evaporation_rate(i+1,T)+impingement_rate(mu, T)+surface_migration_rate(i+1,i+1,T))/denom

    rand = uniform(0,1)
    if rand < prob[0]:
        subset = 1
    elif rand < prob[0] + prob[1]:
        subset = 2
    elif rand < prob[0] + prob[1] + prob[2]:
        subset = 3
    elif rand < prob[0] + prob[1] + prob[2] + prob[3]:
        subset = 4
    elif rand < prob[0] + prob[1] + prob[2] + +prob[3] + prob[4]:
        subset = 5

    return subset


def interaction(surface, T, mu):
    """randomly lets interaction take place in chosen subset"""

    dims = surface.shape
    neigh = nearest_neighbours(surface)
    subset = choose_subset(surface, T, mu)
    options_x = np.where(neigh==subset)[0]
    options_y = np.where(neigh==subset)[1]
    site = choice(range(np.size(options_x)))

    location = (options_x[site], options_y[site])

    k_plus = impingement_rate(mu, T)
    k_minus = evaporation_rate(subset, T)
    k_nn = surface_migration_rate(subset, subset, T)

    denom = k_plus + k_minus + k_nn

    rand = uniform(0,1)
    if rand < k_plus/denom:
        surface[location] += 1
    elif rand < (k_plus+k_minus)/denom:
        surface[location] -= 1
    else:
        migrate = choice([(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)])
        m = neigh[int(location[0]+migrate[0]-dims[0]*np.floor((location[0]+migrate[0])/dims[0])),
                  int(location[1]+migrate[1]-dims[1]*np.floor((location[1]+migrate[1])/dims[1]))]
        n = neigh[location]
        prob = surface_migration_rate(n, m, T)
        rand = uniform(0,1)
        if rand < prob:
            surface[location] -= 1
            surface[int(location[0]+migrate[0]-dims[0]*np.floor((location[0]+migrate[0])/dims[0])),
                  int(location[1]+migrate[1]-dims[1]*np.floor((location[1]+migrate[1])/dims[1]))] += 1


    return surface



def dislocation_matrices(dims, face, face_loc, boundaries, b):
    """Defining a single dislocation line on the (001) cystal surface.

    Parameter
    ---------
    dims : Tulple or nd.array
        Dimensions of the crystal surface
    face : int --> {0, 1}
        The plain the dislocation line is located in
        Value
        -----
        0 : dislocation line lies in the (100) plain
        1 : dislocation line lies in the (010) plain
    face_loc : int --> {1:dims[i]-1}
        The location of the plane the dislocation line lies in. For
        [face_loc] = n, the dislocation is between the (n-1)th and nth
        atom.
    boundaries : Tulple --> [start, end]
        The boundaries of the dislocation line with [start] < [end]
        Value
        -----
        start : {0:dims[i]-1}
        end : {1:dims[i]}
    b : int
        The magnitude of the Burgers vector
        If b=0, there is no dislocation
        If b>0, the step will go up
        If b<0, the step will go down

    Return
    ------
    forward_matrix : nd.array
        Matrix used to create dislocation when looking at the forward neighbour
    backward_matrix : nd.array
        Matrix used to create dislocation when looking at the backward neighbour
    """
    forward_matrix = np.zeros(dims)
    backward_matrix = np.zeros(dims)
    line = np.arange(boundaries[0], boundaries[1], 1, dtype=int)
    dislocation_line = np.ones(boundaries[1]-boundaries[0])*b
    if face == 0:
        forward_matrix[face_loc, line] = dislocation_line
        backward_matrix[face_loc-1, line] = -dislocation_line
    elif face == 1:
        forward_matrix[line, face_loc] = dislocation_line
        backward_matrix[line, face_loc-1] = -dislocation_line
    else:
        raise ValueWarning('Value for [face] should be either 0 or 1')

    return forward_matrix, backward_matrix


def dislocation_neighbours(surface, face, forward_matrix, backward_matrix):
    """Identifying the number of neighbours of each surface atom using periodic boundary
    conditions for a surface with a single dislocation.

    Parameter
    ---------
    surface : nd.array
        An N x N matrix representing the surface of a crystal
    face : int --> {0, 1}
        The plain the dislocation line is located in
        Value
        -----
        0 : dislocation line lies in the (100) plain
        1 : dislocation line lies in the (010) plain
    forward_matrix : nd.array
        Matrix used to create dislocation when looking at the forward neighbour
    backward_matrix : nd.array
        Matrix used to create dislocation when looking at the backward neighbour

    Return
    ------
    neighbours : nd.array
        An N x N matrix representing the number of neighbouring spaces of location (i, j)
        of the crystal surface that are occupied by an atom
    """
    neighbours = np.ones(dims)
    forward_neighbour = surface + forward_matrix
    backward_neighbour = surface + backward_matrix

    if face == 0:
        for i in range(dims[0]):
            for j in range(dims[1]):
                if surface[i,j] <= forward_neighbour[int(i+1-dims[0]*np.floor((i+1)/dims[0])),j]:
                    neighbours[i,j] += 1
                if surface[i,j] <= surface[i,int(j+1-dims[1]*np.floor((j+1)/dims[1]))]:
                    neighbours[i,j] += 1
                if surface[i,j] <= backward_neighbour[int(i-1-dims[0]*np.floor((i-1)/dims[0])),j]:
                    neighbours[i,j] += 1
                if surface[i,j] <= surface[i,int(j-1-dims[1]*np.floor((j-1)/dims[1]))]:
                    neighbours[i,j] += 1
    elif face == 1:
        for i in range(dims[0]):
            for j in range(dims[1]):
                if surface[i,j] <= surface[int(i+1-dims[0]*np.floor((i+1)/dims[0])),j]:
                    neighbours[i,j] += 1
                if surface[i,j] <= forward_neighbour[i,int(j+1-dims[1]*np.floor((j+1)/dims[1]))]:
                    neighbours[i,j] += 1
                if surface[i,j] <= surface[int(i-1-dims[0]*np.floor((i-1)/dims[0])),j]:
                    neighbours[i,j] += 1
                if surface[i,j] <= backward_neighbour[i,int(j-1-dims[1]*np.floor((j-1)/dims[1]))]:
                    neighbours[i,j] += 1
    else:
        raise ValueWarning('Value for the face of the dislocation should be either 0 for (010) plane or 1 for the (100) plane')
    return neighbours


def nm_migration_rate(loc_n, loc_m, surface, neighbours, T, face, forward_matrix,
                      backward_matrix):
    """The migration rate of an atom from a position of n neighbours to m neighbours.
    When determining m a new surface has to be created where the surface original position of
    the atom has decreased in hight and the surface of the new position of the atom has
    increased in hight.

    Parameter
    ---------
    loc_n : Tulple
        The location of the atom on the crystal surface in its original position
    loc_m : Tulple
        The location of the atom on the crystal surface in its new position
    surface : nd.array
        The surface of the crystal
    neighbours : nd.array
        The number of neighbouring spaces of location (i, j) of the crystal surface
        that are occupied by an atom
    T : float
        Dimensionless temperature
    face : int --> {0, 1}
        The plain the dislocation line is located in
    forward_matrix : nd.array
        Matrix used to create dislocation when looking at the forward neighbour
    backward_matrix : nd.array
        Matrix used to create dislocation when looking at the backward neighbour

    Return
    ------
    k_nm : float
        Dimensionless migration rate
    """

    n = neighbours(loc)
    surface[loc_n] += -1
    surface[loc_m] += 1
    m = 1
    if face == 0:
        if surface[loc_m] <= forward_neighbour[int(loc_m[0]+1-dims[0]*np.floor((loc_m[0]+1)/dims[0])),loc_m[1]]:
            m += 1
        if surface[loc_m] <= surface[loc_m[0],int(loc_m[1]+1-dims[1]*np.floor((loc_m[1]+1)/dims[1]))]:
            m += 1
        if surface[loc_m] <= backward_neighbour[int(loc_m[0]-1-dims[0]*np.floor((loc_m[0]-1)/dims[0])),loc_m[1]]:
            m += 1
        if surface[loc_m] <= surface[loc_m[0],int(loc_m[1]-1-dims[1]*np.floor((loc_m[1]-1)/dims[1]))]:
            m += 1
    else:
        if surface[loc_m] <= surface[int(loc_m[0]+1-dims[0]*np.floor((loc_m[0]+1)/dims[0])),loc_m[1]]:
            m += 1
        if surface[loc_m] <= forward_neighbour[loc_m[0],int(loc_m[1]+1-dims[1]*np.floor((loc_m[1]+1)/dims[1]))]:
            m += 1
        if surface[loc_m] <= surface[int(loc_m[0]-1-dims[0]*np.floor((loc_m[0]-1)/dims[0])),loc_m[1]]:
            m += 1
        if surface[loc_m] <= backward_neighbour[loc_m[0],int(loc_m[1]-1-dims[1]*np.floor((loc_m[1]-1)/dims[1]))]:
            m += 1

    if n == 1 or m == 1:
        Esd = 1/2
    elif n == 2 or m == 2:
        Esd = 3/2
    else:
        Esd = 5/2

    if m <= n:
        DeltaE = n-m
    else:
        DeltaE = 0

    k_nm = 1/8*np.exp(-(Esd+DeltaE)*T)
    return k_nm


def dis_choose_subset(surface, T, mu, face, f_matrix, b_matrix):
    """choose the number of neighbours each atom in the subset will have in which interaction will occur

    Parameter
    ---------
    surface : nd.array
        An N x N matrix representing the surface of a crystal
    T : float
        Dimensionless temperature
    mu : float
        Dimensionless chemical potential

    Return
    ------
    subset :

    """
    counts = dict(zip([1, 2, 3, 4, 5], [0, 0, 0, 0, 0]))
    neigh = dislocation_neighbours(surface, face, f_matrix, b_matrix)
    unique, counting = np.unique(neigh, return_counts = True)
    index = 0
    for number in unique:
        counts[number] = counting[index]
        index += 1

    denom = 0
    for i in range(1,6):
        denom += counts[i]*(evaporation_rate(i,T)+impingement_rate(mu, T)+surface_migration_rate(i,i,T))

    prob = np.zeros(5)
    for i in range(5):
        prob[i] = counts[i+1]*(evaporation_rate(i+1,T)+impingement_rate(mu, T)+surface_migration_rate(i+1,i+1,T))/denom

    rand = uniform(0,1)
    if rand < prob[0]:
        subset = 1
    elif rand < prob[0] + prob[1]:
        subset = 2
    elif rand < prob[0] + prob[1] + prob[2]:
        subset = 3
    elif rand < prob[0] + prob[1] + prob[2] + prob[3]:
        subset = 4
    elif rand < prob[0] + prob[1] + prob[2] + +prob[3] + prob[4]:
        subset = 5

    return subset


def find_avg_height(plane: np.ndarray) -> list[float,float]:
    """Finds the average height and standard deviation of the height of the plane

    Parameters
    ----------
    plane : np.ndarray
        array describing the height of the current crystal face at point (i,j)

    Returns
    -------
    List[float,float]
        list of average height and standard deviation
    """

    average_height = np.average(plane)
    deviation_height = np.std(plane)

    return average_height, deviation_height


def find_rate(initial_state: np.ndarray,
    final_state: np.ndarray,
    initial_iter: int,
    final_iter: int
    ) -> list[float, float]:
    """Finds the rate of growth of the crystal phase in units of k+

    Parameters
    ----------
    initial_state : np.ndarray
        starting face
    final_state : np.ndarray
        ending face
    initial_iter : int
        statting iter
    final_iter : int
        ending iter

    Returns
    -------
    list[float, float]
        rate and error thereof
    """

    init_height, init_dev = find_avg_height(initial_state)
    final_height, final_dev = find_avg_height(final_state)

    iter_elaps = final_iter - initial_iter
    rate = (final_height - init_height) / iter_elaps
    error = np.sqrt((1/iter_elaps)**2 * init_dev**2 + (1/iter_elaps)**2 * final_dev**2)

    return rate, error


def compute_rates(simulation: Simulation) -> list[np.ndarray,np.ndarray]:
    """ Computes the growth rate over a whole simulation and error by using error propagation

    Parameters
    ----------
    simulation : Simulation
        simulation object made from a saved array

    Returns
    -------
    list[np.ndarray,np.ndarray]
        array of rates and errors thereof
    """

    tot_steps = simulation.parameters['N']
    int_surf_amnt = simulation.parameters['steps'] - 1
    length = simulation.parameters['L']
    atoms = length**2

    data_arr = simulation.data

    temp = simulation.parameters['T']
    mu = simulation.parameters['mu']

    iter_int = tot_steps / int_surf_amnt

    rates = np.array([], dtype=np.float64)
    rates_err = np.array([], dtype=np.float64)

    for i in range(int_surf_amnt-1):
        start = i*iter_int
        stop = (i+1)*iter_int


        rate, err = find_rate(data_arr[:,:,i], data_arr[:,:,i+1], start, stop)
        rates = np.append(rates, rate)
        rates_err = np.append(rates_err, err)

    kplus = np.exp(mu)*evaporation_rate(3, temp)
    rates = rates * atoms
    rates_err = rates_err /kplus /atoms

    return rates, rates_err