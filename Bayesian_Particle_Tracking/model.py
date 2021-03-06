import numpy as np
from numpy.random import normal
from numpy.random import uniform
from Bayesian_Particle_Tracking.printable import Printable
from Bayesian_Particle_Tracking.prior import JeffreysPrior
from Bayesian_Particle_Tracking.prior import UniformPrior

def displacement(data):
    """
    This returns the displacement between successive points for a data set of positions.

    Parameter
    ---------
    data: size m x n array where m can be 1, 2, or 3
        positional data input in cartesian coordinates (x,y,z)

    Returns
    -------
    distance : 1 x n-1 array
        containins n-1 displacement measurments for n positional points
    """

    ndim = data.shape[1]-2

    #The lines below copy the array and subtract the first element, and then do the same thing but subtract the last element.
    #For some reason, this runs faster than np.diff()
    data_length = len(data)
    point_before = data[:data_length-1]
    data_points = data[1:]

    y_before, y_data, z_before, z_data = 0, 0, 0, 0

    if ndim == 1:
        x_before = point_before[:,0]
        x_data = data_points[:,0]
    elif ndim == 2:
        x_before, y_before = point_before[:,0], point_before[:,1]
        x_data, y_data = data_points[:,0], data_points[:,1]
    elif ndim == 3:
        x_before, y_before, z_before = point_before[:,0], point_before[:,1], point_before[:,2]
        x_data, y_data, z_data = data_points[:,0], data_points[:,1], data_points[:,2]

    distance = np.sqrt((x_before-x_data)**2+(y_before-y_data)**2+(z_before-z_data)**2)
    return distance

class diffusion(Printable):
    '''
    Contains data and relevent parameters for a 3-D Diffusion Process.

    TODO: Pandas dataframe may be better, since there are only a couple of advantages to the class:
        self.dim: checking dimensionality of the process
        translate: translation funciton in the object allows for check that translation does effect output. No other use otherwise
    Pandas dataframe offers the key advantage of labeled columns although to be fair, we can still look at columns by name here.

    Attributes
    ----------
    data: size 3 x n array
        positional data input in cartesian coordinates (x,y,z)
    sigma: nonzero float
        specifies measurement uncertainty on measurement of particle position
    ndim : integer
        number of dimensions
    position: length 3 listlike
        initial position
    '''
    def __init__(self, data):
        self.data = data
        self.initial_position = data[0:]
        self.dim = data.shape[1] - 2
        if self.dim < 1 or self.dim > 3:
            raise ValueError('Number of dimensions should be either 1, 2, or 3.')
        if self.dim == 1:
            self.x = data[:,0]
        elif self.dim == 2:
            self.x = data[:,0]
            self.y = data[:,1]
        elif self.dim == 3:
            self.x = data[:,0]
            self.y = data[:,1]
            self.z = data[:,2]
        self.sigma_m = data[:,-2]
        self.time = data[:,-1]
    
    #Allows translation of the object
    def translate(self, offset):
        return diffusion(np.array((self.x+offset, self.y+offset, self.z+offset, self.sigma_m, selt.time)).T)


def log_prior(theta, lower_bound = 1e-12, upper_bound = 1e-8, prior = "Jeffreys"):
    """
    Log prior function for 3D diffusion process of a single particle.
    Default prior is a Jeffreys prior with lower bound at 1e-12 and upper bound at 1e-8

    Parameters
    ----------
        D: diffusion coefficient
        lower_bound: lower_bound of Prior
        upper_bound: upper_bound of Prior
    """
    if prior == "Jeffreys":
        theta_prior = JeffreysPrior(lower_bound, upper_bound).lnprob(theta)
    elif prior == "Uniform":
        theta_prior = UniformPrior(lower_bound, upper_bound).lnprob(theta)
    #Putting in different priors is possible.
    else:
        raise ValueError("Prior not recognized. ")
    return theta_prior

def log_likelihood(theta, diffusion_object, unknown = 'D', known_variables = None):
    """
    Likelihood function for 3D diffusion process of a single particle.

    Parameters
    ----------
        diffusion_object: contains the following:
            data: positional data: assumes data is in the form of column vectors (traj_x,traj_y,traj_z,sigma,tau)
                where traj_x,traj_y,traj_z are the coordinate positions of the particle
                sigma: variance on positional data; we assume the uncertainty is Gaussian; true dependency will be from raw image data
                tau: lag time
        theta: unknown parameter;
        unknown: The unknown parameter to be determined. Default is D. Must be input as string. Possible parameters are:
            D: diffusion coefficient
            a: radius of particle
            mu: dynamic viscosity of medium
            T: temperature of medium
        known_variables: Given as a tuple (a,b), where a and b are known values for the two unknown parameters if the uknown parameter is not D.
            For the following unknown parameters, the tuple (a,b) should be given as follows:
                a: (mu, T)
                mu: (a, T)
                T: (a, mu)
    """
    data = diffusion_object.data
    ndim = diffusion_object.dim
    sigma_m = diffusion_object.sigma_m

    #This code assumes the diffusion obeject gives absolute time instead of time displacements
    time = diffusion_object.time
    tau = time[1:len(time)] - time[0:len(time)-1]
    distance = displacement(data)

    if unknown == 'D':
        D = theta
    elif unknown != 'D':
        kb = 1.38e-23
        if unknown == 'a':
            a = theta
            mu, T = known_variables
            D = (kb*T)/(2*ndim*np.pi*mu*a)
        elif unknown == 'mu':
            mu = theta
            a, T = known_variables
            D = (kb*T)/(2*nim*np.pi*mu*a)
        elif unknown == 'T':
            T = theta
            a, mu = known_variables
            D = (kb*T)/(2*ndim*np.pi*mu*a)
        elif isinstance(unkonwn, str):
            raise ValueError('%s is not a valid parameter. Valid parameters are D, a, mu, T.' %unknown)
        else:
            raise TypeError('%s is not a string. Valid parameters are D, a, mu, T.' %unknown)
    
    #sigma is the error on the displacement. This comes from the error propogation terms in the positional measurments, sigma1 and sigma2.
    sigma_1 = sigma_m[1:len(sigma_m)]
    sigma_2 = sigma_m[:len(sigma_m)-1]
    sigma = np.sqrt(sigma_1**2+sigma_2**2)

    diffusion_factor = np.sqrt(2*ndim*D*tau)

    result = (-len(data)/2)*np.log(2*np.pi)+np.sum(np.log((diffusion_factor**2+sigma**2)**(-1/2)))+np.sum(-((distance)**2)/(2*(diffusion_factor**2+sigma**2)))
    return result
    
def log_posterior(theta, diffusion_object, unknown = 'D', known_variables = None, lower_bound = 1e-12, upper_bound = 1e-8, prior = "Jeffreys"):
    """
    Log posterior function for 3D diffusion process of a single particle. 

    Parameters are given by parameters in log_likelihood() function and log_prior() function
        theta, diffusion_object, unknown, known_variables given are parameters of log_likelihood()
        lower_bound, upper_bound, Jeffreys given are parameters of log_prior function

    """
    prior = log_prior(theta, lower_bound = lower_bound, upper_bound = upper_bound, prior = "Jeffreys")
    if prior == -np.inf:
        return prior
    return prior + log_likelihood(theta, diffusion_object, unknown = unknown, known_variables = known_variables)