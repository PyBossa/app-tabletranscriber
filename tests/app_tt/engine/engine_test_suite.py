import tests.app_tt.engine.test_application as test_application
import tests.app_tt.engine.test_api as test_api
import tests.app_tt.engine.test_workflow as test_workflow 

import unittest

if __name__ == "__main__" :
    suite_api = test_api.suite()
    suite_app = test_application.suite()
    suite_workflow = test_workflow.suite()
     
    alltests = unittest.TestSuite([
                                   suite_api, 
                                   suite_app, 
                                   suite_workflow
                                   ])

    unittest.TextTestRunner(verbosity=2).run(alltests)