import unittest
import mantid
import math

from SANS2.Common.SANSFunctions import (create_unmanaged_algorithm)
from SANS2.Common.SANSConstants import SANSConstants
from SANS2.State.StateDirector.TestDirector import TestDirector
from SANS2.State.StateBuilder.SANSStateScaleBuilder import get_scale_builder
from SANS2.State.StateBuilder.SANSStateDataBuilder import get_data_builder
from SANS2.Common.SANSType import (SANSFacility, SampleShape)


class SANSScaleTest(unittest.TestCase):
    @staticmethod
    def _get_workspace():
        sample_name = "CreateSampleWorkspace"
        sample_options = {"WorkspaceType": "Histogram",
                          "NumBanks": 1,
                          "BankPixelWidth": 1,
                          "OutputWorkspace": "test"}
        sample_alg = create_unmanaged_algorithm(sample_name, **sample_options)
        sample_alg.execute()
        workspace = sample_alg.getProperty("OutputWorkspace").value
        return workspace

    @staticmethod
    def _get_sample_state(width, height, thickness, shape, scale):
        # Arrange
        facility = SANSFacility.ISIS
        data_builder = get_data_builder(facility)
        data_builder.set_sample_scatter("LOQ74044")
        data_state = data_builder.build()

        scale_builder = get_scale_builder(data_state)
        scale_builder.set_scale(scale)
        scale_builder.set_thickness(thickness)
        scale_builder.set_width(width)
        scale_builder.set_height(height)
        scale_builder.set_shape(shape)
        scale_state = scale_builder.build()

        test_director = TestDirector()
        test_director.set_states(scale_state=scale_state, data_state=data_state)
        return test_director.construct()

    def test_that_scales_the_workspace_correctly(self):
        # Arrange
        workspace = self._get_workspace()
        width = 1.0
        height = 2.0
        scale = 7.2
        state = self._get_sample_state(width=width, height=height, thickness=3.0, scale=scale,
                                       shape=SampleShape.CylinderAxisUp)
        serialized_state = state.property_manager
        scale_name = "SANSScale"
        scale_options = {"SANSState": serialized_state,
                         SANSConstants.input_workspace: workspace,
                         SANSConstants.output_workspace: SANSConstants.dummy}
        scale_alg = create_unmanaged_algorithm(scale_name, **scale_options)

        # Act
        scale_alg.execute()
        output_workspace = scale_alg.getProperty(SANSConstants.output_workspace).value

        # Assert
        # We have a LOQ data set, hence we need to divide by pi
        expected_value = 0.3/(height * math.pi * math.pow(width, 2) / 4.0) * (scale / math.pi) * 100.
        data_y = output_workspace.dataY(0)
        tolerance = 1e-7
        self.assertTrue(abs(data_y[0] - expected_value) < tolerance)

if __name__ == '__main__':
    unittest.main()
