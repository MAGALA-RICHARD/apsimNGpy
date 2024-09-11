from experiment_utils import _run_experiment, experiment_runner, define_factor, define_cultivar


class Experiment:
    def __init__(self, **kwargs):
        self.define_cultivar = define_cultivar
        self.define_factor = define_factor
        self.data = []

    def add_factor(self, factor_type, **kwargs):
        if factor_type == 'management' or factor_type == 'soils':
            self.data.append(self.define_factor(factor_type=factor_type, **kwargs))
        else:
            self.data.append(self.define_cultivar(**kwargs))

    def test_experiment(self):
        """
        this function will test the experiment set up to be called by the user before running start a few things to
        check reports supplied really exist in the simulations, and the data tables are serializable into the sql
        database

        """

    def start_experiment(self):
        """
        This will run the experiment
        """

    def get_simulated_data(self):
        ...

    def end_experiment(self):
        """
        cleans up stuff
        """


if __name__ == '__main__':
    og = Experiment()
    og.add_factor(parameter='Carbon', param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
    og.add_factor(parameter='BD', param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Physical')
    print(len(og.data))
