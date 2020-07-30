import json
import pytest

XDR_URL = 'https://api.xdrurl.com'


def load_test_data(json_path):
    with open(json_path) as f:
        return json.load(f)


def test_get_incident_list(requests_mock):
    from PaloAltoNetworks_XDR import get_incidents_command, Client

    get_incidents_list_response = load_test_data('./test_data/get_incidents_list.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incidents/', json=get_incidents_list_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'incident_id_list': '1 day'
    }
    _, outputs, _ = get_incidents_command(client, args)

    expected_output = {
        'PaloAltoNetworksXDR.Incident(val.incident_id==obj.incident_id)':
            get_incidents_list_response.get('reply').get('incidents')
    }
    assert expected_output == outputs


def test_fetch_incidents(requests_mock):
    from PaloAltoNetworks_XDR import fetch_incidents, Client

    get_incidents_list_response = load_test_data('./test_data/get_incidents_list.json')
    raw_incident = load_test_data('./test_data/get_incident_extra_data.json')
    modified_raw_incident = raw_incident['reply']['incident']
    modified_raw_incident['alerts'] = raw_incident['reply'].get('alerts').get('data')
    modified_raw_incident['network_artifacts'] = raw_incident['reply'].get('network_artifacts').get('data')
    modified_raw_incident['file_artifacts'] = raw_incident['reply'].get('file_artifacts').get('data')

    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incidents/', json=get_incidents_list_response)
    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incident_extra_data/', json=raw_incident)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    next_run, incidents = fetch_incidents(client, '3 month', {})

    assert len(incidents) == 2
    assert incidents[0]['name'] == "#1 - 'Local Analysis Malware' generated by XDR Agent detected on host AAAAA " \
                                   "involving user Administrator"

    assert incidents[0]['rawJSON'] == json.dumps(modified_raw_incident)


def test_get_incident_extra_data(requests_mock):
    from PaloAltoNetworks_XDR import get_incident_extra_data_command, Client

    get_incident_extra_data_response = load_test_data('./test_data/get_incident_extra_data.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incident_extra_data/',
                       json=get_incident_extra_data_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'incident_id': '1'
    }
    _, outputs, _ = get_incident_extra_data_command(client, args)

    expected_incident = get_incident_extra_data_response.get('reply').get('incident')

    expected_incident.update({
        'alerts': get_incident_extra_data_response.get('reply').get('alerts').get('data'),
        'network_artifacts': get_incident_extra_data_response.get('reply').get('network_artifacts').get('data', []),
        'file_artifacts': get_incident_extra_data_response.get('reply').get('file_artifacts').get('data')
    })

    expected_output = {
        'PaloAltoNetworksXDR.Incident(val.incident_id==obj.incident_id)': expected_incident
    }
    assert expected_output == outputs


def test_update_incident(requests_mock):
    from PaloAltoNetworks_XDR import update_incident_command, Client

    update_incident_response = load_test_data('./test_data/update_incident.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/update_incident/', json=update_incident_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'incident_id': '1',
        'status': 'new'
    }
    readable_output, outputs, _ = update_incident_command(client, args)

    assert outputs is None
    assert readable_output == 'Incident 1 has been updated'


def test_get_endpoints(requests_mock):
    from PaloAltoNetworks_XDR import get_endpoints_command, Client

    get_endpoints_response = load_test_data('./test_data/get_endpoints.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/get_endpoint/', json=get_endpoints_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'hostname': 'foo',
        'page': 1,
        'limit': 3
    }

    _, outputs, _ = get_endpoints_command(client, args)
    assert get_endpoints_response.get('reply').get('endpoints') == \
           outputs['PaloAltoNetworksXDR.Endpoint(val.endpoint_id == obj.endpoint_id)']


def test_get_all_endpoints_using_limit(requests_mock):
    from PaloAltoNetworks_XDR import get_endpoints_command, Client

    get_endpoints_response = load_test_data('./test_data/get_all_endpoints.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/get_endpoints/', json=get_endpoints_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'limit': 1,
        'page': 0,
        'sort_order': 'asc'
    }

    _, outputs, _ = get_endpoints_command(client, args)
    expected_endpoint = get_endpoints_response.get('reply')[0]

    assert [expected_endpoint] == outputs['PaloAltoNetworksXDR.Endpoint(val.endpoint_id == obj.endpoint_id)']


def test_insert_parsed_alert(requests_mock):
    from PaloAltoNetworks_XDR import insert_parsed_alert_command, Client

    insert_alerts_response = load_test_data('./test_data/create_alerts.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/alerts/insert_parsed_alerts/', json=insert_alerts_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        "product": "VPN & Firewall-1",
        "vendor": "Check Point",
        "local_ip": "192.168.1.254",
        "local_port": "35398",
        "remote_ip": "0.0.0.0",
        "remote_port": "0",
        "event_timestamp": "1543270652000",
        "severity": "Low",
        "alert_name": "Alert Name Example",
        "alert_description": "Alert Description"
    }

    readable_output, outputs, _ = insert_parsed_alert_command(client, args)
    assert outputs is None
    assert readable_output == 'Alert inserted successfully'


def test_isolate_endpoint(requests_mock):
    from PaloAltoNetworks_XDR import isolate_endpoint_command, Client

    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/get_endpoint/', json={
        'reply': {
            'endpoints': [
                {
                    'endpoint_id': '1111',
                    "endpoint_status": "CONNECTED"
                }
            ]
        }
    })

    isolate_endpoint_response = load_test_data('./test_data/isolate_endpoint.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/isolate', json=isolate_endpoint_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        "endpoint_id": "1111"
    }

    readable_output, _, _ = isolate_endpoint_command(client, args)
    assert readable_output == 'The isolation request has been submitted successfully on Endpoint 1111.\n' \
                              'To check the endpoint isolation status please run:' \
                              ' !xdr-get-endpoints endpoint_id_list=1111 and look at the [is_isolated] field.'


def test_isolate_endpoint_unconnected_machine(requests_mock, mocker):
    from PaloAltoNetworks_XDR import isolate_endpoint_command, Client
    #    return_error_mock = mocker.patch(RETURN_ERROR_TARGET)

    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/get_endpoint/', json={
        'reply': {
            'endpoints': [
                {
                    'endpoint_id': '1111',
                    "endpoint_status": "DISCONNECTED"
                }
            ]
        }
    })

    isolate_endpoint_response = load_test_data('./test_data/isolate_endpoint.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/isolate', json=isolate_endpoint_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        "endpoint_id": "1111"
    }
    with pytest.raises(ValueError, match='Error: Endpoint 1111 is disconnected and therefore can not be isolated.'):
        isolate_endpoint_command(client, args)


def test_unisolate_endpoint(requests_mock):
    from PaloAltoNetworks_XDR import unisolate_endpoint_command, Client

    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/get_endpoint/', json={
        'reply': {
            'endpoints': [
                {
                    'endpoint_id': '1111',
                    "endpoint_status": "CONNECTED"
                }
            ]
        }
    })

    unisolate_endpoint_response = load_test_data('./test_data/unisolate_endpoint.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/unisolate', json=unisolate_endpoint_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        "endpoint_id": "1111"
    }

    readable_output, _, _ = unisolate_endpoint_command(client, args)
    assert readable_output == 'The un-isolation request has been submitted successfully on Endpoint 1111.\n' \
                              'To check the endpoint isolation status please run:' \
                              ' !xdr-get-endpoints endpoint_id_list=1111 and look at the [is_isolated] field.'


def test_unisolate_endpoint_pending_isolation(requests_mock):
    from PaloAltoNetworks_XDR import unisolate_endpoint_command, Client

    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/get_endpoint/', json={
        'reply': {
            'endpoints': [
                {
                    'endpoint_id': '1111',
                    "is_isolated": "AGENT_PENDING_ISOLATION"
                }
            ]
        }
    })

    unisolate_endpoint_response = load_test_data('./test_data/unisolate_endpoint.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/unisolate', json=unisolate_endpoint_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        "endpoint_id": "1111"
    }
    with pytest.raises(ValueError, match='Error: Endpoint 1111 is pending isolation and therefore can not be'
                                         ' un-isolated.'):
        unisolate_endpoint_command(client, args)


def test_get_distribution_url(requests_mock):
    from PaloAltoNetworks_XDR import get_distribution_url_command, Client

    get_distribution_url_response = load_test_data('./test_data/get_distribution_url.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/distributions/get_dist_url/', json=get_distribution_url_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        'distribution_id': '1111',
        'package_type': 'x86'
    }

    readable_output, outputs, _ = get_distribution_url_command(client, args)
    expected_url = get_distribution_url_response.get('reply').get('distribution_url')
    assert outputs == {
        'PaloAltoNetworksXDR.Distribution(val.id == obj.id)': {
            'id': '1111',
            'url': expected_url
        }
    }

    assert readable_output == f'[Distribution URL]({expected_url})'


def test_get_audit_management_logs(requests_mock):
    from PaloAltoNetworks_XDR import get_audit_management_logs_command, Client

    get_audit_management_logs_response = load_test_data('./test_data/get_audit_management_logs.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/audits/management_logs/', json=get_audit_management_logs_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        'email': 'woo@demisto.com',
        'limit': '3',
        'timestamp_gte': '3 month'
    }

    readable_output, outputs, _ = get_audit_management_logs_command(client, args)

    expected_outputs = get_audit_management_logs_response.get('reply').get('data')
    assert outputs['PaloAltoNetworksXDR.AuditManagementLogs(val.AUDIT_ID == obj.AUDIT_ID)'] == expected_outputs


def test_get_audit_agent_reports(requests_mock):
    from PaloAltoNetworks_XDR import get_audit_agent_reports_command, Client

    get_audit_agent_reports_response = load_test_data('./test_data/get_audit_agent_report.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/audits/agents_reports/', json=get_audit_agent_reports_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        'endpoint_names': 'woo.demisto',
        'limit': '3',
        'timestamp_gte': '3 month'
    }

    readable_output, outputs, _ = get_audit_agent_reports_command(client, args)
    expected_outputs = get_audit_agent_reports_response.get('reply').get('data')
    assert outputs['PaloAltoNetworksXDR.AuditAgentReports'] == expected_outputs


def test_insert_cef_alerts(requests_mock):
    from PaloAltoNetworks_XDR import insert_cef_alerts_command, Client

    insert_cef_alerts_response = load_test_data('./test_data/insert_cef_alerts.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/alerts/insert_cef_alerts/', json=insert_cef_alerts_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        'cef_alerts': [
            'CEF:0|Check Point|VPN-1 & FireWall-1|Check Point|Log|microsoft-ds|Unknown|act=AcceptdeviceDirection=0 '
            'rt=1569477512000 spt=56957 dpt=445 cs2Label=Rule Name cs2=ADPrimery '
            'layer_name=FW_Device_blackened Securitylayer_uuid=07693fc7-1a5c-4f31-8afe-77ae96c71b8c match_id=1806 '
            'parent_rule=0rule_action=Accept rule_uid=8e45f36b-d106-4d81-a1f0-9d1ed9a6be5c ifname=bond2logid=0 '
            'loguid={0x5d8c5388,0x61,0x29321fac,0xc0000022} origin=1.1.1.1originsicname=CN=DWdeviceBlackend,'
            'O=Blackend sequencenum=363 version=5dst=1.1.1.1 inzone=External outzone=Internal product=VPN-1 & '
            'FireWall-1 proto=6service_id=microsoft-ds src=1.1.1.1',

            'CEF:0|Check Point|VPN-1 & FireWall-1|Check Point|Log|Log|Unknown|act=AcceptdeviceDirection=0 '
            'rt=1569477501000 spt=63088 dpt=5985 cs2Label=Rule Namelayer_name=FW_Device_blackened Securitylayer_'
            'uuid=07693fc7-1a5c-4f31-8afe-77ae96c71b8c match_id=8899 parent_rule=0rule_action=Accept rule_'
            'uid=ae987933-82c0-470f-ab1c-1ad552c82369conn_direction=Internal ifname=bond1.12 '
            'logid=0loguid={0x5d8c537d,0xbb,0x29321fac,0xc0000014} origin=1.1.1.1originsicname=CN=DWdeviceBlackend,'
            'O=Blackend sequencenum=899 version=5dst=1.1.1.1 product=VPN-1 & FireWall-1 proto=6 src=1.1.1.1'
        ]
    }

    readable_output, _, _ = insert_cef_alerts_command(client, args)

    assert readable_output == 'Alerts inserted successfully'


def test_get_distribution_status(requests_mock):
    from PaloAltoNetworks_XDR import get_distribution_status_command, Client

    get_distribution_status_response = load_test_data('./test_data/get_distribution_status.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/distributions/get_status/', json=get_distribution_status_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        "distribution_ids": "588a56de313549b49d70d14d4c1fd0e3"
    }

    readable_output, outputs, _ = get_distribution_status_command(client, args)

    assert outputs == {
        'PaloAltoNetworksXDR.Distribution(val.id == obj.id)': [
            {
                'id': '588a56de313549b49d70d14d4c1fd0e3',
                'status': 'Completed'
            }
        ]
    }


def test_get_distribution_versions(requests_mock):
    from PaloAltoNetworks_XDR import get_distribution_versions_command, Client

    get_distribution_versions_response = load_test_data('./test_data/get_distribution_versions.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/distributions/get_versions/', json=get_distribution_versions_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    readable_output, outputs, _ = get_distribution_versions_command(client)

    assert outputs == {
        'PaloAltoNetworksXDR.DistributionVersions': {
            "windows": [
                "7.0.0.27797"
            ],
            "linux": [
                "7.0.0.1915"
            ],
            "macos": [
                "7.0.0.1914"
            ]
        }
    }


def test_create_distribution(requests_mock):
    from PaloAltoNetworks_XDR import create_distribution_command, Client

    create_distribution_response = load_test_data('./test_data/create_distribution.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/distributions/create/', json=create_distribution_response)

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )

    args = {
        "name": "dfslcxe",
        "platform": "windows",
        "package_type": "standalone",
        "agent_version": "7.0.0.28644"
    }

    readable_output, outputs, _ = create_distribution_command(client, args)

    expected_distribution_id = create_distribution_response.get('reply').get('distribution_id')
    assert outputs == {
        'PaloAltoNetworksXDR.Distribution(val.id == obj.id)': {
            'id': expected_distribution_id,
            "name": "dfslcxe",
            "platform": "windows",
            "package_type": "standalone",
            "agent_version": "7.0.0.28644",
            'description': None
        }
    }
    assert readable_output == f'Distribution {expected_distribution_id} created successfully'


def test_blacklist_files_command_with_more_than_one_file(requests_mock):
    """
    Given:
        - List of files' hashes to put in blacklist
    When
        - A user desires to mark more than one file
    Then
        - returns markdown, context data and raw response.
    """

    from PaloAltoNetworks_XDR import blacklist_files_command, Client
    test_data = load_test_data('test_data/blacklist_whitelist_files_success.json')
    expected_command_result = {'PaloAltoNetworksXDR.blackList.fileHash(val.fileHash == obj.fileHash)': test_data[
        'multi_command_args']['hash_list']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/hash_exceptions/blacklist/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = blacklist_files_command(client, test_data['multi_command_args'])

    assert expected_command_result == context


def test_blacklist_files_command_with_single_file(requests_mock):
    """
    Given:
        - List of a file hashes to put in blacklist.
    When
        - A user desires to blacklist one file.
    Then
        - returns markdown, context data and raw response.
    """

    from PaloAltoNetworks_XDR import blacklist_files_command, Client
    test_data = load_test_data('test_data/blacklist_whitelist_files_success.json')
    expected_command_result = {
        'PaloAltoNetworksXDR.blackList.fileHash(val.fileHash == obj.fileHash)':
            test_data['single_command_args']['hash_list']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/hash_exceptions/blacklist/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = blacklist_files_command(client, test_data['single_command_args'])

    assert expected_command_result == context


def test_blacklist_files_command_with_no_comment_file(requests_mock):
    """
    Given:
        - ￿List of files' hashes to put in blacklist without passing the comment argument.
    When
        - A user desires to blacklist files without adding a comment.
    Then
        - returns markdown, context data and raw response.
    """

    from PaloAltoNetworks_XDR import blacklist_files_command, Client
    test_data = load_test_data('test_data/blacklist_whitelist_files_success.json')
    expected_command_result = {
        'PaloAltoNetworksXDR.blackList.fileHash(val.fileHash == obj.fileHash)':
            test_data['no_comment_command_args']['hash_list']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/hash_exceptions/blacklist/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = blacklist_files_command(client, test_data['no_comment_command_args'])

    assert expected_command_result == context


def test_whitelist_files_command_with_more_than_one_file(requests_mock):
    """
    Given:
        - ￿List of files' hashes to put in whitelist
    When
        - A user desires to mark more than one file
    Then
        - returns markdown, context data and raw response.
    """

    from PaloAltoNetworks_XDR import whitelist_files_command, Client
    test_data = load_test_data('test_data/blacklist_whitelist_files_success.json')
    expected_command_result = {'PaloAltoNetworksXDR.whiteList.fileHash(val.fileHash == obj.fileHash)': test_data[
        'multi_command_args']['hash_list']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/hash_exceptions/whitelist/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = whitelist_files_command(client, test_data['multi_command_args'])

    assert expected_command_result == context


def test_whitelist_files_command_with_single_file(requests_mock):
    """
    Given:
        - List of a file hashes to put in whitelist.
    When
        - A user desires to whitelist one file.
    Then
        - returns markdown, context data and raw response.
    """

    from PaloAltoNetworks_XDR import whitelist_files_command, Client
    test_data = load_test_data('test_data/blacklist_whitelist_files_success.json')
    expected_command_result = {
        'PaloAltoNetworksXDR.whiteList.fileHash(val.fileHash == obj.fileHash)':
            test_data['single_command_args']['hash_list']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/hash_exceptions/whitelist/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = whitelist_files_command(client, test_data['single_command_args'])

    assert expected_command_result == context


def test_whitelist_files_command_with_no_comment_file(requests_mock):
    """
    Given:
        - List of files' hashes to put in whitelist without passing the comment argument.
    When
        - A user desires to whitelist files without adding a comment.
    Then
        - returns markdown, context data and raw response.
    """

    from PaloAltoNetworks_XDR import whitelist_files_command, Client
    test_data = load_test_data('test_data/blacklist_whitelist_files_success.json')
    expected_command_result = {
        'PaloAltoNetworksXDR.whiteList.fileHash(val.fileHash == obj.fileHash)': test_data['no_comment_command_args'][
            'hash_list']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/hash_exceptions/whitelist/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = whitelist_files_command(client, test_data['no_comment_command_args'])

    assert expected_command_result == context


def test_quarantine_files_command(requests_mock):
    """
    Given:
        - List of files' hashes to put in quarantine
    When
        - A user desires to quarantine files.
    Then
        - returns markdown, context data and raw response.
    """
    from PaloAltoNetworks_XDR import quarantine_files_command, Client
    test_data = load_test_data('test_data/quarantine_files.json')
    quarantine_files_expected_tesult = {
        'PaloAltoNetworksXDR.quarantineFiles.actionIds(val.actionId === obj.actionId)': test_data['context_data']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/quarantine/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = quarantine_files_command(client, test_data['command_args'])

    assert quarantine_files_expected_tesult == context


def test_get_quarantine_status_command(requests_mock):
    """
    Given:
        - Endpoint_id, file_path, file_hash
    When
        - A user desires to check a file's quarantine status.
    Then
        - returns markdown, context data and raw response.
    """
    from PaloAltoNetworks_XDR import get_quarantine_status_command, Client
    test_data = load_test_data('test_data/get_quarantine_status.json')
    quarantine_files_expected_tesult = {
        'PaloAltoNetworksXDR.quarantineFiles.status(val.fileHash === obj.fileHash &&val.endpointId'
        ' === obj.endpointId && val.filePath === obj.filePath)':
            test_data['context_data']}
    requests_mock.post(f'{XDR_URL}/public_api/v1/quarantine/status/', json=test_data['api_response'])

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = get_quarantine_status_command(client, test_data['command_args'])

    assert quarantine_files_expected_tesult == context


def test_restore_file_command(requests_mock):
    """
    Given:
        - file_hash
    When
        - A user desires to restore a file.
    Then
        - returns markdown, context data and raw response.
    """
    from PaloAltoNetworks_XDR import restore_file_command, Client

    restore_expected_tesult = {'PaloAltoNetworksXDR.restoredFiles.actionId(val.actionId == obj.actionId)': 123}
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/restore/', json={"reply": {"action_id": 123}})

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = restore_file_command(client, {"file_hash": "123"})

    assert restore_expected_tesult == context


def test_endpoint_scan_command(requests_mock):
    """
    Given:
    -   endpoint_id_list, dist_name, gte_first_seen, gte_last_seen, lte_first_seen, lte_last_seen, ip_list,
    group_name, platform, alias, isolate, hostname
    When
        - A user desires to scan endpoint.
    Then
        - returns markdown, context data and raw response.
    """
    from PaloAltoNetworks_XDR import endpoint_scan_command, Client
    test_data = load_test_data('test_data/scan_endpoints.json')
    scan_expected_tesult = {'PaloAltoNetworksXDR.endpointScan.actionId(val.actionId == obj.actionId)': 123}
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/scan/', json={"reply": {"action_id": 123}})

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = endpoint_scan_command(client, test_data['command_args'])

    assert scan_expected_tesult == context


def test_endpoint_scan_command_scan_all_endpoints(requests_mock):
    """
    Given:
    -  no filters.
    When
        - A user desires to scan all endpoints.
    Then
        - returns markdown, context data and raw response.
    """
    from PaloAltoNetworks_XDR import endpoint_scan_command, Client
    scan_expected_tesult = {'PaloAltoNetworksXDR.endpointScan.actionId(val.actionId == obj.actionId)': 123}
    requests_mock.post(f'{XDR_URL}/public_api/v1/endpoints/scan/', json={"reply": {"action_id": 123}})

    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    client._headers = {}
    markdown, context, raw = endpoint_scan_command(client, {})

    assert scan_expected_tesult == context


def test_sort_all_lists_incident_fields():
    from PaloAltoNetworks_XDR import sort_all_lists_incident_fields
    raw_incident = load_test_data('test_data/raw_fetched_incident.json')
    sort_all_lists_incident_fields(raw_incident)
    assert raw_incident.get('alerts')[0].get('alert_id') == "42"
    assert raw_incident.get('alerts')[1].get('alert_id') == "55"
    assert raw_incident.get('alerts')[2].get('alert_id') == "60"


def test_get_mapping_fields_command():
    from PaloAltoNetworks_XDR import get_mapping_fields_command
    expected_mapping = [{"Cortex XDR Incident": {
        "status": "Current status of the incident: \"new\",\"under_investigation\",\"resolved_threat_handled\","
                  "\"resolved_known_issue\",\"resolved_duplicate\",\"resolved_false_positive\",\"resolved_other\"",
        "assigned_user_mail": "Email address of the assigned user.",
        "assigned_user_pretty_name": "Full name of the user assigned to the incident.",
        "resolve_comment": "Comments entered by the user when the incident was resolved.",
        "manual_severity": "Incident severity assigned by the user. This does not "
                           "affect the calculated severity low medium high"
    }}]
    res = get_mapping_fields_command()
    assert expected_mapping == res.extract_mapping()


def test_get_remote_data_command_should_update(requests_mock):
    from PaloAltoNetworks_XDR import get_remote_data_command, Client
    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'id': 1,
        'lastUpdate': 0
    }
    raw_incident = load_test_data('./test_data/get_incident_extra_data.json')
    modified_raw_incident = raw_incident['reply']['incident']
    modified_raw_incident['alerts'] = raw_incident['reply'].get('alerts').get('data')
    modified_raw_incident['network_artifacts'] = raw_incident['reply'].get('network_artifacts').get('data')
    modified_raw_incident['file_artifacts'] = raw_incident['reply'].get('file_artifacts').get('data')
    modified_raw_incident['id'] = modified_raw_incident.get('incident_id')
    modified_raw_incident['assigned_user_mail'] = ''
    modified_raw_incident['assigned_user_pretty_name'] = ''

    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incident_extra_data/', json=raw_incident)

    response = get_remote_data_command(client, args)
    assert response.mirrored_object == modified_raw_incident
    assert response.entries == []


def test_get_remote_data_command_should_not_update(requests_mock):
    from PaloAltoNetworks_XDR import get_remote_data_command, Client
    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'id': 1,
        'lastUpdate': '2020-07-31T00:00:00Z'
    }
    raw_incident = load_test_data('./test_data/get_incident_extra_data.json')
    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incident_extra_data/', json=raw_incident)

    response = get_remote_data_command(client, args)
    assert response == {}


def test_get_remote_data_command_should_close_issue(requests_mock):
    from PaloAltoNetworks_XDR import get_remote_data_command, Client
    client = Client(
        base_url=f'{XDR_URL}/public_api/v1'
    )
    args = {
        'id': 1,
        'lastUpdate': 0
    }
    raw_incident = load_test_data('./test_data/get_incident_extra_data.json')
    raw_incident['reply']['incident']['status'] = 'resolved_threat_handled'
    raw_incident['reply']['incident']['resolve_comment'] = 'Handled'
    modified_raw_incident = raw_incident['reply']['incident']
    modified_raw_incident['alerts'] = raw_incident['reply'].get('alerts').get('data')
    modified_raw_incident['network_artifacts'] = raw_incident['reply'].get('network_artifacts').get('data')
    modified_raw_incident['file_artifacts'] = raw_incident['reply'].get('file_artifacts').get('data')
    modified_raw_incident['id'] = modified_raw_incident.get('incident_id')
    modified_raw_incident['assigned_user_mail'] = ''
    modified_raw_incident['assigned_user_pretty_name'] = ''
    modified_raw_incident['closeReason'] = 'Resolved'
    modified_raw_incident['closeNotes'] = 'Handled'

    expected_closing_entry = {
        'Type': 1,
        'Contents': {
            'dbotIncidentClose': True,
            'closeReason': 'Resolved',
            'closeNotes': 'Handled'
        },
        'ContentsFormat': 'json'
    }

    requests_mock.post(f'{XDR_URL}/public_api/v1/incidents/get_incident_extra_data/', json=raw_incident)

    response = get_remote_data_command(client, args)
    assert response.mirrored_object == modified_raw_incident
    assert expected_closing_entry in response.entries
