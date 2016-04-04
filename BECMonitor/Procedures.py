"""This file will have all our procedures.  This is not necessary, but its good for
keeping track of things
@author: zachglassman
"""
try:
    from BECMonitor.ProcedureObject import Procedure
    from BECMonitor.AbsorptionFit_2D import fit_mask_bimodal_2D, fit_TF, fit_Gauss
except:
    from ProcedureObject import Procedure
    from AbsorptionFit_2D import fit_mask_bimodal_2D, fit_TF, fit_Gauss

bimodal_mask_2d = Procedure('bimod_mask_2d',fit_mask_bimodal_2D,data='data_in')
tf_2d = Procedure('tf_2d', fit_TF, data = 'data_in')
gauss_2d = Procedure('gauss_2d', fit_Gauss, data = 'data_in')
