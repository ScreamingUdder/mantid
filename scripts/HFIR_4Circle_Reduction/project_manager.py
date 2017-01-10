import os

import mantid.simpleapi as mantidsimple
import pickle

# Project manager is in charge of importing and exporting a project


class ProjectManager(object):
    """
    Class project manager
    """
    def __init__(self, mode, project_file_path):
        """
        Initialization
        :param mode:  (1) import (2) export
        """
        self._mode = mode

        self._projectPath = project_file_path
        self._wsDir = self._projectPath + '.worksapces'

        self._variableDict = dict()

        self._wsList = list()

        return

    def add_workspaces(self, ws_name_list):
        """

        :param ws_name_list:
        :return:
        """
        self._wsList.extend(ws_name_list)

    def get(self, key):
        """

        :param key:
        :return:
        """
        return self._variableDict[key]

    def create_workspace_directory(self):
        """

        :return:
        """
        # use a fixed way to create a directory
        try:
            os.mkdir(self._wsDir)
        except OSError as os_err:
            if 'File exists:' not in str(os_err):
                raise os_err

        return

    def set(self, key, value):
        """
        Set parameter (can be any data structure) to project manager and then export data
        :param key:
        :param value:
        :return:
        """
        self._variableDict[key] = value

        return

    def export(self, overwrite=False):
        """
        Export the (ideally) whole project to disk
        :param overwrite: if specified, then any existing files with same name will be rewritten
        :return:
        """
        # create workspace directory
        self.create_workspace_directory()

        print '[INFO] Saving {0} MDEventWorkspaces to {1}.'.format(len(self._wsList), self._wsDir)

        # save MDs
        for ws_name in self._wsList:
            md_file_name = os.path.join(self._wsDir, ws_name + '.nxs')
            if overwrite or not os.path.exists(md_file_name):
                mantidsimple.SaveMD(InputWorkspace=ws_name, Filename=md_file_name)

        with open(self._projectPath, 'w') as pickle_file:
            pickle.dump(self._variableDict, pickle_file, pickle.HIGHEST_PROTOCOL)
            pickle.dump(self._wsList, pickle_file, pickle.HIGHEST_PROTOCOL)

        return

    def load(self):
        """

        :return:
        """
        # open file
        with open(self._projectPath, 'rb') as project_file:
            self._variableDict = pickle.load(project_file)
            self._wsList = pickle.load(project_file)

        # load data
        for ws_name in self._wsList:
            md_file_path = os.path.join(self._wsDir, ws_name + '.nxs')
            mantidsimple.LoadMD(Filename=md_file_path, OutputWorkspace=ws_name)
        # END-FOR

        return
