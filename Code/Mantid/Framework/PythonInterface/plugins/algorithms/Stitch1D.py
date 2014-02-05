"""*WIKI* 

Stitches single histogram [[MatrixWorkspace|Matrix Workspaces]] together outputing a stitched Matrix Workspace. This algorithm is a wrapper over [[Stitch1DMD]].

The workspaces must be histogrammed. Use [[ConvertToHistogram]] on workspaces prior to passing them to this algorithm.
*WIKI*"""
from mantid.simpleapi import *

from mantid.api import *
from mantid.kernel import *
import numpy as np

class Stitch1D(PythonAlgorithm):

    def category(self):
        return "Reflectometry\\ISIS;PythonAlgorithms"

    def name(self):
	    return "Stitch1D"

    def PyInit(self):
        
        histogram_validator = HistogramValidator()
        
        self.declareProperty(MatrixWorkspaceProperty("LHSWorkspace", "", Direction.Input, validator=histogram_validator), "Input workspace")
        self.declareProperty(MatrixWorkspaceProperty("RHSWorkspace", "", Direction.Input, validator=histogram_validator), "Input workspace")
        self.declareProperty(MatrixWorkspaceProperty("OutputWorkspace", "", Direction.Output), "Output stitched workspace")
        
        overlap_validator = FloatMandatoryValidator() 
        
        self.declareProperty(name="StartOverlap", defaultValue=-1.0, validator=overlap_validator, doc="Overlap in Q.")
        self.declareProperty(name="EndOverlap", defaultValue=-1.0, validator=overlap_validator, doc="End overlap in Q.")
        self.declareProperty(FloatArrayProperty(name="Params", values=[0.1]), doc="Rebinning Parameters. See Rebin for format.")
        self.declareProperty(name="ScaleRHSWorkspace", defaultValue=True, doc="Scaling either with respect to workspace 1 or workspace 2.")
        self.declareProperty(name="UseManualScaleFactor", defaultValue=False, doc="True to use a provided value for the scale factor.")
        self.declareProperty(name="ManualScaleFactor", defaultValue=1.0, doc="Provided value for the scale factor.")
        self.declareProperty(name="OutScaleFactor", defaultValue=-2.0, direction = Direction.Output, doc="The actual used value for the scaling factor.")
    
    def has_non_zero_errors(self, ws):
        errors = ws.extractE()
        count = len(errors.nonzero()[0])
        return count > 0
    
    def __find_indexes_start_end(self, startOverlap, endOverlap, workspace):
        a1=workspace.binIndexOf(startOverlap)
        a2=workspace.binIndexOf(endOverlap)
        if a1 == a2:
            raise RuntimeError("The Params you have provided for binning yield a workspace in which start and end overlap appear in the same bin. Make binning finer via input Params.")
        return a1, a2
    
    '''
    Fetch and create rebin parameters.
    If a single step is provided, then the min and max values are taken from the input workspaces.
    '''
    def __create_rebin_parameters(self):
        params = None
        user_params = self.getProperty("Params").value
        if user_params.size >= 3:
            params = user_params
        else:
            lhs_ws = self.getProperty("LHSWorkspace").value
            rhs_ws = self.getProperty("RHSWorkspace").value
            params = list()
            params.append(np.min(lhs_ws.readX(0)))
            params.append(user_params[0])
            params.append(np.max(rhs_ws.readX(0)))
        return params
            
    def PyExec(self):
        # Just forward the other properties on.
        range_tolerance = 1e-9
        startOverlap = self.getProperty('StartOverlap').value - range_tolerance
        endOverlap = self.getProperty('EndOverlap').value + range_tolerance
        scaleRHSWorkspace = self.getProperty('ScaleRHSWorkspace').value
        useManualScaleFactor = self.getProperty('UseManualScaleFactor').value
        manualScaleFactor = self.getProperty('ManualScaleFactor').value
        outScaleFactor = self.getProperty('OutScaleFactor').value
        
        params = self.__create_rebin_parameters()
        print params
        logger.warning(str(params))
        lhs_rebinned = Rebin(InputWorkspace=self.getProperty("LHSWorkspace").value, Params=params)
        rhs_rebinned = Rebin(InputWorkspace=self.getProperty("RHSWorkspace").value, Params=params)
        
        xRange = lhs_rebinned.readX(0)
        minX = xRange[0]
        maxX = xRange[-1]
        if(round(startOverlap, 9) < round(minX, 9)):
            logger.warning("StartOverlap: %0.9f, X min: %0.9f" % (startOverlap, minX))
            raise RuntimeError("Stitch1D StartOverlap is outside the X range after rebinning")
        if(round(endOverlap, 9) > round(maxX, 9)):
            logger.warning("EndOverlap: %0.9f, X max: %0.9f" % (endOverlap, maxX))
            raise RuntimeError("Stitch1D EndOverlap is outside the X range after rebinning")
        
        if(startOverlap > endOverlap):
            raise RuntimeError("Stitch1D cannot have a StartOverlap > EndOverlap")
    
        a1, a2 = self.__find_indexes_start_end(startOverlap, endOverlap, lhs_rebinned)
        
        if not useManualScaleFactor:
            lhsOverlapIntegrated = Integration(InputWorkspace=lhs_rebinned, RangeLower=startOverlap, RangeUpper=endOverlap)
            rhsOverlapIntegrated = Integration(InputWorkspace=rhs_rebinned, RangeLower=startOverlap, RangeUpper=endOverlap)
            y1=lhsOverlapIntegrated.readY(0)
            y2=rhsOverlapIntegrated.readY(0)
            if scaleRHSWorkspace:
                rhs_rebinned *= (lhsOverlapIntegrated/rhsOverlapIntegrated)
                scalefactor = y1[0]/y2[0]
            else: 
                lhs_rebinned *= (rhsOverlapIntegrated/lhsOverlapIntegrated)
                scalefactor = y2[0]/y1[0]   
            DeleteWorkspace(lhsOverlapIntegrated)
            DeleteWorkspace(rhsOverlapIntegrated) 
        else:
            if scaleRHSWorkspace:
                rhs_rebinned *= manualScaleFactor
            else:
                lhs_rebinned *= manualScaleFactor
            scalefactor = manualScaleFactor
        
        # Mask out everything BUT the overlap region as a new workspace.
        overlap1 = MultiplyRange(InputWorkspace=lhs_rebinned, StartBin=0,EndBin=a1,Factor=0)
        overlap1 = MultiplyRange(InputWorkspace=overlap1,StartBin=a2,Factor=0)
    
        # Mask out everything BUT the overlap region as a new workspace.
        overlap2 = MultiplyRange(InputWorkspace=rhs_rebinned,StartBin=0,EndBin=a1,Factor=0)#-1
        overlap2 = MultiplyRange(InputWorkspace=overlap2,StartBin=a2,Factor=0)
    
        # Mask out everything AFTER the start of the overlap region
        lhs_rebinned=MultiplyRange(InputWorkspace=lhs_rebinned, StartBin=a1+1, Factor=0)
        # Mask out everything BEFORE the end of the overlap region
        rhs_rebinned=MultiplyRange(InputWorkspace=rhs_rebinned,StartBin=0,EndBin=a2-1,Factor=0)
        
        # Calculate a weighted mean for the overlap region
        overlapave = None
        if self.has_non_zero_errors(overlap1) and self.has_non_zero_errors(overlap2):
            overlapave = WeightedMean(InputWorkspace1=overlap1,InputWorkspace2=overlap2)
        else:
            self.log().information("Using un-weighted mean for Stitch1D overlap mean")
            overlapave = (overlap1 + overlap2)/2
            
        # Add the Three masked workspaces together to create a complete x-range
        result = lhs_rebinned + overlapave + rhs_rebinned
        RenameWorkspace(InputWorkspace=result, OutputWorkspace=self.getPropertyValue("OutputWorkspace"))
        
        # Cleanup
        DeleteWorkspace(lhs_rebinned)
        DeleteWorkspace(rhs_rebinned)
        DeleteWorkspace(overlap1)
        DeleteWorkspace(overlap2)
        DeleteWorkspace(overlapave)
       
        self.setProperty('OutputWorkspace', result)
        self.setProperty('OutScaleFactor', scalefactor)
        
        return None
        

#############################################################################################

AlgorithmFactory.subscribe(Stitch1D())
