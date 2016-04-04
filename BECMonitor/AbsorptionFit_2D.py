"""
Created on Mon Nov 2 2015
2D Fitting Procedure
@author: zachglassman
"""
import numpy as np
from lmfit import Model, Parameters, Parameter
import copy
try:
    from BECMonitor.ProcedureObject import Procedure
except:
    from ProcedureObject import Procedure
from numba import autojit
from collections import OrderedDict

def TF_2D(x,y,peak, Rx,Ry, centerx, centery, off, theta):
    """ 2 Dimensional Thomas-Fermi profile

    .. math::
            TF = A \\max\\left\\{\\left[1-\\left(\\frac{x_c}{dx}\\right)^2-\\left(\\frac{y_c}{dy}\\right)^2\\right],0\\right\\}^{3/2}

    :param x: array of x values
    :param y: array of y values
    :param peak: Peak value of distribution
    :param Rx: X Thomas-Fermi radius in rotated frame
    :param Ry: Y Thomas-Fermi radius in rotated frame
    :param centerx: x center in unrotated frame
    :param centery: y center in unrotated frame
    :param off: offset
    :param theta: angle of rotation
    :return: Thomas-Fermi Profile in two-dimensions
    """
    angle = np.deg2rad(theta)

    xcenter = (x-centerx)*np.cos(angle) - (y-centery) * np.sin(angle)
    ycenter = (x-centerx)*np.sin(angle) + (y-centery) * np.cos(angle)
    a = (np.divide((xcenter),Rx))**2
    aa = (np.divide((ycenter),Ry))**2
    bb = np.subtract(np.subtract(1, a), aa)
    c = np.zeros(bb.shape)
    b = np.power(np.maximum(bb,c),3/2)
    return (off + np.multiply(peak,b)).ravel()


def gauss_2D(x,y,peak,sigx,sigy, centerx, centery, off, theta):
    """ 2 Dimensional Gaussian profile

    :param x: array of x values
    :param y: array of y values
    :param peak: Peak value of distribution
    :param sigx: X variance in rotated frame
    :param sigy: Y variance in rotated frame
    :param centerx: x center in unrotated frame
    :param centery: y center in unrotated frame
    :param off: offset
    :param theta: angle of rotation
    :return: Gaussian Profile in two-dimensions
    """
    angle = np.deg2rad(theta)

    xcenter = (x-centerx)*np.cos(angle) - (y-centery) * np.sin(angle)
    ycenter = (x-centerx)*np.sin(angle) + (y-centery) * np.cos(angle)
    a = np.divide(np.power(xcenter,2),(2 * sigx**2))
    b = np.divide(np.power(ycenter,2),(2 * sigy**2))
    return (off + peak * np.exp(-a-b)).ravel()



def flat_gauss_2D(x,y,mask,peak,sigx,sigy, centerx, centery, off, theta):
    """ 2 Dimensional flat Gaussian profile
    normal Gaussian in wings and flat between Thomas Fermi Radius
    Assumes already found mask which is array of true/false values
    the True values correspond to flat peak, we will proceed as follows
    1. in mask, true into 0 and false in 1
    2. multiply ans by mask (clear center values)
    3. turn true into 1 and false into 0
    3. add ans to mask * center value

    :param x: array of x values
    :param y: array of y values
    :param peak: Peak value of distribution
    :param sigx: X variance in rotated frame
    :param sigy: Y variance in rotated frame
    :param centerx: x center in unrotated frame
    :param centery: y center in unrotated frame
    :param off: offset
    :param theta: angle of rotation
    :params mask:TF mask
    :return: flattened Gaussian Profile in two-dimensions
    """
    angle = np.deg2rad(theta)
    xcenter = (x-centerx)*np.cos(angle) - (y-centery) * np.sin(angle)
    ycenter = (x-centerx)*np.sin(angle) + (y-centery) * np.cos(angle)
    a = np.divide(np.power(xcenter,2),(2 * sigx**2))
    b = np.divide(np.power(ycenter,2),(2 * sigy**2))

    ans = peak * np.exp(-a-b)
    #now smooth the peak
    mask1 = np.logical_not(mask).ravel()
    ans = ans * mask1
    #now the value for the middle should be max value of ans
    val = np.max(ans)
    return off + ans + mask.astype(int).ravel() * val


def bimod_2D(x,y,centerx,centery,peakg,peaktf,Rx,Ry,sigx,sigy,off,theta):
    """ two dimensional bimodal profile """
    a = gauss_2D(x,y,peakg,sigx,sigy, centerx, centery, off/2, theta)
    b = TF_2D(x,y,peaktf, Rx,Ry, centerx, centery, off/2, theta)
    return (a + b).ravel()

def bimod_flat_2D(x,y,mask,centerx,centery,peakg,peaktf,Rx,Ry,sigx,sigy,off,theta):
    """ two dimensional bimodal profile """
    a = flat_gauss_2D(x,y,mask,peakg,sigx,sigy, centerx, centery, off/2, theta)
    b = TF_2D(x,y,peaktf, Rx,Ry, centerx, centery, off/2, theta)
    return (a + b).ravel()



def create_vec(shape):
    """Create them meshgrid of vectors for fitting"""
    x = np.arange(0,shape[1],1)
    y = np.arange(0,shape[0],1)
    return np.meshgrid(x,y)


def pos(x,y,xc,yc,angle):
    """get the position when rotated"""
    xpos = (x-xc)*np.cos(angle) - (y-yc) * np.sin(angle)
    ypos = (x-xc)*np.sin(angle) + (y-yc) * np.cos(angle)
    return abs(xpos), abs(ypos)

@autojit
def find_rotated_mask(shape,Rx,Ry,angle,xc,yc):
    """find a rotated mask"""
    arr = np.empty((shape[0],shape[1]), dtype = bool)
    #now fill the array with distance away from center
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            xpos, ypos = pos(j,i,xc,yc,angle)
            if (xpos/Rx)**2 + (ypos/Ry)**2 < 1:
                arr[i,j] = True
            else:
                arr[i,j] = False

    return arr

def find_mask(s, params, shape):
    """ find the mask for the TF radius"""

    to_rotate = {'xc': params['centerx'].value,
                 'yc': params['centery'].value,
                 'Rx': s*params['Rx'].value,
                 'Ry': s*params['Ry'].value,
                 'angle' : np.deg2rad(params['theta'].value)}


    return find_rotated_mask(shape,**to_rotate)

def subtract_back(image,n):
    """subtract average of n rows of top and bottom from background"""
    back = (np.average(image[:n])+np.average(image[-n:]))/2
    return np.subtract(image,back)

def BEC_num(A,Rx,Ry, scalex,scaley):
    """get number of BEC atoms from fit from equation

    .. math::
        N = \\left(\\frac{2 \\pi}{3\\lambda^2}\\right)\\frac{2\\pi A}{5}R_x R_y

    :param scalex: x scale of pixel
    :param scaley: y scale of pixel
    :param A: fitted Thomas-Fermi amplitude
    :param Rx: fitted Thomas-Fermi x radius
    :param Ry: fitted Thomas-Fermi y radius
    :param sigma: optical density
    :return: atom number
    """

    Rx = Rx * scalex
    Ry = Ry * scaley
    sigma =  3 * (0.5891583264**2)/(2 * np.pi)
    V = 2*np.pi/5 * A* Rx * Ry
    return V/sigma

def Therm_num(A,sigx, sigy, scalex,scaley):
    """get number of Therm atoms from fit from equation

    .. math::
        N = \\left(\\frac{2 \\pi}{3\\lambda^2}\\right)\\frac{2\\pi A}{5}R_x R_y

    :param scalex: x scale of pixel
    :param scaley: y scale of pixel
    :param A: fitted Gaussian amplitude
    :param Rx: fitted Gaussian x standard deviation
    :param Ry: fitted Gaussian y standard deviation
    :param sigma: optical density
    :return: atom number
    """
    Rx = sigx * scalex
    Ry = sigy * scaley
    sigma =  3 * (0.5891583264**2)/(2 * np.pi)
    V = 2*np.pi* A* Rx * Ry
    return V/sigma

#################
#Model initialization
#################
gauss_2d_mod = Model(gauss_2D, independent_vars = ['x','y'])
tf_2d_mod = Model(TF_2D, independent_vars = ['x','y'])
bimod_2d_mod = Model(bimod_2D, independent_vars = ['x','y'])
bimod_flat_2d_mod = Model(bimod_flat_2D, independent_vars = ['x','y','mask'])

##################
#Fitting
# input parameters can be dictionaries with value, min ,max
##################
def fit_mask_bimodal_2D(data_in,
                        s = {'value':1,'min':None,'max':None},
                        centerx={'value':92,'min':40,'max':200},
                        centery={'value':71,'min':40,'max':200},
                        peakg={'value':.02,'min':.009,'max':.05},
                        peaktf={'value':.15,'min':0,'max':.5},
                        Rx={'value':13 ,'min':9,'max':14},
                        Ry={'value':13,'min':9,'max':14},
                        sigx={'value':17,'min':14,'max':24},
                        sigy={'value':17,'min':14,'max':24},
                        off={'value':0 ,'min':-1,'max': 1},
                        theta={'value':48.5,'min':48,'max':50}):
    """
    function to fit image.  For a sequential fit, proceed as follows
    1. Do full bimodal fit to determine approximate TF radius
    2. Mask TF and fit to flat Gaussian
    3. Fix flat Gaussian and re-fit TF

    :param data_in: image data
    """
    data = subtract_back(data_in,20)
    in_pars = {'centerx':centerx,
              'centery':centery,
              'peakg':peakg,
              'peaktf':peaktf,
              'Rx':Rx,
              'Ry':Ry,
              'sigx':sigx,
              'sigy':sigy,
              'off':off,
              'theta':theta
              }
    #first handle case when dictionaries
    try:
        pars = Parameters()
        for i in in_pars:
            pars.add(name=i,**in_pars[i])
    except:
        #now handle case when just values
        pars = Parameters()
        for i in in_pars:
            pars.add(name=i,value=in_pars[i])
    #find center for image ROI
    idx = np.argmax(data, axis = None)
    center_idx = np.unravel_index(idx,data.shape)
    width = 60
    data = data[center_idx[0]-width:center_idx[0]+width,
                center_idx[1]-width:center_idx[1]+width]


    x,y = create_vec(data.shape)
    #now find center for fit parameters
    idx = np.argmax(data, axis = None)
    center_idx = np.unravel_index(idx,data.shape)
    pars['centerx'].value = center_idx[1]
    pars['centery'].value = center_idx[0]


    first_fit = bimod_2d_mod.fit(data.ravel(),pars,x=x.ravel(),y=y.ravel())
    pars = copy.deepcopy(first_fit.params)
    #now figure out mask by finding square region of larger TF radius after rotation
    mask = find_mask(s,pars,data.shape) #array for mask

    # now make maskd array
    ma = np.ma.array(data, mask = mask)
    #now we apply the same mask to the vectors
    xm = np.ma.array(x, mask = mask)
    ym = np.ma.array(y, mask = mask)
    #now fix TFpeak to 0 and fix center
    TF_val = pars['peaktf'].value

    pars['peaktf'].value = 0
    pars['peaktf'].vary = False
    pars['Rx'].vary = False
    pars['Ry'].vary = False
    pars['centerx'].vary = False
    pars['centery'].vary = False
    #set gaussian wings to good guesses
    pars['sigx'].value = 10
    pars['sigy'].value = 10
    pars['peakg'].value = 0.1
    #fit to notmral gaussian
    second_fit = bimod_2d_mod.fit(ma.compressed(),
                                  pars,
                                  x=xm.compressed(),
                                  y=ym.compressed())



    pars = copy.deepcopy(second_fit.params)
    #now free the TF parameters
    pars['peaktf'].value = TF_val
    pars['peaktf'].vary = True
    pars['Rx'].vary = True
    pars['Ry'].vary = True
    #fix gaussian parameters
    pars['sigx'].vary = False
    pars['sigy'].vary = False
    pars['peakg'].vary = False

    #do third fit to either flat or gaussian
    gauss = True
    if gauss:
        out = bimod_2d_mod.fit(data.ravel(),pars,x=x.ravel(),y=y.ravel())
    else:
        #find new mask with s =0
        temps = args.s
        args.s = 1
        mask2 = find_mask(args,pars,data.shape)
        args.s = temps
        out = bimod_flat_2d_mod.fit(data.ravel(),
                                pars,
                                mask = mask2,
                                x=x.ravel(),
                                y=y.ravel())
    #results
    report = out.fit_report()
    results =  {key:out.params[key].value for key in out.params.keys()}
    #results['N_BEC_Atoms'] = BEC_num(A,Rx,Ry, scalex,scaley)
    return results

def fit_Gauss(data_in,
           centerx={'value':92,'min':40,'max':200},
           centery={'value':71,'min':40,'max':200},
           peak={'value':.15,'min':0,'max':.5},
           sigx={'value':13 ,'min':9,'max':14},
           sigy={'value':13,'min':9,'max':14},
           off={'value':0 ,'min':-1,'max': 1},
           theta={'value':48.5,'min':48,'max':50}):
        """Function to fit thomas Fermi radius to data.  Will be wrapped with
        Procedure class"""

        data = subtract_back(data_in,20)
        in_pars = {'centerx':centerx,
                  'centery':centery,
                  'peak':peak,
                  'sigx':sigx,
                  'sigy':sigy,
                  'off':off,
                  'theta':theta
                  }
        #first handle case when dictionaries
        try:
            pars = Parameters()
            for i in in_pars:
                pars.add(name=i,**in_pars[i])
        except:
            #now handle case when just values
            pars = Parameters()
            for i in in_pars:
                pars.add(name=i,value=in_pars[i])
        #find center for image ROI
        idx = np.argmax(data, axis = None)
        center_idx = np.unravel_index(idx,data.shape)
        width = 60
        data = data[center_idx[0]-width:center_idx[0]+width,
                    center_idx[1]-width:center_idx[1]+width]


        x,y = create_vec(data.shape)
        #now find center for fit parameters
        idx = np.argmax(data, axis = None)
        center_idx = np.unravel_index(idx,data.shape)
        pars['centerx'].value = center_idx[1]
        pars['centery'].value = center_idx[0]


        out = gauss_2d_mod.fit(data.ravel(),pars,x=x.ravel(),y=y.ravel())
        report = out.fit_report()

        results =  {key:out.params[key].value for key in out.params.keys()}
        #results['N_Therm_Atoms'] = Therm_num(A,Rx,Ry, scalex,scaley)
        return results

def fit_TF(data_in,
           centerx={'value':92,'min':40,'max':200},
           centery={'value':71,'min':40,'max':200},
           peak={'value':.15,'min':0,'max':.5},
           Rx={'value':13 ,'min':9,'max':14},
           Ry={'value':13,'min':9,'max':14},
           off={'value':0 ,'min':-1,'max': 1},
           theta={'value':48.5,'min':48,'max':50}):
        """Function to fit thomas Fermi radius to data.  Will be wrapped with
        Procedure class"""

        data = subtract_back(data_in,20)
        in_pars = {'centerx':centerx,
                  'centery':centery,
                  'peak':peak,
                  'Rx':Rx,
                  'Ry':Ry,
                  'off':off,
                  'theta':theta
                  }
        #first handle case when dictionaries
        try:
            pars = Parameters()
            for i in in_pars:
                pars.add(name=i,**in_pars[i])
        except:
            #now handle case when just values
            pars = Parameters()
            for i in in_pars:
                pars.add(name=i,value=in_pars[i])
        #find center for image ROI
        idx = np.argmax(data, axis = None)
        center_idx = np.unravel_index(idx,data.shape)
        width = 60
        data = data[center_idx[0]-width:center_idx[0]+width,
                    center_idx[1]-width:center_idx[1]+width]


        x,y = create_vec(data.shape)
        #now find center for fit parameters
        idx = np.argmax(data, axis = None)
        center_idx = np.unravel_index(idx,data.shape)
        pars['centerx'].value = center_idx[1]
        pars['centery'].value = center_idx[0]


        out = tf_2d_mod.fit(data.ravel(),pars,x=x.ravel(),y=y.ravel())
        report = out.fit_report()

        results =  {key:out.params[key].value for key in out.params.keys()}
        #results['N_BEC_Atoms'] = BEC_num(A,Rx,Ry, scalex,scaley)
        return results
