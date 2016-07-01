#pylint: disable=no-init,invalid-name
import mantid
from mantid.kernel import Direction, StringArrayProperty, StringListValidator
import sys

try:
    from plotly import tools as toolsly
    from plotly.offline import plot
    import plotly.graph_objs as go
    have_plotly = True
except ImportError:
    have_plotly = False


class SavePlot1D(mantid.api.PythonAlgorithm):

    _wksp = None

    def category(self):
        """ Category
        """
        return "DataHandling\\Plots"

    def name(self):
        """ Algorithm name
        """
        return "SavePlot1D"

    def summary(self):
        return "Save 1D plots to a file"

    def checkGroups(self):
        return False

    def PyInit(self):
        self.declareProperty(mantid.api.WorkspaceProperty('InputWorkspace', '',
                                                          mantid.kernel.Direction.Input),
                             'Workspace to plot')
        self.declareProperty(mantid.api.FileProperty('OutputFilename', '',
                                                     action=mantid.api.FileAction.OptionalSave,
                                                     extensions=['.png']),
                             doc='Name of the image file to savefile.')
        if have_plotly:
            outputTypes = ['image', 'plotly', 'plotly-full']
        else:
            outputTypes = ['image']
        self.declareProperty('OutputType', 'image',
                             StringListValidator(outputTypes),
                             'Method for rendering plot')
        self.declareProperty('XLabel', '',
                             'Label on the X axis. If empty, it will be taken from workspace')
        self.declareProperty('YLabel', '',
                             'Label on the Y axis. If empty, it will be taken from workspace')
        self.declareProperty(StringArrayProperty('SpectraNames', [], direction=Direction.Input),
                             'Override with custom names for spectra')
        self.declareProperty('Result', '', Direction.Output)

    def validateInputs(self):
        messages = {}
        outputType = self.getProperty('OutputType').value
        if outputType != 'plotly':
            filename = self.getProperty('OutputFilename').value
            if len(filename.strip()) <= 0:
                messages['OutputFilename'] = 'Required for OutputType != plotly'

        return messages

    def PyExec(self):
        self._wksp = self.getProperty("InputWorkspace").value
        outputType = self.getProperty('OutputType').value

        if outputType == 'image':
            result = self.saveImage()
        else:
            result = self.savePlotly(outputType == 'plotly-full')

        self.setProperty('Result', result)

    def getData(self, ws, wkspIndex, label=''):
        x = ws.readX(wkspIndex)
        y = ws.readY(wkspIndex)
        if x.size == y.size+1:
            x = (x[:-1]+x[1:])*0.5

        # use suggested label
        if len(label.strip()) > 0:
            return (x, y, label)

        # determine the label from the data
        ax = ws.getAxis(1)
        if ax.isSpectra():
            label = ax.label(wkspIndex)
        else:
            LHS = a.title()
            if LHS == "":
                LHS = ax.getUnit().caption()
            label = LHS + " = " + str(float(ax.label(wkspIndex)))

        return (x, y, label)

    def getAxesLabels(self, ws, utf8=False):
        xlabel = self.getProperty('XLabel').value
        if xlabel == '':
            xaxis = ws.getAxis(0)
            if utf8:
                unitLabel = xaxis.getUnit().symbol().utf8()
            else:  # latex markup
                unitLabel = '$' + xaxis.getUnit().symbol().latex() + '$'
            xlabel = xaxis.getUnit().caption()+' ('+unitLabel+')'

        ylabel = self.getProperty('YLabel').value
        if ylabel == '':
            ylabel = ws.YUnit()
            if ylabel == '':
                ylabel = ws.YUnitLabel()

        return (xlabel, ylabel)

    def savePlotly(self, fullPage):
        spectraNames = self.getProperty('SpectraNames').value

        if type(self._wksp) == mantid.api.WorkspaceGroup:
            fig = toolsly.make_subplots(rows=self._wksp.getNumberOfEntries())

            for i in range(self._wksp.getNumberOfEntries()):
                wksp = self._wksp.getItem(i)
                (traces, xlabel, ylabel) = self.toScatterAndLabels(wksp, spectraNames)
                for spectrum in traces:
                    fig.append_trace(spectrum, i+1, 1)
                fig['layout']['xaxis%d' % (i+1)].update(title=xlabel)
                fig['layout']['yaxis%d' % (i+1)].update(title=ylabel)
                if len(spectraNames) > 0:  # remove the used spectra names
                    spectraNames = spectraNames[len(traces):]
        else:
            (traces, xlabel, ylabel) = self.toScatterAndLabels(self._wksp,
                                                               spectraNames)

            layout = go.Layout(yaxis={'title': ylabel},
                               xaxis={'title': xlabel})

            fig = go.Figure(data=traces, layout=layout)

        # extra arguments for div vs full page
        if fullPage:
            filename = self.getProperty("OutputFilename").value
            plotly_args = {'filename': filename}
        else:  # just the div
            plotly_args = {'output_type': 'div',
                           'include_plotlyjs': False}

        # render the plot
        div = plot(fig, show_link=False, **plotly_args)

        # decide what to return
        if fullPage:
            return filename
        else:
            return str(div)

    def toScatterAndLabels(self, wksp, spectraNames=[]):
        data = []
        for i in xrange(wksp.getNumberHistograms()):
            if len(spectraNames) > i:
                (x, y, label) = self.getData(wksp, i, spectraNames[i])
            else:
                (x, y, label) = self.getData(wksp, i)
            data.append(go.Scatter(x=x, y=y, name=label))

        (xlabel, ylabel) = self.getAxesLabels(wksp, utf8=True)

        return (data, xlabel, ylabel)

    def saveImage(self):
        ok2run = ''
        try:
            import matplotlib
            from distutils.version import LooseVersion
            if LooseVersion(matplotlib.__version__) < LooseVersion("1.2.0"):
                ok2run = 'Wrong version of matplotlib. Required >= 1.2.0'
        except ImportError:
            ok2run = 'Problem importing matplotlib'
        if len(ok2run) > 0:
            raise RuntimeError(ok2run)

        matplotlib = sys.modules['matplotlib']
        matplotlib.use('agg')
        import matplotlib.pyplot as plt

        if type(self._wksp) == mantid.api.WorkspaceGroup:
            num_subplots = self._wksp.getNumberOfEntries()
            fig, axarr = plt.subplots(num_subplots)
            for i in range(self._wksp.getNumberOfEntries()):
                self.doPlotImage(axarr[i], self._wksp.getItem(i))
        else:
            fig, ax = plt.subplots()
            self.doPlotImage(ax, self._wksp)

        plt.tight_layout(1.08)
        plt.show()
        filename = self.getProperty("OutputFilename").value
        plt.savefig(filename, bbox_inches='tight')

        return filename

    def doPlotImage(self, ax, ws):
        spectra = ws.getNumberHistograms()
        if spectra > 10:
            mantid.kernel.logger.warning("more than 10 spectra to plot")
        prog_reporter = mantid.api.Progress(self, start=0.0, end=1.0,
                                            nreports=spectra)

        for j in range(spectra):
            (x, y, plotlabel) = self.getData(ws, j)

            ax.plot(x, y, label=plotlabel)

            (xlabel, ylabel) = self.getAxesLabels(ws)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            prog_reporter.report("Processing")

        if 1 < spectra <= 10:
            ax.legend()

mantid.api.AlgorithmFactory.subscribe(SavePlot1D)
