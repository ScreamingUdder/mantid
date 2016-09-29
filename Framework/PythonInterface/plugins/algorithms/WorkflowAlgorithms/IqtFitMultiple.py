#pylint: disable=no-init, too-many-instance-attributes
from __future__ import (absolute_import, division, print_function)

from mantid.api import (PythonAlgorithm, AlgorithmFactory, MatrixWorkspaceProperty,
                        ITableWorkspaceProperty, WorkspaceGroupProperty, Progress)
from mantid.kernel import Direction, FloatBoundedValidator, IntBoundedValidator, logger
from mantid.simpleapi import *


class IqtFitMultiple(PythonAlgorithm):

    _input_ws = None
    _function = None
    _fit_type = None
    _start_x = None
    _end_x = None
    _spec_min = None
    _spec_max = None
    _intensities_constrained = None
    _minimizer = None
    _max_iterations = None
    _result_name = None
    _parameter_name = None
    _fit_group_name = None


    def category(self):
        return "Workflow\\MIDAS"

    def summary(self):
        #pylint: disable=anomalous-backslash-in-string
        return "Fits an \*\_iqt file generated by I(Q,t)."

    def PyInit(self):
        self.declareProperty(MatrixWorkspaceProperty('InputWorkspace', '', direction=Direction.Input),
                             doc='The _iqt.nxs InputWorkspace used by the algorithm')

        self.declareProperty(name='Function', defaultValue='',
                             doc='The function to use in fitting')

        self.declareProperty(name='FitType', defaultValue='',
                             doc='The type of fit being carried out')

        self.declareProperty(name='StartX', defaultValue=0.0,
                             validator=FloatBoundedValidator(0.0),
                             doc="The first value for X")

        self.declareProperty(name='EndX', defaultValue=0.2,
                             validator=FloatBoundedValidator(0.0),
                             doc="The last value for X")

        self.declareProperty(name='SpecMin', defaultValue=0,
                             validator=IntBoundedValidator(0),
                             doc='Minimum spectra in the worksapce to fit')

        self.declareProperty(name='SpecMax', defaultValue=1,
                             validator=IntBoundedValidator(0),
                             doc='Maximum spectra in the worksapce to fit')

        self.declareProperty(name='Minimizer', defaultValue='Levenberg-Marquardt',
                             doc='The minimizer to use in fitting')

        self.declareProperty(name="MaxIterations", defaultValue=500,
                             validator=IntBoundedValidator(0),
                             doc="The Maximum number of iterations for the fit")

        self.declareProperty(name='ConstrainIntensities', defaultValue=False,
                             doc="If the Intensities should be constrained during the fit")

        self.declareProperty(MatrixWorkspaceProperty('OutputResultWorkspace', '', direction=Direction.Output),
                             doc='The outputworkspace containing the results of the fit data')

        self.declareProperty(ITableWorkspaceProperty('OutputParameterWorkspace', '', direction=Direction.Output),
                             doc='The outputworkspace containing the parameters for each fit')

        self.declareProperty(WorkspaceGroupProperty('OutputWorkspaceGroup', '', direction=Direction.Output),
                             doc='The OutputWorkspace group Data, Calc and Diff, values for the fit of each spectra')


    def validateInputs(self):
        self._get_properties()
        issues = dict()

        maximum_possible_spectra = self._input_ws.getNumberHistograms()
        maximum_possible_x = self._input_ws.readX(0)[self._input_ws.blocksize() - 1]
        # Validate SpecMin/Max

        if self._spec_max > maximum_possible_spectra:
            issues['SpecMax'] = ('SpecMax must be smaller or equal to the '\
             'number of spectra in the input workspace, %d' % maximum_possible_spectra)
        if self._spec_min < 0:
            issues['SpecMin'] = 'SpecMin can not be less than 0'
        if self._spec_max < self._spec_min:
            issues['SpecMax'] = 'SpecMax must be more than or equal to SpecMin'

        # Validate Start/EndX
        if self._end_x > maximum_possible_x:
            issues['EndX'] = ('EndX must be less than the highest x value in the workspace, %d' % maximum_possible_x)
        if self._start_x < 0:
            issues['StartX'] = 'StartX can not be less than 0'
        if self._start_x > self._end_x:
            issues['EndX'] = 'EndX must be more than StartX'

        return issues

    def _get_properties(self):
        self._input_ws = self.getProperty('InputWorkspace').value
        self._function = self.getProperty('Function').value
        self._fit_type = self.getProperty('FitType').value
        self._start_x = self.getProperty('StartX').value
        self._end_x = self.getProperty('EndX').value
        self._spec_min = self.getProperty('SpecMin').value
        self._spec_max = self.getProperty('SpecMax').value
        self._intensities_constrained = self.getProperty('ConstrainIntensities').value
        self._minimizer = self.getProperty('Minimizer').value
        self._max_iterations = self.getProperty('MaxIterations').value
        self._result_name = self.getPropertyValue('OutputResultWorkspace')
        self._parameter_name = self.getPropertyValue('OutputParameterWorkspace')
        self._fit_group_name = self.getPropertyValue('OutputWorkspaceGroup')

    def PyExec(self):

        setup_prog = Progress(self, start=0.0, end=0.1, nreports=4)
        setup_prog.report('generating output name')
        output_workspace = self._fit_group_name
        # check if the naming convention used is alreay correct
        chopped_name = self._fit_group_name.split('_')
        if 'WORKSPACE' in chopped_name[-1].upper():
            output_workspace = ('_').join(chopped_name[:-1])

        option = self._fit_type[:-2]
        logger.information('Option: '+ option)
        logger.information('Function: '+ self._function)

        setup_prog.report('Cropping workspace')
        #prepare input workspace for fitting
        tmp_fit_workspace = "__Iqtfit_fit_ws"
        if self._spec_max is None:
            CropWorkspace(InputWorkspace=self._input_ws, OutputWorkspace=tmp_fit_workspace,
                          XMin=self._start_x, XMax=self._end_x,
                          StartWorkspaceIndex=self._spec_min)
        else:
            CropWorkspace(InputWorkspace=self._input_ws, OutputWorkspace=tmp_fit_workspace,
                          XMin=self._start_x, XMax=self._end_x,
                          StartWorkspaceIndex=self._spec_min, EndWorkspaceIndex=self._spec_max)

        setup_prog.report('Converting to Histogram')
        ConvertToHistogram(tmp_fit_workspace, OutputWorkspace=tmp_fit_workspace)
        setup_prog.report('Convert to Elastic Q')
        self.convertToElasticQ(tmp_fit_workspace)

        #fit multi-domian functino to workspace
        fit_prog = Progress(self, start=0.1, end=0.8, nreports=2)
        multi_domain_func, kwargs = self._create_mutli_domain_func(self._function, tmp_fit_workspace)
        fit_prog.report('Fitting...')
        Fit(Function=multi_domain_func,
            InputWorkspace=tmp_fit_workspace,
            WorkspaceIndex=0,
            Output=output_workspace,
            CreateOutput=True,
            Minimizer=self._minimizer,
            MaxIterations=self._max_iterations,
            **kwargs)
        fit_prog.report('Fitting complete')

        conclusion_prog = Progress(self, start=0.8, end=1.0, nreports=5)
        conclusion_prog.report('Renaming workspaces')
        # rename workspaces to match user input
        if output_workspace + "_Workspaces" != self._fit_group_name:
            RenameWorkspace(InputWorkspace=output_workspace + "_Workspaces",
                            OutputWorkspace=self._fit_group_name)
        if output_workspace + "_Parameters" != self._parameter_name:
            RenameWorkspace(InputWorkspace=output_workspace + "_Parameters",
                            OutputWorkspace=self._parameter_name)

        conclusion_prog.report('Tansposing parameter table')
        self.transposeFitParametersTable(self._parameter_name)

        #set first column of parameter table to be axis values
        x_axis = mtd[tmp_fit_workspace].getAxis(1)
        axis_values = x_axis.extractValues()
        for i, value in enumerate(axis_values):
            mtd[self._parameter_name].setCell('axis-1', i, value)

        #convert parameters to matrix workspace
        parameter_names = 'A0,Intensity,Tau,Beta'
        conclusion_prog.report('Processing indirect fit parameters')
        result_workspace = ProcessIndirectFitParameters(InputWorkspace=self._parameter_name,
                                                        ColumnX="axis-1", XAxisUnit="MomentumTransfer",
                                                        ParameterNames=parameter_names,
                                                        OutputWorkspace=self._result_name)

        # create and add sample logs
        sample_logs  = {'start_x': self._start_x, 'end_x': self._end_x, 'fit_type': self._fit_type[:-2],
                        'intensities_constrained': self._intensities_constrained, 'beta_constrained': True}

        conclusion_prog.report('Copying sample logs')
        CopyLogs(InputWorkspace=self._input_ws, OutputWorkspace=result_workspace)
        CopyLogs(InputWorkspace=self._input_ws, OutputWorkspace=self._fit_group_name)

        log_names = [item for item in sample_logs]
        log_values = [sample_logs[item] for item in sample_logs]
        conclusion_prog.report('Adding sample logs')
        AddSampleLogMultiple(Workspace=result_workspace, LogNames=log_names, LogValues=log_values)
        AddSampleLogMultiple(Workspace=self._fit_group_name, LogNames=log_names, LogValues=log_values)

        DeleteWorkspace(tmp_fit_workspace)

        self.setProperty('OutputResultWorkspace', result_workspace)
        self.setProperty('OutputParameterWorkspace', self._parameter_name)
        self.setProperty('OutputWorkspaceGroup', self._fit_group_name)
        conclusion_prog.report('Algorithm complete')


    def _create_mutli_domain_func(self, function, input_ws):
        multi= 'composite=MultiDomainFunction,NumDeriv=true;'
        comp = '(composite=CompositeFunction,NumDeriv=true,$domains=i;' + function + ');'

        ties = []
        kwargs = {}
        num_spectra = mtd[input_ws].getNumberHistograms()
        for i in range(0, num_spectra):
            multi += comp
            kwargs['WorkspaceIndex_' + str(i)] = i

            if i > 0:
                kwargs['InputWorkspace_' + str(i)] = input_ws

                #tie beta for every spectrum
                tie = 'f%d.f1.Beta=f0.f1.Beta' % i
                ties.append(tie)

        ties = ','.join(ties)
        multi += 'ties=(' + ties + ')'

        return multi, kwargs

    def convertToElasticQ(self, input_ws, output_ws=None):
        from IndirectCommon import getEfixed
        """
        Helper function to convert the spectrum axis of a sample to ElasticQ.
        @param input_ws - the name of the workspace to convert from
        @param output_ws - the name to call the converted workspace
        """
        if output_ws is None:
            output_ws = input_ws

        axis = mtd[input_ws].getAxis(1)
        if axis.isSpectra():
            e_fixed = getEfixed(input_ws)
            ConvertSpectrumAxis(input_ws, Target='ElasticQ', EMode='Indirect', EFixed=e_fixed,
                                      OutputWorkspace=output_ws)

        elif axis.isNumeric():
            # Check that units are Momentum Transfer
            if axis.getUnit().unitID() != 'MomentumTransfer':
                raise RuntimeError('Input must have axis values of Q')

            CloneWorkspace(input_ws, OutputWorkspace=output_ws)
        else:
            raise RuntimeError('Input workspace must have either spectra or numeric axis.')
            
    def transposeFitParametersTable(self, params_table, output_table=None):
        """
        Transpose the parameter table created from a multi domain Fit.
        This function will make the output consistent with PlotPeakByLogValue.
        @param params_table - the parameter table output from Fit.
        @param output_table - name to call the transposed table. If omitted,
                the output_table will be the same as the params_table
        """
        params_table = mtd[params_table]
        table_ws = '__tmp_table_ws'
        table_ws = CreateEmptyTableWorkspace(OutputWorkspace=table_ws)
        param_names = params_table.column(0)[:-1]  # -1 to remove cost function
        param_values = params_table.column(1)[:-1]
        param_errors = params_table.column(2)[:-1]

        # Find the number of parameters per function
        func_index = param_names[0].split('.')[0]
        num_params = 0
        for i, name in enumerate(param_names):
            if name.split('.')[0] != func_index:
                num_params = i
                break

        # Create columns with parameter names for headers
        column_names = ['.'.join(name.split('.')[1:]) for name in param_names[:num_params]]
        column_error_names = [name + '_Err' for name in column_names]
        column_names = zip(column_names, column_error_names)
        table_ws.addColumn('double', 'axis-1')
        for name, error_name in column_names:
            table_ws.addColumn('double', name)
            table_ws.addColumn('double', error_name)

        # Output parameter values to table row
        for i in xrange(0, params_table.rowCount() - 1, num_params):
            row_values = param_values[i:i + num_params]
            row_errors = param_errors[i:i + num_params]
            row = [value for pair in zip(row_values, row_errors) for value in pair]
            row = [i / num_params] + row
            table_ws.addRow(row)

        if output_table is None:
            output_table = params_table.name()

        RenameWorkspace(table_ws.name(), OutputWorkspace=output_table)

AlgorithmFactory.subscribe(IqtFitMultiple)
