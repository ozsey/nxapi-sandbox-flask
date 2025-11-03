from flask import render_template, request, flash, redirect, url_for, session
from . import app
import requests
from requests.exceptions import RequestException
import json

sandbox_host = 'sbx-nxos-mgmt.cisco.com'
sandbox_username = 'admin'
sandbox_password = 'Admin_1234!'
sandbox_url = f"https://{sandbox_host}/ins"
headers_json = {'Content-Type': 'application/json'}
headers_jsonrpc= {'Content-Type': 'application/json-rpc'}
verify = False

# Fungsi untuk melakukan permintaan NXAPI
def nxapi_request(payload):
    try:
        response = requests.post(sandbox_url, headers=headers_json, json=payload, auth=(sandbox_username, sandbox_password), verify=verify)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# Fungsi untuk melakukan permintaan NXAPI menggunakan JSON-RPC
def nxapi_request2(payload):
    try:
        payload = [{
            "jsonrpc": "2.0",
            "method": "cli",
            "params": {
                "cmd": payload["ins_api"]["input"],
                "version": 1
            },
            "id": 1
        }]
        response = requests.post(sandbox_url, data=json.dumps(payload), headers=headers_jsonrpc, auth=(sandbox_username, sandbox_password), verify=verify)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Request failed: {e}")
        return None

# Rute untuk halaman utama (index)
@app.route('/')
def index():
    return render_template('index.html')

# Rute untuk halaman akses login
@app.route('/access', methods=['GET', 'POST'])
def access():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == sandbox_username and password == sandbox_password:
            session['logged_in'] = True
            session['login_success'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please try again.', 'danger')

    return render_template('access.html')

# Rute untuk halaman dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('access'))
    
    login_success = session.pop('login_success', None)

    # Mendapatkan informasi perangkat
    payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": "show version",
            "output_format": "json"
        }
    }
    device_info = nxapi_request(payload)

    # Mendapatkan daftar interface menggunakan perintah show interface brief
    payload["ins_api"]["input"] = "show interface brief"
    interface_list = nxapi_request(payload)

    # Mendapatkan detail untuk interface tertentu
    interfaces = ["mgmt0", "loopback0", "loopback05", "loopback99"]
    non_vlan_interface_details = {}
    for iface in interfaces:
        payload["ins_api"]["input"] = f"show interface {iface} brief"
        result = nxapi_request(payload)
        if result:
            interface_data = result.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}).get('TABLE_interface', {}).get('ROW_interface', [])
            if interface_data:
                non_vlan_interface_details[iface] = {
                    "interface": iface,
                    "state": interface_data.get('state'),
                    "admin_state": interface_data.get('admin_state')
                }
    
    return render_template('dashboard.html',
                           device_info=device_info.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}),
                           interface_list=interface_list.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}).get('TABLE_interface', {}).get('ROW_interface', []),
                           non_vlan_interface_details=non_vlan_interface_details,
                           login_success=login_success)

# Rute untuk pencarian interface
@app.route('/search_interface', methods=['POST'])
def search_interface():
    if not session.get('logged_in'):
        return redirect(url_for('access'))

    interface = request.form['interface']
    payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": f"show interface {interface} brief",
            "output_format": "json"
        }
    }
    search_result = nxapi_request(payload)

    # Mendapatkan informasi perangkat
    device_payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": "show version",
            "output_format": "json"
        }
    }
    device_info = nxapi_request(device_payload)

    # Mendapatkan daftar interface menggunakan perintah show interface brief
    interface_payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": "show interface brief",
            "output_format": "json"
        }
    }
    interface_list = nxapi_request(interface_payload)

    # Mendapatkan detail untuk interface tertentu
    interfaces = ["mgmt0", "loopback0", "loopback05", "loopback99"]
    non_vlan_interface_details = {}
    for iface in interfaces:
        payload["ins_api"]["input"] = f"show interface {iface} brief"
        result = nxapi_request(payload)
        if result:
            interface_data = result.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}).get('TABLE_interface', {}).get('ROW_interface', [])
            if interface_data:
                non_vlan_interface_details[iface] = {
                    "interface": iface,
                    "state": interface_data.get('state'),
                    "admin_state": interface_data.get('admin_state')
                }  
                
    formatted_search_result = json.dumps(search_result.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}), indent=4)

    return render_template('dashboard.html',
                           device_info=device_info.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}),
                           interface_list=interface_list.get('ins_api', {}).get('outputs', {}).get('output', {}).get('body', {}).get('TABLE_interface', {}).get('ROW_interface', []),
                           non_vlan_interface_details=non_vlan_interface_details,
                           search_result=formatted_search_result,
                           search_interface_name=interface)

# Rute untuk halaman eksekusi perintah
@app.route('/commands', methods=['GET', 'POST'])
def commands():
    if not session.get('logged_in'):
        return redirect(url_for('access'))

    command_result = None
    if request.method == 'POST':
        command = request.form['command']
        payload = {
            "ins_api": {
                "version": "1.0",
                "type": "cli_show",
                "chunk": "0",
                "sid": "1",
                "input": command,
                "output_format": "json"
            }
        }
        command_result = nxapi_request(payload)

    return render_template('commands.html', command_result=command_result)

# Rute untuk logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))