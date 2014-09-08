# Copyright 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from mock import patch

from ebcli.core.ebcore import EB
from integration.baseinttest import BaseIntegrationTest
from ebcli.resources.strings import strings
from ebcli.core import fileoperations
from ebcli.objects.sourcecontrol import NoSC

from botocore.exceptions import NoCredentialsError


class TestInit(BaseIntegrationTest):

    def test_init_standard(self):
        """
                testing for:
                1. Prompt for app name
                2. Ask to set up default region: Accept
                3. Create app
            """
        app_name = 'ebcli-intTest-app'

        # Set up mock responses
        self.mock_aws.make_api_call.side_effect = [
            {'Applications': []},  # describe call
            None  # create call, we don't need a return value
        ]

        self.mock_input.side_effect = [
            app_name,  # Application name
            'y',    # setup region
            '3',  # region
        ]

        # run cmd
        self.app = EB(argv=['init'])
        self.app.setup()
        self.app.run()
        self.app.close()

        # make sure everything happened
        self.mock_aws.make_api_call.assert_any_call(
            'elasticbeanstalk',
            'describe-applications',
            application_names=[app_name],
            region='us-west-2'
        )
        self.mock_aws.make_api_call.assert_called_with(
            'elasticbeanstalk',
            'create-application',
            application_name=app_name,
            description=strings['app.description'],
            region='us-west-2'
        )
        self.assertEqual(self.mock_input.call_count, 3)

    def test_init_no_creds(self):
        """
                testing for:
                1. Give app name as cli option
                4. Fail to create app (no credentials)
        """
        app_name = 'ebcli-intTest-app'

        # Set up mock responses
        self.mock_aws.make_api_call.side_effect = [
            NoCredentialsError,  # first describe call
            {'Applications': []},  # describe call
            None  # create call, we don't need a return value
        ]

        self.mock_input.side_effect = [
            '12345',  # access key
            'ABCDEF',  # Secret Key
        ]

        # run cmd
        self.app = EB(argv=['init', '-a', app_name, '-r', 'us-west-2'])
        self.app.setup()
        self.app.run()
        self.app.close()

        # make sure we were prompted for keys
        self.assertEqual(self.mock_input.call_count, 2)

    def test_init_override(self):
        """
                testing to make sure all options successfully override defaults
                 1. App name overrides config file app name
            """

        # setup config file
        fileoperations.create_config_file('savedAppName', 'saved-region')

        # Set up mock responses
        self.mock_aws.make_api_call.side_effect = [
            {'Applications': []},  # describe call
            None  # create call, we don't need a return value
        ]

        app_name = 'ebcli-intTest-app'

        # run cmd
        self.app = EB(argv=['init', '-a', app_name])
        self.app.setup()
        self.app.run()
        self.app.close()

        self.assertEqual(self.mock_input.call_count, 0)
        self.mock_output.assert_called_with('Application', app_name,
                                            'has been created')

    @patch('ebcli.core.operations.SourceControl')
    @patch('ebcli.core.io.log_warning')
    def test_init_no_git(self, mock_warning, mock_src_ctrl):
        """
                testing to make sure a warning is given if git is not installed
                1. Prompt for app name
                2. Create App
                3. Warn that git is not installed
        """
        # Set up mock responses
        self.mock_aws.make_api_call.side_effect = [
            {'Applications': []},  # describe call
            None  # create call, we don't need a return value
        ]
        mock_src_ctrl.get_source_control.return_value = NoSC()

        app_name = 'ebcli-intTest-app'

        # run cmd
        self.app = EB(argv=['init', '-a', app_name, '-r', 'us-west-w'])
        self.app.setup()
        self.app.run()
        self.app.close()

        mock_warning.assert_called_with(strings['git.notfound'])

    def test_init_repeat(self):
        """
                testing to make sure init doesnt override anything if
                called a second time
                All options previously entered should be persisted
        """

        # Set up mock responses
        self.mock_aws.make_api_call.side_effect = [
            {'Applications': []},  # describe call
            None,  # create call, we don't need a return value
            {'Applications': []},  # describe call
            None  # create call, we don't need a return value
        ]
        self.mock_input.side_effect = Exception('should not be called')


        app_name = 'ebcli-intTest-app'

        # run cmd
        self.app = EB(argv=['init', '-a', app_name, '-r', 'us-west-2'])
        self.app.setup()
        self.app.run()
        self.app.close()
        self.reset_backend()

        self.app = EB(argv=['init'])
        self.app.setup()
        self.app.run()
        self.app.close()

        self.assertEqual(self.mock_input.call_count, 0)

    def test_init_app_exists(self):
        """
                testing for:
                1. Prompt for app name
                2. Ask to set up credentials: Accept
                3. Ask to set up default region: Accept
                4. Create app

                Create app api should not be called because app exists
            """
        app_name = 'ebcli-intTest-app'

        # Set up mock responses
        self.mock_aws.make_api_call.side_effect = [
            {'Applications': [{'ApplicationName': 'myApp'}]},  # describe call
            {'Environments': []},  # get env's
            None  # create call, we don't need a return value
        ]

        self.mock_input.side_effect = [
            app_name,  # Application name
            'y',    # setup region
            '3',  # region
        ]

        self.app = EB(argv=['init'])
        self.app.setup()
        self.app.run()
        self.app.close()

        # make sure describe and get_all_environments were called
        #
        self.mock_aws.make_api_call.assert_any_call(
            'elasticbeanstalk',
            'describe-applications',
            application_names=[app_name],
            region='us-west-2'
        )
        self.mock_aws.make_api_call.assert_called_with(
            'elasticbeanstalk',
            'describe-environments',
            application_name=app_name,
            region='us-west-2'
        )
        self.assertEqual(self.mock_input.call_count, 3)