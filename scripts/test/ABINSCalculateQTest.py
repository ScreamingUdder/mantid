import unittest
import numpy as np
from mantid.simpleapi import *

from os import path

try:
    import simplejson as json
except ImportError:
    logger.warning("Failure of CalculateQTest because simplejson is unavailable.")
    exit(1)

try:
    import scipy
except ImportError:
    logger.warning("Failure of CalculateQTest because scipy is unavailable.")
    exit(1)

try:
    import h5py
except ImportError:
    logger.warning("Failure of CalculateQTest because h5py is unavailable.")
    exit(1)

from AbinsModules import  CalculateQ
from AbinsModules import KpointsData
from AbinsModules.InstrumentProducer import InstrumentProducer
from AbinsModules import AbinsParameters


class ABINSCalculateQTest(unittest.TestCase):

    def setUp(self):
        _core = "../ExternalData/Testing/Data/UnitTest/"
        producer = InstrumentProducer()
        self._tosca_instrument = producer.produceInstrument("TOSCA")
        self._filename = path.relpath(_core + "Si2-sc_Q_test.phonon")

    def test_simple(self):
        """
        Tests various  assertions
        """

        # wrong file name
        with self.assertRaises(ValueError):
            poor_q_calculator = CalculateQ(filename=1, instrument=self._tosca_instrument, sample_form="Powder")

        # wrong instrument
        with self.assertRaises(ValueError):
            poor_q_calculator = CalculateQ(filename=self._filename, instrument="Different_instrument", sample_form="Powder")

        # wrong sample form
        with self.assertRaises(ValueError):
            poor_q_calculator = CalculateQ(filename=self._filename, instrument=self._tosca_instrument, sample_form="Solid")

        # no frequencies required for the case when Q vectors do not depend on frequencies
        poor_q_calculator = CalculateQ(filename=self._filename, sample_form="Powder")
        with self.assertRaises(ValueError):
            poor_q_calculator.collectFrequencies(k_points_data=np.array([1, 2, 3, 4]))


    _core = "../ExternalData/Testing/Data/UnitTest/"

    # Use case: TOSCA
    def test_TOSCA(self):

        raw_data = KpointsData(num_k=1, num_atoms=2)

        raw_data.set({"k_vectors":np.asarray([[0.2, 0.1, 0.2]]),
                      "weights":np.asarray([0.3]),
                      "frequencies":np.asarray([[1.0, 2.0, 3.0, 4.0,  5.0, 6.0]]),  # 6 frequencies
                      "atomic_displacements":np.asarray([[[[1.0,1.0,1.0],[1.0,1.0,1.0],  [1.0,1.0,1.0],
                                                         [1.0,1.0,1.0],[1.0,1.0,1.0],  [1.0,1.0,1.0]],

                                                         [[1.0,1.0,1.0],[1.0,1.0,111.0],[1.0,1.0,1.0],
                                                         [1.0,1.0,1.0],[1.0,1.0,1.0],  [1.0,1.0,1.0]]]]).astype(complex)}) # 12 atomic displacements
        extracted_raw_data = raw_data.extract()
        correct_q_data = ((extracted_raw_data["frequencies"][0] / AbinsParameters.cm1_2_hartree) *
                          (extracted_raw_data["frequencies"][0] / AbinsParameters.cm1_2_hartree) /
                          16.0)

        producer = InstrumentProducer()
        tosca_instrument = producer.produceInstrument("TOSCA")
        q_calculator = CalculateQ(filename=self._filename,
                                  instrument=self._tosca_instrument,
                                  sample_form="Powder")
        q_calculator.collectFrequencies(k_points_data=raw_data)
        q_vectors = q_calculator.calculateData()

        # noinspection PyTypeChecker
        self.assertEqual(True,np.allclose(correct_q_data, q_vectors.extract()))

        loaded_q = q_calculator.loadData()

        # noinspection PyTypeChecker
        self.assertEqual(True,np.allclose(correct_q_data, loaded_q.extract()))

        # here we have a list not a KpointsData
        with self.assertRaises(ValueError):
            q_calculator.collectFrequencies([1,2,3])


    # Helper functions
    def _prepare_data(self, name=None):
        """Reads a corrects values from ASCII file."""
        correct_data = None
        with open(self._core+"CalculateQ_"+name+"_data.txt") as data_file:
            correct_data = json.loads(data_file.read().replace("\n"," ").
                                      replace("array","").
                                      replace("([","[").
                                      replace("])","]").
                                      replace(".,",".0,").
                                      replace(".]",".0]").
                                      replace(". ",".0").
                                      replace("'",'"'))



        return np.array(correct_data)



if __name__ == '__main__':
    unittest.main()
