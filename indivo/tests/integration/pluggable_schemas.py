import os
import settings
import sys
import json

from lxml import etree

from indivo.document_processing import IndivoSchemaLoader

from indivo.tests.internal_tests import TransactionInternalTests
from indivo.tests.data import TEST_ACCOUNTS, TEST_RECORDS, TEST_TESTMED_JSON

class PluggableSchemaIntegrationTests(TransactionInternalTests):

    def setUp(self):
        super(PluggableSchemaIntegrationTests,self).setUp()

        # Create an Account (with a few records)
        self.account = self.createAccount(TEST_ACCOUNTS, 4)

        # Add a record for it
        self.record = self.createRecord(TEST_RECORDS, 0, owner=self.account)
        
        # Add in TestMed class
        model_definition = open(os.path.join(settings.APP_HOME, 'indivo/tests/data_models/test/testmodel/model.sdml')).read()
        self.required_classes = self.load_classes_from_sdml(model_definition)
        
        # load the test schemas
        self.loader = IndivoSchemaLoader(os.path.join(settings.APP_HOME, 'indivo/tests/schemas/test'))
        self.loader.import_schemas()        

    def tearDown(self):
        # Unregister the schemas
        self.loader.unregister_all_schemas()
        
        # Unregister TestMed, reset the DB
        self.unload_classes(self.required_classes)

        self.required_classes = []
        super(PluggableSchemaIntegrationTests,self).tearDown()
        
    def test_nested_model_json(self):
        # post new document with a TestMed
        test_med_data = open(os.path.join(settings.APP_HOME, 'indivo/tests/schemas/test/testmed/testmed.xml')).read()
        response = self.client.post('/records/%s/documents/'%(self.record.id), 
                                    test_med_data,'application/xml')
        self.assertEquals(response.status_code, 200)

        # get a JSON encoded report on TestMed
        response = self.client.get('/records/%s/reports/TestMed/'%(self.record.id), {'response_format':'application/json'})
        self.assertEquals(response.status_code, 200)

        # parse response and check against expected         
        response_json = json.loads(response.content)
        self.assertEquals(len(response_json), 1) 
        expected_json = json.loads(TEST_TESTMED_JSON)
        self.assertTrue(response_json == expected_json, "JSON does not match expected")
        
    def test_nested_model_xml(self):
        # post new document with a TestMed
        test_med_data = open(os.path.join(settings.APP_HOME, 'indivo/tests/schemas/test/testmed/testmed.xml')).read()
        response = self.client.post('/records/%s/documents/'%(self.record.id), 
                                    test_med_data,'application/xml')
        self.assertEquals(response.status_code, 200)
        
        # get a JSON encoded report on TestMed
        response = self.client.get('/records/%s/reports/TestMed/'%(self.record.id), {'response_format':'application/xml'})
        self.assertEquals(response.status_code, 200)

        # parse response and check          
        response_xml = etree.XML(response.content)
        test_meds = response_xml.findall('./Model')
        self.assertEqual(len(test_meds), 1)
        test_med = test_meds[0]
        
        # check TestMed
        self.assertEqual(len(test_med.findall('Field')), 6, "expected 6 fields on TestMed")
        self.assertEqual(test_med.get('name'), 'TestMed')
        self.assertEqual(test_med.find('Field[@name="date_started"]').text, '2010-10-01T00:00:00Z')
        self.assertEqual(test_med.find('Field[@name="name"]').text, 'ibuprofen')
        self.assertEqual(test_med.find('Field[@name="brand_name"]').text, 'Advil')
        self.assertEqual(float(test_med.find('Field[@name="frequency"]').text), 2)
        
        # test TestPrescription
        test_prescription = test_med.find('./Field[@name="prescription"]/Model')
        self.assertTrue(test_prescription is not None, "prescription not found")
        self.assertEqual(test_prescription.find('Field[@name="prescribed_by_name"]').text, 'Kenneth D. Mandl')
        self.assertEqual(test_prescription.find('Field[@name="prescribed_on"]').text, '2010-09-30T00:00:00Z')

        # test TestFill
        test_fills = test_med.findall('./Field[@name="fills"]/Models/Model')
        self.assertEqual(len(test_fills), 2)
        self.assertEqual(test_fills[0].get("name"), "TestFill")
        self.assertEqual(float(test_fills[0].find('Field[@name="supply_days"]').text), 15.0)
        
    def test_nonexistent_model(self):  
        # get a JSON encoded report on a non-existent model
        response = self.client.get('/records/%s/reports/DoesNotExist/'%(self.record.id), {'response_format':'application/json'})
        self.assertEquals(response.status_code, 404)
        
    def test_default_response_format(self):
        # post new document with a TestMed
        test_med_data = open(os.path.join(settings.APP_HOME, 'indivo/tests/schemas/test/testmed/testmed.xml')).read()
        response = self.client.post('/records/%s/documents/'%(self.record.id), 
                                    test_med_data,'application/xml')
        self.assertEquals(response.status_code, 200)
        
        # request TestMed report without specifying response_format
        response = self.client.get('/records/%s/reports/TestMed/'%(self.record.id))
        self.assertEquals(response.status_code, 200)
        
        # should get back JSON
        self.assertEquals(response.__getitem__('content-type'), 'application/json')
        response_json = json.loads(response.content)
        expected_json = json.loads(TEST_TESTMED_JSON)
        self.assertTrue(response_json == expected_json, "JSON does not match expected")
        
    def test_unsupported_response_format(self):
        # post new document with a TestMed
        test_med_data = open(os.path.join(settings.APP_HOME, 'indivo/tests/schemas/test/testmed/testmed.xml')).read()
        response = self.client.post('/records/%s/documents/'%(self.record.id), 
                                    test_med_data,'application/xml')
        self.assertEquals(response.status_code, 200)
        
        # request an unsupported response_format
        response = self.client.get('/records/%s/reports/TestMed/'%(self.record.id), {'response_format':'application/junk'})
        self.assertEquals(response.status_code, 400)
        
    def test_core_model_json(self):
        #Add some sample Reports
        self.loadTestReports(record=self.record)
        
        response = self.client.get('/records/%s/reports/Lab/'%(self.record.id))
        self.assertEquals(response.status_code, 200)
        
        response_json = json.loads(response.content)
        self.assertTrue(len(response_json), 4)

        # check to make sure Model name is correct, and that it has 13 fields        
        first_lab = response_json[0]
        self.assertEquals(first_lab['__modelname__'], 'Lab')
        self.assertEquals(len(first_lab), 13)
        
    def test_core_model_xml(self):
        #Add some sample Reports
        self.loadTestReports(record=self.record)
        
        response = self.client.get('/records/%s/reports/Lab/'%(self.record.id), {'response_format':'application/xml'})
        self.assertEquals(response.status_code, 200)
        
         # parse response and check          
        response_xml = etree.XML(response.content)
        labs = response_xml.findall('./Model')
        self.assertEqual(len(labs), 4)
        lab = labs[0]
        
        self.assertEqual(len(lab.findall('Field')), 12)
        self.assertEqual(lab.get('name'), 'Lab')
        