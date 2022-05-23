import numpy as np
import matplotlib.pyplot as plt
from random import uniform
'''global parameters'''
kb = 1.380649e-23


def init_crystal(dims):
    surface = np.ones(dims)
    return surface

def nearest_neighbours(surface):
    dims = surface.shape
    neighbours = np.zeros(dims)
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
    '''
    parameters:
        n : number of nearest neigbours
        T: temperature
        
    '''
    
    phi = 1 
    '''not sure what value this is supposed to have'''
    mu = 1 
    '''frequency factor again not sure what it is supposed to be'''
    k_minus = mu*np.exp(-n*phi/(kb*T))
    return k_minus

def impingement_rate(mu, T):
    
    k_plus = np.exp(mu/(kb*T))*evaporation_rate(3, T)
    return k_plus

def surface_migration_rate(n, m, T):
    
    phi = 1
    mu = 1
    
    if n == 1 or m == 1:
        Esd = phi/2
    elif n == 2 or m == 2:
        Esd = 3*phi/2
    else:
        Esd = 5*phi/2
        
    if m <= n:
        DeltaE = (n-m)*phi
    else:
        DeltaE = 0
        
    k_nm = 1/8*mu*np.exp(-(Esd+DeltaE)/(kb*T))
    return k_nm
    
def choose_subset(surface, T, mu):
    
    
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
        
    choice = uniform(0,1)
    if choice < prob[0]:
        subset = 1
    elif choice < prob[0] + prob[1]:
        subset = 2
    elif choice < prob[0] + prob[1] + prob[2]:
        subset = 3
    elif choice < prob[0] + prob[1] + prob[2] + prob[3]:
        subset = 4
    elif choice < prob[0] + prob[1] + prob[2] + +prob[3] + prob[4]:
        subset = 5
        
    return subset
        
        
        
    
    
            