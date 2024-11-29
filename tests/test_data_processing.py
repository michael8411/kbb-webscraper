import sys
import os
import tempfile
import json
import unittest

# Adjust the import path if necessary
# If data_processing.py is in the parent directory, uncomment and adjust the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_processing import (
    load_existing_data,
    compare_and_update_data,
    save_data
)

class TestDataProcessing(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.test_dir.name, 'test_data.json')

    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()

    def test_load_existing_data_file_not_found(self):
        data = load_existing_data(self.test_file)
        self.assertEqual(data, {}, "Should return an empty dict when file is not found.")

    def test_load_existing_data_success(self):
        test_data = {'key1': 'value1', 'key2': 'value2'}
        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)
        data = load_existing_data(self.test_file)
        self.assertEqual(data, test_data, "Loaded data should match the saved data.")

    def test_load_existing_data_json_decode_error(self):
        with open(self.test_file, 'w') as f:
            f.write('Invalid JSON')
        data = load_existing_data(self.test_file)
        self.assertEqual(data, {}, "Should return an empty dict when JSON is invalid.")

    def test_compare_and_update_data(self):
        all_data = {
            'page_1_item1': {'value': 1},
            'page_1_item2': {'value': 2},
            'page_2_item3': {'value': 3}
        }
        new_page_data = {
            'page_1_item1': {'value': 1},   # No change
            'page_1_item2': {'value': 20},  # Updated
            'page_1_item4': {'value': 4}    # Added
        }
        updated, added, removed = compare_and_update_data(all_data, new_page_data, page_number=1)
        self.assertEqual(updated, ['page_1_item2'])
        self.assertEqual(added, ['page_1_item4'])
        self.assertEqual(removed, [], "No items should be removed")
        self.assertIn('page_1_item2', all_data)
        self.assertIn('page_1_item4', all_data)
        self.assertNotIn('page_1_item2', removed, "Updated items should not be in removed list.")

    def test_save_data_success(self):
        test_data = {'key1': 'value1', 'key2': 'value2'}
        save_data(self.test_file, test_data)
        with open(self.test_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(data, test_data, "Data saved should match the data provided.")

    def test_save_data_failure(self):
        # Attempt to save data to an invalid path
        invalid_path = '/invalid_path/test_data.json'
        with self.assertRaises(Exception):
            save_data(invalid_path, {'key': 'value'})

if __name__ == '__main__':
    unittest.main()
