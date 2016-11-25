# pylint: disable=too-many-public-methods, invalid-name, too-many-arguments

import unittest
import os
import stresstesting

import mantid
from mantid.api import AlgorithmManager
from SANS2.UserFile.UserFileStateDirector import UserFileStateDirectorISIS
from SANS2.State.StateBuilder.SANSStateDataBuilder import get_data_builder
from SANS2.Common.SANSType import SANSFacility
from SANS2.Common.SANSConstants import SANSConstants
from SANS2.Common.SANSFunctions import create_unmanaged_algorithm


# -----------------------------------------------
# Tests for the SANSSingleReduction algorithm
# -----------------------------------------------
class SANSSingleReductionTest(unittest.TestCase):
    def _load_workspace(self, state):
        load_alg = AlgorithmManager.createUnmanaged("SANSLoad")
        load_alg.setChild(True)
        load_alg.initialize()

        state_dict = state.property_manager
        load_alg.setProperty("SANSState", state_dict)
        load_alg.setProperty("PublishToCache", False)
        load_alg.setProperty("UseCached", False)
        load_alg.setProperty("MoveWorkspace", False)
        load_alg.setProperty("SampleScatterWorkspace", "dummy")
        load_alg.setProperty("SampleScatterMonitorWorkspace", "dummy")
        load_alg.setProperty("SampleTransmissionWorkspace", "dummy")
        load_alg.setProperty("SampleDirectWorkspace", "dummy")

        # Act
        load_alg.execute()
        self.assertTrue(load_alg.isExecuted())
        sample_scatter = load_alg.getProperty("SampleScatterWorkspace").value
        sample_scatter_monitor_workspace = load_alg.getProperty("SampleScatterMonitorWorkspace").value
        return sample_scatter, sample_scatter_monitor_workspace

    def _run_single_reduction(self, state, sample_scatter, sample_monitor, sample_transmission=None, sample_direct=None,
                              can_scatter=None, can_monitor=None, can_transmission=None, can_direct=None,
                              output_settings=None):
        single_reduction_name = "SANSSingleReduction"
        state_dict = state.property_manager

        single_reduction_options = {"SANSState": state_dict,
                                    "SampleScatterWorkspace": sample_scatter,
                                    "SampleScatterMonitorWorkspace": sample_monitor}
        if sample_transmission:
            single_reduction_options.update({"SampleTransmissionWorkspace": sample_transmission})

        if sample_direct:
            single_reduction_options.update({"SampleDirectWorkspace": sample_direct})

        if can_scatter:
            single_reduction_options.update({"CanScatterWorkspace": can_scatter})

        if can_monitor:
            single_reduction_options.update({"CanScatterMonitorWorkspace": can_monitor})

        if can_transmission:
            single_reduction_options.update({"CanTransmissionWorkspace": can_transmission})

        if can_direct:
            single_reduction_options.update({"CanDirectWorkspace": can_direct})

        if output_settings:
            single_reduction_options.update(output_settings)

        single_reduction_alg = create_unmanaged_algorithm(single_reduction_name, **single_reduction_options)

        # Act
        single_reduction_alg.execute()
        self.assertTrue(single_reduction_alg.isExecuted())
        return single_reduction_alg

    def _compare_workspace(self, workspace, reference_file_name):
        # Load the reference file
        load_name = "LoadNexusProcessed"
        load_options = {"Filename": reference_file_name,
                        SANSConstants.output_workspace: SANSConstants.dummy}
        load_alg = create_unmanaged_algorithm(load_name, **load_options)
        load_alg.execute()
        reference_workspace = load_alg.getProperty(SANSConstants.output_workspace).value

        # In order to compare the output workspace with the reference, we need to convert it to rebin it so we
        # get a Workspace2D and then perform a bin masking again
        rebin_name = "Rebin"
        rebin_option = {SANSConstants.input_workspace: workspace,
                        SANSConstants.output_workspace: SANSConstants.dummy,
                        "Params": "8000,-0.025,100000",
                        "PreserveEvents": False}

        rebin_alg = create_unmanaged_algorithm(rebin_name, **rebin_option)
        rebin_alg.execute()
        rebinned = rebin_alg.getProperty(SANSConstants.output_workspace).value

        mask_name = "MaskBins"
        mask_options = {SANSConstants.input_workspace: rebinned,
                        SANSConstants.output_workspace: SANSConstants.dummy,
                        "XMin": 13000.,
                        "XMax": 15750.}
        mask_alg = create_unmanaged_algorithm(mask_name, **mask_options)
        mask_alg.execute()
        masked = mask_alg.getProperty(SANSConstants.output_workspace).value

        # Save the workspace out and reload it again. This makes equalizes it with the reference workspace
        f_name = os.path.join(mantid.config.getString('defaultsave.directory'),
                              'SANS_temp_single_reduction_testout.nxs')

        save_name = "SaveNexus"
        save_options = {"Filename": f_name,
                        "InputWorkspace": masked}
        save_alg = create_unmanaged_algorithm(save_name, **save_options)
        save_alg.execute()
        load_alg.setProperty("Filename", f_name)
        load_alg.setProperty(SANSConstants.output_workspace, SANSConstants.dummy)
        load_alg.execute()
        ws = load_alg.getProperty(SANSConstants.output_workspace).value

        # Compare reference file with the output_workspace
        # We need to disable the instrument comparison, it takes way too long
        # We need to disable the sample -- Not clear why yet
        # operation how many entries can be found in the sample logs
        compare_name = "CompareWorkspaces"
        compare_options = {"Workspace1": ws,
                           "Workspace2": reference_workspace,
                           "Tolerance": 1e-7,
                           "CheckInstrument": False,
                           "CheckSample": False,
                           "ToleranceRelErr": True,
                           "CheckAllData": True,
                           "CheckMasking": True,
                           "CheckType": True,
                           "CheckAxes": True,
                           "CheckSpectraMap": True}
        compare_alg = create_unmanaged_algorithm(compare_name, **compare_options)
        compare_alg.setChild(False)
        compare_alg.execute()
        result = compare_alg.getProperty("Result").value
        self.assertTrue(result)

        # Remove file
        if os.path.exists(f_name):
            os.remove(f_name)

    def test_that_single_reduction_evaluates_LAB(self):
        # Arrange
        # Build the data information
        data_builder = get_data_builder(SANSFacility.ISIS)
        data_builder.set_sample_scatter("SANS2D00034484")
        data_builder.set_sample_transmission("SANS2D00034505")
        data_builder.set_sample_direct("SANS2D00034461")
        data_builder.set_calibration("TUBE_SANS2D_BOTH_31681_25Sept15.nxs")
        data_info = data_builder.build()

        # Get the rest of the state from the user file
        user_file_director = UserFileStateDirectorISIS(data_info)
        user_file_director.set_user_file("USER_SANS2D_154E_2p4_4m_M3_Xpress_8mm_SampleChanger.txt")
        state = user_file_director.construct()

        # Load the sample workspaces
        workspace, workspace_monitor = self._load_workspace(state)

        # Act
        output_settings = {"OutputWorkspaceLAB": SANSConstants.dummy}
        single_reduction_alg = self._run_single_reduction(state, sample_scatter=workspace,
                                                          sample_monitor=workspace_monitor,
                                                          output_settings=output_settings)
        output_workspace = single_reduction_alg.getProperty("OutputWorkspaceLAB").value

        # Evaluate it up to a defined point
        reference_file_name = "SANS2D_ws_D20_reference_after_masking"
        self._compare_workspace(output_workspace, reference_file_name)


class SANSReductionRunnerTest(stresstesting.MantidStressTest):
    def __init__(self):
        stresstesting.MantidStressTest.__init__(self)
        self._success = False

    def runTest(self):
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(SANSSingleReductionTest, 'test'))
        runner = unittest.TextTestRunner()
        res = runner.run(suite)
        if res.wasSuccessful():
            self._success = True

    def requiredMemoryMB(self):
        return 2000

    def validate(self):
        return self._success


if __name__ == '__main__':
    unittest.main()
