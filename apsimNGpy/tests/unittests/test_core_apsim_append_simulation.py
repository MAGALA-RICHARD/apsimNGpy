import sys
import unittest
from pathlib import Path

import numpy as np

from apsimNGpy import ApsimModel, timer
from apsimNGpy.exceptions import NodeNotFoundError
import asyncio

TOTAL = 100


@timer
def test_using_threads(run=False):
    with ApsimModel("Maize") as ap:
        ap.append_in_threads(TOTAL)
        print(len(ap))

        if run:
            ap.run()
            return ap.results.groupby('SimulationID')['Yield'].mean()


@timer
def test_append_no_threads():
    with ApsimModel("Maize") as ap:
        source = ap[0]
        tasks = [
            ap.append_simulation(
                source,
                rename=f"Simulation_{index}",
            )
            for index in range(TOTAL)
        ]
        ap.run()
        return ap.results.groupby('SimulationID')['Yield'].mean()



class TestCoreApsimAppendSimulation(unittest.TestCase):
    def assert_model_not_in(self, model, member, model_type, fullpath):
        """helper for finding whether model was deleted"""
        mns = model.inspect_model(model_type=model_type, fullpath=fullpath)
        self.assertNotIn(member, mns)

    def assert_model_in(self, model, member, model_type, fullpath):
        """helper for finding whether model was not deleted"""
        mns = model.inspect_model(model_type=model_type, fullpath=fullpath)
        self.assertIn(member, mns)

    def contained_changed(self, model, reference_count):
        container = model.inspect_model("Models.Core.Simulation")
        chg = len(container) > reference_count
        self.assertTrue(chg)

    @timer
    def _test_append_in_loop(self):
        import time
        tim = 0
        with ApsimModel('Maize') as ap:
            for count in np.arange(0, 10, 1):
                start = time.perf_counter()
                ap.append_simulation(ap[0], )
                end = time.perf_counter()
                tim += end - start
            print(tim)

    @timer
    def _test_core_apsim_append_simulation(self):
        with ApsimModel('Maize') as model:
            model.append_simulation(model[0], )
            self.assert_model_in(model, 'Simulation1', model_type='Models.Core.Simulation', fullpath=False)
            model.append_simulation(model[0], rename='Ss')
            self.assert_model_in(model, 'Ss', model_type='Models.Core.Simulation', fullpath=False)
            model.append_simulation(model[0], rename='St')
            self.assert_model_in(model, 'St', model_type='Models.Core.Simulation', fullpath=False)
            print('Testing no rename speed')
            model.append_simulation(model[1], )
            self.contained_changed(model, 4)
            model.append_simulation(model[0], )
            self.contained_changed(model, 5)
            model.append_simulation(model[0], )
            self.contained_changed(model, 6)
            model.append_simulation(model[0], )
            self.contained_changed(model, 7)
            model.append_simulation(model[0], )
            self.contained_changed(model, 8)
            model.append_simulation(model[0], rename='re')
            self.assert_model_in(model, 're', model_type='Models.Core.Simulation', fullpath=False)
            model.append_simulation(model[0], rename='11')
            self.assert_model_in(model, '11', model_type='Models.Core.Simulation', fullpath=False)
            model.append_simulation(model[0], rename='re')
            self.assert_model_in(model, 're', model_type='Models.Core.Simulation', fullpath=False)
            model.append_simulation(model[0], rename='12')
            self.assert_model_in(model, '12', model_type='Models.Core.Simulation', fullpath=False)


if __name__ == '__main__':
    test_using_threads()
    #test_append_no_threads()
