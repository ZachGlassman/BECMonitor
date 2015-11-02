"""
Created on Mon Nov 2 2015
2D Fitting Procedure
@author: zachglassman
"""
import numpy as np
from lmfit import Model
import copy
from BECMonitor.Procedure import Procedure
from numba import autojit

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

def find_mask(args, params, shape):
    """ find the mask for the TF radius"""

    to_rotate = {'xc': params['bimod_centerx'].value,
                 'yc': params['bimod_centery'].value,
                 'Rx': args.s*params['bimod_Rx'].value,
                 'Ry': args.s*params['bimod_Ry'].value,
                 'angle' : np.deg2rad(params['bimod_theta'].value)}

    if args.constant_mask:
        to_rotate['Rx'] = args.constant_mask
        to_rotate['Ry'] = args.constant_mask

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
gauss_2d_mod = Model(gauss_2D, independent_vars = ['x','y'],prefix='gauss_')
tf_2d_mod = Model(TF_2D, independent_vars = ['x','y'],prefix='tf_')
bimod_2d_mod = Model(bimod_2D, independent_vars = ['x','y'],prefix='bimod_')
bimod_flat_2d_mod = Model(bimod_flat_2D, independent_vars = ['x','y','mask'],prefix='bimod_')

#starting parameters for bimodal fits
start_bimod_params = {'bimod_centerx': {'value':92,'min':40, 'max':200},
                      'bimod_centery':{'value':71,'min':40, 'max':200},
                      'bimod_peakg':{'value':.02,'min' : .009,'max':.05},
                      'bimod_peaktf':{'value':.15,'min' : 0,'max':.5},
                      'bimod_Rx':{'value':13 ,'min' : 9,'max':14},
                      'bimod_Ry':{'value':13,'min' : 9,'max':14},
                      'bimod_sigx':{'value':17,'min' :14,'max':24},
                      'bimod_sigy':{'value':17,'min' : 14,'max':24},
                      'bimod_off':{'value':0 ,'min' : -1,'max': 1},
                      'bimod_theta':{'value':48.5, 'min' : 48, 'max': 50}
                      }


#set parameter hings in model
for key, value in start_bimod_params.items():
    bimod_2d_mod.set_param_hint(key, **value)

##################
#Fitting
##################
def fit_image(args, data_in, filename, filepath):
    """
    function to fit image.  For a sequential fit, proceed as follows
    1. Do full bimodal fit to determine approximate TF radius
    2. Mask TF and fit to flat Gaussian
    3. Fix flat Gaussian and re-fit TF

    :param args: arguments passed from command line
    :param data_in: image data
    :param filename: filename of thing being fit
    :param filepath: path to results folder

    """
    data = subtract_back(data_in,20)
    pars = bimod_2d_mod.make_params()
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
    pars['bimod_centerx'].value = center_idx[1]
    pars['bimod_centery'].value = center_idx[0]



    if args.lock_sig:
        pars['bimod_sigy'].expr = 'bimod_sigx'

    if args.single:
        out = bimod_2d_mod.fit(data.ravel(),
                               pars,
                               x=x.ravel(),
                               y=y.ravel())
        report = out.fit_report()
        results =  {key:out.params[key].value for key in out.params.keys()}

    else:
        first_fit = bimod_2d_mod.fit(data.ravel(),pars,x=x.ravel(),y=y.ravel())
        pars = copy.deepcopy(first_fit.params)
        #now figure out mask by finding square region of larger TF radius after rotation
        mask = find_mask(args,pars,data.shape) #array for mask

        # now make maskd array
        ma = np.ma.array(data, mask = mask)
        #now we apply the same mask to the vectors
        xm = np.ma.array(x, mask = mask)
        ym = np.ma.array(y, mask = mask)
        #now fix TFpeak to 0 and fix center
        TF_val = pars['bimod_peaktf'].value

        pars['bimod_peaktf'].value = 0
        pars['bimod_peaktf'].vary = False
        pars['bimod_Rx'].vary = False
        pars['bimod_Ry'].vary = False
        pars['bimod_centerx'].vary = False
        pars['bimod_centery'].vary = False
        #set gaussian wings to good guesses
        pars['bimod_sigx'].value = 10
        if not args.lock_sig:
            pars['bimod_sigy'].value = 10
        pars['bimod_peakg'].value = 0.1
        #fit to notmral gaussian
        second_fit = bimod_2d_mod.fit(ma.compressed(),
                                      pars,
                                      x=xm.compressed(),
                                      y=ym.compressed())



        pars = copy.deepcopy(second_fit.params)
        #now free the TF parameters
        pars['bimod_peaktf'].value = TF_val
        pars['bimod_peaktf'].vary = True
        pars['bimod_Rx'].vary = True
        pars['bimod_Ry'].vary = True
        #fix gaussian parameters
        pars['bimod_sigx'].vary = False
        if not args.lock_sig:
            pars['bimod_sigy'].vary = False
        pars['bimod_peakg'].vary = False

        #do third fit to either flat or gaussian
        if args.gauss:
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

class AbsorbtionFit_2D(Procedure):
    """2D absorbtion Fitting"""
