import numpy as np
from Bayesian_Particle_Tracking.model import log_likelihood, displacement

def max_likelihood_estimation(diffusion_object, lower_bound, upper_bound, intervals):
    """
    Maximum Likelihood estimation for diffusion coefficient for a basic diffusion process.

    Parameters
    ----------
    diffusion_object: diffusion_object containing data
    lower_bound: log_10 of lower_bound of likelihood
    upper_bound: log_10 of upper_bound of likelihood
    intervals: number of intervals in logspace between lower_bound and upper_bound

    Outputs
    -------
    D: entire logspace of possible D's tested
    D[maxindex]: most likely value of D from max_likelihood_estimation
    loglikelihood: all values of loglikelihood across D
    D_range.min(): minimum value of D in 68 percent confidence interval
    D_range.max(): maximum value of D in 68 percent confidence interval
    """
    D = np.logspace(lower_bound, upper_bound, intervals)
    loglikelihood = np.array(list(map(lambda d: log_likelihood(d, diffusion_object), D)))
    maxindex = np.argmax(loglikelihood)
    D_range = D[loglikelihood > (loglikelihood.max() - 0.5)]
    return D, D[maxindex], loglikelihood, D_range.min(), D_range.max()

def MSD(data, i):
    """
    Parameters
    ----------
    data: n x 3 array of positional measurments (x,y,z)
    i: numbero f time steps

    Returns 
    -------
    MSD for i arbitrary time steps
    """
    data_length = len(data)
    point_before = data[:data_length-i]
    point_after = data[i:]
    
    x_before, y_before, z_before = point_before[:,0], point_before[:,1], point_before[:,2]
    x_after, y_after, z_after = point_after[:,0], point_after[:,1], point_after[:,2]
    SD = (x_before-x_after)**2+(y_before-y_after)**2+(z_before-z_after)**2
    return np.mean(SD)

def Nind(data, i):
    """
    Parameters
    ----------
    data: n x 3 array of positional measurments (x,y,z)
    i: number of time setps

    Returns
    -------
    Nind
    """
    N = len(data)
    return 2*(N - i)/i
    
def sigma_var(data, i):
    """
    Parameters
    ----------
    data: n x 3 array of positional measurments (x,y,z)
    i: number of time setps

    Returns
    -------
    variance on the MSD
    """
    return MSD(data, i)*np.sqrt(2/(Nind(data, i)-1))

def CGW_analysis(diffusion_object, max_lag_time, down_sample = 10):
    """
    Crocker, Grier, Weeks method for obtaining the diffusion coefficient and the uncertainties on its estimate.

    Parameters
    ----------
    diffusion_object: diffusion_object

    Outputs
    -------
    msd_array: array containing MSD's
    sigma_var_array: array containing errors on MSD
    counter: array containing number of time steps for the corresponding calculations in msd_array and sigma_var_array
    """
    msd_array = []
    sigma_var_array = []
    counter = np.arange(1,max_lag_time,down_sample)
    
    for i in range(1, max_lag_time, down_sample):
        msd_array.append(MSD(diffusion_object.data, i))
        sigma_var_array.append(sigma_var(diffusion_object.data, i))
        
    msd_array = np.array(msd_array)
    sigma_var_array = np.array(sigma_var_array)
    return msd_array, sigma_var_array, counter

def line_fit3D(tau, D):
    """
    This is the line that we want to fit our line tau vs MSD to. tau and MSD come from counter and msd_array from CGW_analysis, respectively.
    This is for 3D Diffusion

    Parameters
    ----------
    tau: lag time
    D: diffusion coefficient
    n: number of dimensions
    """
    return 6*D*tau