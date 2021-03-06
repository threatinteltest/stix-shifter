from stix_shifter.src.json_to_stix import json_to_stix_translator
from stix_shifter.src import transformers
from stix_shifter.src.modules.qradar import qradar_translator
import json

interface = qradar_translator.Translator()
map_file = open(interface.mapping_filepath).read()
map_data = json.loads(map_file)
data_source = {
    "type": "identity",
    "id": "identity--3532c56d-ea72-48be-a2ad-1a53f4c9c6d3",
    "name": "QRadar",
    "identity_class": "events"
}
options = {}


class TestTransform(object):
    @staticmethod
    def get_first(itr, constraint):
        return next(
            (obj for obj in itr if constraint(obj)),
            None
        )

    @staticmethod
    def get_first_of_type(itr, typ):
        return TestTransform.get_first(itr, lambda o: type(o) == dict and o.get('type') == typ)

    def test_common_prop(self):
        data = {"starttime": 1531169112, "eventcount": 5}

        result_bundle = json_to_stix_translator.convert_to_stix(
            data_source, map_data, [data], transformers.get_all_transformers(), options)

        assert(result_bundle['type'] == 'bundle')
        result_bundle_objects = result_bundle['objects']

        result_bundle_identity = result_bundle_objects[0]
        assert(result_bundle_identity['type'] == data_source['type'])
        assert(result_bundle_identity['id'] == data_source['id'])
        assert(result_bundle_identity['name'] == data_source['name'])
        assert(result_bundle_identity['identity_class']
               == data_source['identity_class'])

        observed_data = result_bundle_objects[1]

        assert(observed_data['id'] is not None)
        assert(observed_data['type'] == "observed-data")
        assert(observed_data['created_by_ref'] == result_bundle_identity['id'])

        assert(observed_data['number_observed'] == 5)
        assert(observed_data['created'] is not None)
        assert(observed_data['modified'] is not None)
        assert(observed_data['first_observed'] is not None)
        assert(observed_data['last_observed'] is not None)

    def test_cybox_observables(self):
        payload = "SomeBase64Payload"
        user_id = "someuserid2018"
        url = "https://example.com"
        domain = "example.com"
        source_ip = "127.0.0.1"
        destination_ip = "255.255.255.1"
        data = {"sourceip": source_ip, "destinationip": destination_ip, "url": url,
                "domain": domain, "payload": payload, "username": user_id, "protocol": 'TCP', "sourceport": 3000, "destinationport": 2000}

        result_bundle = json_to_stix_translator.convert_to_stix(
            data_source, map_data, [data], transformers.get_all_transformers(), options)

        assert(result_bundle['type'] == 'bundle')

        result_bundle_objects = result_bundle['objects']
        observed_data = result_bundle_objects[1]

        assert('objects' in observed_data)
        objects = observed_data['objects']

        nt_object = TestTransform.get_first_of_type(objects.values(), 'network-traffic')
        assert(nt_object is not None), 'network-traffic object type not found'
        assert(nt_object.keys() ==
            {'type', 'src_port', 'dst_port', 'src_ref', 'dst_ref', 'protocols'})
        assert(nt_object['src_port'] == 3000)
        assert(nt_object['dst_port'] == 2000)
        assert(nt_object['protocols'] == ['tcp'])

        ip_ref = nt_object['dst_ref']
        assert(ip_ref in objects), f"dst_ref with key {nt_object['dst_ref']} not found"
        ip_obj = objects[ip_ref]
        assert(ip_obj.keys() == {'type', 'value'})
        assert(ip_obj['type'] == 'ipv4-addr')
        assert(ip_obj['value'] == destination_ip)

        ip_ref = nt_object['src_ref']
        assert(ip_ref in objects), f"src_ref with key {nt_object['src_ref']} not found"
        ip_obj = objects[ip_ref]
        assert(ip_obj.keys() == {'type', 'value'})
        assert(ip_obj['type'] == 'ipv4-addr')
        assert(ip_obj['value'] == source_ip)

        curr_obj = TestTransform.get_first_of_type(objects.values(), 'url')
        assert(curr_obj is not None), 'url object type not found'
        assert(curr_obj.keys() == {'type', 'value'})
        assert(curr_obj['value'] == url)

        curr_obj = TestTransform.get_first_of_type(objects.values(), 'domain-name')
        assert(curr_obj is not None), 'domain-name object type not found'
        assert(curr_obj.keys() == {'type', 'value'})
        assert(curr_obj['value'] == domain)

        curr_obj = TestTransform.get_first_of_type(objects.values(), 'artifact')
        assert(curr_obj is not None), 'artifact object type not found'
        assert(curr_obj.keys() == {'type', 'payload_bin'})
        assert(curr_obj['payload_bin'] == payload)

        curr_obj = TestTransform.get_first_of_type(objects.values(), 'user-account')
        assert(curr_obj is not None), 'user-account object type not found'
        assert(curr_obj.keys() == {'type', 'user_id'})
        assert(curr_obj['user_id'] == user_id)

        assert(objects.keys() == set(map(str, range(0, 7))))

    def test_custom_props(self):
        data = {"logsourceid": 126, "qid": 55500004,
                "identityip": "0.0.0.0", "magnitude": 4, "logsourcename": "someLogSourceName"}

        result_bundle = json_to_stix_translator.convert_to_stix(
            data_source, map_data, [data], transformers.get_all_transformers(), options)
        observed_data = result_bundle['objects'][1]

        assert('x_com_ibm_ariel' in observed_data)
        custom_props = observed_data['x_com_ibm_ariel']
        assert(custom_props['identity_ip'] == data['identityip'])
        assert(custom_props['log_source_id'] == data['logsourceid'])
        assert(custom_props['qid'] == data['qid'])
        assert(custom_props['magnitude'] == data['magnitude'])
        assert(custom_props['log_source_name'] == data['logsourcename'])
