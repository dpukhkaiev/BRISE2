import pytest
from typing import Union
from configuration_selection.configuration_selection import ConfigurationSelection
from configuration_selection.model.surrogate.model_mock import ModelMock
from configuration_selection.model.surrogate.tree_parzen_estimator import TreeParzenEstimator
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from default_config_handler.default_configuration_handler_orchestrator import DefaultConfigHandlerOrchestrator
from core_entities.experiment import Experiment
from core_entities.configuration import Configuration
from core_entities.search_space import get_search_space_record
from tools.restore_db import RestoreDB

rdb = RestoreDB()


class TestConfigurationSelection:

    def test_0(self, get_experiment, get_workers, get_configurations_2_float):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'tpe', 'surr.vt.none', 'surr.ct',
        'optimizer.moea', 'opt.vt', 'opt.ct', 'validator.none', 'cs.best',
        'ted.quantity', 'mr.dynamic', 'mtl.oldnewratio', 'mtl.onlybest',
        'sc.bad', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(0)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_2_float[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        cs = ConfigurationSelection(experiment)
        assert isinstance(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                              0], TreeParzenEstimator)
        configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_2_float[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # Scalar
        assert isinstance(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                              0].surrogate_instance, GaussianProcessRegressor)
        experiment.dump("Results")

    def test_1(self, get_experiment, get_workers, get_configurations_float_nom):
        """
        ['1 float 1 nom', 'flat', '2-mo', 'scalar', 'sklearn', 'surr.vt', 'surr.ct',
        'optimizer.moea', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal.none' 'cs.random',
        'ted.none', 'mr.none', 'mtl.none', 'sc.time', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        experiment_description, search_space = get_experiment(1)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            # Update to 2-Objectives
            results = get_configurations_float_nom[i]['Result']
            del results["Y3"]
            del results["Y4"]
            del results["Y5"]
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # Scalar
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])

    def test_2(self, get_experiment, get_workers, get_configurations_all_types):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', '5-mo', 'pure', 'gpr-gpr',
         'surr.vt.none', 'surr.ct',  'optimizer.nsga2-moead', 'opt.ct',, 'opt.vt.none'
         'validator.quality', 'validator.internal.none' , 'cs.random',
         'ted.none', 'mr.none', 'mtl.none', 'sc.guaranteed', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        experiment_description, search_space = get_experiment(2)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        configs = []
        hierarchical_configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            predicted[0].results = get_configurations_all_types[i]['Result']
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            hierarchical_configs = hierarchical_configs + measured
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])

        assert all([len(c.parameters) == 3 for c in configs]) is True
        assert all([len(c.parameters) == 3 for c in hierarchical_configs]) is True

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # Pure
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])

    def test_3(self, get_experiment, get_workers, get_configurations_all_types):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'flat', '5-mo', 'compositional', 'tpe', 'tpe', 'tpe', 'tpe', 'tpe',
         'surr.vt.none', 'surr.ct', 'optimizer.gaco', 'optimizer.gaco', 'optimizer.gaco',
         'optimizer.gaco', 'optimizer.gaco', 'opt.vt', 'opt.ct','validator.mock', 'validator.internal.none',
         'cs.best', 'ted.none', 'mr.none', 'mtl.none', 'sc.bad', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        experiment_description, search_space = get_experiment(3)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        configs = []
        hierarchical_configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            predicted[0].results = get_configurations_all_types[i]['Result']
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            hierarchical_configs = hierarchical_configs + measured
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])

        assert all([len(c.parameters) == 5 for c in configs]) is True
        assert all([len(c.parameters) == 3 for c in hierarchical_configs]) is True

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 5  # Compositional
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])

    def test_4(self, get_experiment, get_workers, get_configurations_float_nom):
        """
        ['1 float 1 nom', 'flat', 'so', 'mo.none', 'brr', 'surr.vt.none', 'surr.ct',
        'optimizer.nsga2', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.none', 'mtl.fsl', 'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(4)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_float_nom[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_float_nom[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_float_nom[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        assert predicted[0].type is Configuration.Type.TRANSFERRED
        experiment.add_configuration(predicted[0])

        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_5(self, get_experiment, get_workers, get_configurations_2_float):
        """
        ['2 float', 'flat', '2-mo', 'dynamic', 'mock', 'sklearn', 'sklearn', 'sklearn', 'sklearn', 'surr.vt.none',
        'surr.ct.none', 'optimizer.moead', 'opt.vt.none', 'opt.ct', 'validator.quality', 'validator.internal',
         'cs.random', 'ted.none', 'mr.none', 'mtl.none',
        'sc.time', 'rm.experiment_aware', 'dch.random', 'ss.mersenne']
        """
        experiment_description, search_space = get_experiment(5)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = get_configurations_2_float[10]['Result']
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        experiment.evaluated_configurations.append(default_configuration)
        experiment.measured_configurations.append(default_configuration)

        configs = []
        hierarchical_configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = get_configurations_2_float[i]['Result']
            del results["Y3"]
            del results["Y4"]
            del results["Y5"]
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            hierarchical_configs = hierarchical_configs + measured
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 11  # DynamicCompositional
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])


    def test_6(self, get_experiment, get_workers, get_configurations_float_nom):
        """
         ['1 float 1 nom', 'flat', '5-mo', 'pf', 'gpr', 'lr', 'mock', 'surr.vt.none',
         'surr.ct', 'optimizer.random', 'opt.vt.none', 'opt.ct','validator.quality', 'validator.internal',
         'cs.random', 'ted.none', 'mr.none', 'mtl.none', 'sc.guaranteed', 'rm.quality', 'dch.none', 'ss.mersenne']
        """
        experiment_description, search_space = get_experiment(6)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            predicted[0].results = get_configurations_float_nom[i]['Result']
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i+1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])


        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 17  # Portfolio 5 Obj 3 Surr 2 MO 15 + 2
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])

    def test_7(self, get_experiment, get_workers, get_configurations_2_float):
        """
         ['2 float', 'flat', '5-mo', 'pure', 'sklearn', 'surr.vt.none', 'surr.ct', 'optimizer.nsga2', 'opt.ct',
         'validator.quality', 'validator.internal.none','cs.random', 'ted.none', 'mr.none', 'mtl.none',
         'sc.guaranteed', 'rm.experiment_aware', 'dch.random', 'ss.sobol']
        """
        experiment_description, search_space = get_experiment(7)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = get_configurations_2_float[10]['Result']
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.evaluated_configurations.append(default_configuration)
        experiment.measured_configurations.append(default_configuration)

        configs = []
        for i in range(20):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            predicted[0].results = get_configurations_2_float[i]['Result']
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i+1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])


        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # Pure
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])

    def test_8(self, get_experiment, get_workers, get_configurations_all_types):
        """
         ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', '2-mo', 'scalar-pf', 'mab', 'lr-gbr-brr-mock',
         'surr.vt', 'surr.ct', 'optimizer.random', 'opt.vt.none', 'opt.ct.none',
         'validator.mock-q', 'validator.internal.none-y', 'cs.best', 'ted.none',
         'mr.none', 'mtl.none', 'sc.time', 'rm.quality', 'dch.none', 'ss.sobol']
        """
        experiment_description, search_space = get_experiment(8)
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # Scalar
        second_region = list(cs.predictor.mapping_region_model.keys())[1]
        assert len(cs.predictor.mapping_region_model[second_region].mapping_surrogate_objective) == 9  # PF 2 Obj 4 Surr 1 MO

        configs = []
        for i in range(40):
            j = i
            if i > 19:
                j = i - 20
            predicted, _ = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = get_configurations_all_types[j]['Result']
            if not i > 19:
                del results["Y3"]
                del results["Y4"]
                del results["Y5"]
            predicted[0].results = results
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])

        assert all([len(c.parameters) == 3 for c in configs]) is True
        assert any([c.type is Configuration.Type.PREDICTED for c in configs])

    def test_9(self, get_experiment, get_workers, get_configurations_float_nom):
        """
        ['1 float 1 nom', 'flat', 'so', 'mo.none', 'mock', 'surr.vt.none', 'surr.ct.none',
        'optimizer.gaco', 'opt.vt.none', 'opt.ct',  'validator.mock', 'validator.internal.none', cs.random',
        'ted.quantity', 'mr.fsl', 'mtl.oldnewratio-fsl', 'sc.fsl', 'rm.quality', 'dch.random', 'ss.sobol']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(9)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_float_nom[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        configs = []
        # assert isinstance(list(cs.predictor.mapping_region_model[
        #                            list(cs.predictor.mapping_region_model)[0]].mapping_surrogate_objective.keys())[0],
        #                   ModelMock)
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_float_nom[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_float_nom[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        assert predicted[0].type is Configuration.Type.TRANSFERRED
        experiment.add_configuration(predicted[0])
        # assert isinstance(list(cs.predictor.mapping_region_model[
        #                            list(cs.predictor.mapping_region_model)[0]].mapping_surrogate_objective.keys())[0],
        #                   TreeParzenEstimator)


        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_10(self, get_experiment, get_workers, get_configurations_2_float):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'gbr', 'surr.vt.none', 'surr.ct.none', 'optimizer.random',
        'opt.vt.none', 'opt.ct.none', 'validator.mock', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.dynamic', 'mtl.onlybest', 'sc.time', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(10)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_2_float[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        assert isinstance(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                              0].surrogate_instance, GradientBoostingRegressor)
        configs = []
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_2_float[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_2_float[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        experiment.add_configuration(predicted[0])
        assert isinstance(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                              0].surrogate_instance, GaussianProcessRegressor)
        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_11(self, get_experiment, get_workers, get_configurations_all_types):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float, 'hierarchical', 'so', 'mo.none', 'mab-brr',
        'surr.vt.none', 'surr.ct.none-y', 'optimizer.bee-gwo', 'opt.vt.none', 'opt.ct.y-none',
        'validator.mock', 'validator.internal.none', 'cs.random', 'ted.quantity', 'mr.none',
        'mtl.oldnewratio-onlybest', 'sc.guaranteed', 'rm.experiment_aware', 'dch.none', 'ss.mersenne']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(11)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_all_types[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_all_types[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_all_types[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        experiment.add_configuration(predicted[0])
        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_12(self, get_experiment, get_workers, get_configurations_all_types):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float', 'hierarchical', 'so', 'mo.none', 'framab-tpe',
        'surr.vt.none', 'surr.ct.none-y', 'optimizer.de-cmaes', 'opt.vt.none-af', 'opt.ct.y-none',
        'validator.mock', 'validator.internal.none', 'cs.best', 'ted.none', 'mr.fsl', 'mtl.none',
        'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(12)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_all_types[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_all_types[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_all_types[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        experiment.add_configuration(predicted[0])
        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_13(self, get_experiment, get_workers, get_configurations_all_types):
        """
        ['1 nom 1 float 1 nom 1 ord 1 float', 'flat', 'so', 'mo.none', 'brr', 'surr.vt.none', 'surr.ct',
        'optimizer.sade', 'opt.vt.none', 'opt.ct', 'validator.mock', 'validator.internal.none', 'cs.random',
        'ted.quantity', 'mr.dynamic', 'mtl.none', 'sc.bad', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(13)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_all_types[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_all_types[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_all_types[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        experiment.add_configuration(predicted[0])
        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_14(self, get_experiment, get_workers, get_configurations_2_float):
        """
        ['2 float', 'flat', 'so', 'mo.none', 'lr', 'surr.vt.none', 'surr.ct.none',
        'optimizer.pso', 'opt.vt.none', 'opt.ct.none',  'validator.mock', 'validator.internal.none', 'cs.best',
        'ted.quantity', 'mr.fsl', 'mtl.none', 'sc.fsl', 'rm.experiment_aware', 'dch.none', 'ss.sobol']
        """
        rdb.cleanup()
        rdb.restore()
        experiment_description, search_space = get_experiment(14)
        experiment = Experiment(experiment_description, search_space)
        experiment.database.write_one_record("Experiment_description", experiment.get_experiment_description_record())
        experiment.database.write_one_record(
            "Search_space", get_search_space_record(search_space, experiment.unique_id)
        )
        dch_o = DefaultConfigHandlerOrchestrator()
        default_config_handler = dch_o.get_default_configuration_handler(experiment=experiment)
        default_configuration = default_config_handler.get_default_configuration()
        assert isinstance(default_configuration, Configuration)
        default_configuration.results = {"Y1": get_configurations_2_float[10]['Result']["Y1"]}
        default_configuration.status['measured'] = True
        default_configuration.status['evaluated'] = True
        experiment.default_configuration = default_configuration
        Configuration.set_task_config(experiment.description["Context"]["TaskConfiguration"])
        cs = ConfigurationSelection(experiment)
        assert isinstance(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                              0].surrogate_instance, LinearRegression)
        configs = []
        for i in range(0, 9):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            results = {"Y1": get_configurations_2_float[i]['Result']["Y1"]}
            predicted[0].results = results
            predicted[0].status['enabled'] = True
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type is Configuration.Type.FROM_SELECTOR
            experiment.add_configuration(predicted[0])

            experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
            experiment.send_state_to_db()

        predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
        results = {"Y1": get_configurations_2_float[10]['Result']["Y1"]}
        predicted[0].results = results
        predicted[0].status['enabled'] = True
        predicted[0].status['measured'] = True
        predicted[0].status['evaluated'] = True
        configs = configs + predicted
        assert len(configs) == 10
        experiment.add_configuration(predicted[0])
        assert isinstance(list(list(cs.predictor.mapping_region_model.values())[0].mapping_surrogate_objective.keys())[
                              0].surrogate_instance, GaussianProcessRegressor)
        experiment.database.write_one_record("Configuration", predicted[0].get_configuration_record())
        experiment.send_state_to_db()

        temp_region = list(cs.predictor.mapping_region_model.keys())[0]
        assert len(cs.predictor.mapping_region_model[temp_region].mapping_surrogate_objective) == 1  # SO
        experiment.dump("Results")

    def test_15(self, get_energy_experiment_and_search_space, get_workers, get_energy_configurations):
        """
        Energy experiment, test energy validator
        """
        experiment_description, search_space = get_energy_experiment_and_search_space
        experiment = Experiment(experiment_description, search_space)
        cs = ConfigurationSelection(experiment)
        configs = []
        for i in range(30):
            predicted, measured = cs.send_new_configurations_to_measure("", "", "", get_workers)
            predicted[0].results = get_energy_configurations[i]['Result']
            predicted[0].status['measured'] = True
            predicted[0].status['evaluated'] = True
            configs = configs + predicted
            assert len(configs) == i + 1
            assert predicted[0].type in [Configuration.Type.FROM_SELECTOR, Configuration.Type.PREDICTED]
            experiment.measured_configurations.append(predicted[0])

        assert any([c.type is Configuration.Type.PREDICTED for c in configs])
