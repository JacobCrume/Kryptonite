import base64
import requests
import json
import xmltodict
import os
import shutil
from urllib.parse import urlparse
from cdm import cdm, deviceconfig

class WvDecrypt(object):
    WV_SYSTEM_ID = [
     237, 239, 139, 169, 121, 214, 74, 206, 163, 200, 39, 220, 213, 29, 33, 237]

    def __init__(self, init_data_b64, cert_data_b64, device):
        self.init_data_b64 = init_data_b64
        self.cert_data_b64 = cert_data_b64
        self.device = device
        self.cdm = cdm.Cdm()

        def check_pssh(pssh_b64):
            pssh = base64.b64decode(pssh_b64)
            if not pssh[12:28] == bytes(self.WV_SYSTEM_ID):
                new_pssh = bytearray([0, 0, 0])
                new_pssh.append(32 + len(pssh))
                new_pssh[4:] = bytearray(b'pssh')
                new_pssh[8:] = [0, 0, 0, 0]
                new_pssh[13:] = self.WV_SYSTEM_ID
                new_pssh[29:] = [0, 0, 0, 0]
                new_pssh[31] = len(pssh)
                new_pssh[32:] = pssh
                return base64.b64encode(new_pssh)
            else:
                return pssh_b64

        self.session = self.cdm.open_session(check_pssh(self.init_data_b64), deviceconfig.DeviceConfig(self.device))
        if self.cert_data_b64:
            self.cdm.set_service_certificate(self.session, self.cert_data_b64)

    def log_message(self, msg):
        return '{}'.format(msg)

    def start_process(self):
        keyswvdecrypt = []
        try:
            for key in self.cdm.get_keys(self.session):
                if key.type == 'CONTENT':
                    keyswvdecrypt.append(self.log_message('{}:{}'.format(key.kid.hex(), key.key.hex())))

        except Exception:
            return (
             False, keyswvdecrypt)
        else:
            return (
             True, keyswvdecrypt)

    def get_challenge(self):
        return self.cdm.get_license_request(self.session)

    def update_license(self, license_b64):
        self.cdm.provide_license(self.session, license_b64)
        return True

def getPssh(mpd_url):
    pssh = ''
    r = requests.get(url=mpd_url)
    r.raise_for_status()
    xml = xmltodict.parse(r.text)
    mpd = json.loads(json.dumps(xml))
    periods = mpd['MPD']['Period']
    try:
        if isinstance(periods, list):
            for idx, period in enumerate(periods):
                if isinstance(period['AdaptationSet'], list):
                    for ad_set in period['AdaptationSet']:
                        if ad_set['@mimeType'] == 'video/mp4':
                            try:
                                for t in ad_set['ContentProtection']:
                                    if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                                        pssh = t["cenc:pssh"]
                            except Exception:
                                pass
                else:
                    if period['AdaptationSet']['@mimeType'] == 'video/mp4':
                            try:
                                for t in period['AdaptationSet']['ContentProtection']:
                                    if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                                        pssh = t["cenc:pssh"]
                            except Exception:
                                pass
        else:
            for ad_set in periods['AdaptationSet']:
                    if ad_set['@mimeType'] == 'video/mp4':
                        try:
                            for t in ad_set['ContentProtection']:
                                if t['@schemeIdUri'].lower() == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                                    pssh = t["cenc:pssh"]
                        except Exception:
                            pass
    except Exception:
        pass
    return pssh

def getDecryptionKeys(mpdUrl, licenceUrl, clientId=f"{os.getcwd()}/cdm/devices/android_generic/client_id.bin", privateKey=f"{os.getcwd()}/cdm/devices/android_generic/private_key.pem", cert_b64=None):
    # Get PSSH from MPD URL
    pssh = getPssh(mpdUrl)

    device_android_generic = {
        'name': 'android_generic',
        'description': 'android studio cdm',
        'security_level': 3,
        'session_id_type': 'android',
        'private_key_available': True,
        'vmp': False,
        'send_key_control_nonce': True,
        'device_client_id_blob_filename': clientId,
        'device_private_key_filename': privateKey
    }

    # Initialize WvDecrypt object
    wvdecrypt = WvDecrypt(init_data_b64=pssh, cert_data_b64=cert_b64, device=device_android_generic)
    raw_request = wvdecrypt.get_challenge()
    request = base64.b64encode(raw_request).decode('utf-8')
    signature = cdm.hash_object

    # Prepare headers and params
    params = urlparse(licenceUrl).query
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    responses = []

    # Make multiple POST requests to handle different site requirements
    responses.append(requests.post(url=licenceUrl, headers=headers, data=raw_request, params=params))
    responses.append(requests.post(url=licenceUrl, headers=headers, params=params, json={"rawLicenseRequestBase64": request}))
    responses.append(requests.post(url=licenceUrl, headers=headers, params=params, data=f'token=YOUR_TOKEN&provider=YOUR_PROVIDER&payload={request}'))
    headers['licenseRequest'] = request
    responses.append(requests.post(url=licenceUrl, headers=headers, params=params))
    del headers['licenseRequest']
    responses.append(requests.post(url=licenceUrl, headers=headers, params=params, json={"getWidevineLicense": {'releasePid': 'YOUR_RELEASE_PID', 'widevineChallenge': request}}))
    responses.append(requests.post(url=licenceUrl, headers=headers, params=params, json={"rawLicenseRequestBase64": request, "puid": 'YOUR_PUID', "watchSessionId": 'YOUR_SESSION_ID', "contentId": 'YOUR_CONTENT_ID', "contentTypeId": '21', "serviceName": 'ott-kp', "productId": '2', "monetizationModel": 'SVOD', "expirationTimestamp": 'YOUR_TIMESTAMP', "verificationRequired": 'false', "signature": str(signature), "version": 'V4'}))

    # Process responses to find a valid license
    for response in responses:
        try:
            response.content.decode('utf-8')
        except UnicodeDecodeError:
            widevine_license = response
            break
        else:
            if len(response.content.decode('utf-8')) > 500:
                widevine_license = response
                break
    else:
        print('Unable to obtain license. Is your CDM private or otherwise not blacklisted?')
        return None

    # Extract license
    license_b64 = ''
    lic_field_names = ['license', 'payload', 'getWidevineLicenseResponse']
    lic_field_names2 = ['license']
    try:
        if ':' in response.content.decode('utf-8'):
            for key in lic_field_names:
                try:
                    license_b64 = response.json()[key]
                except KeyError:
                    pass
                else:
                    for key2 in lic_field_names2:
                        try:
                            license_b64 = response.json()[key][key2]
                        except KeyError:
                            pass
        else:
            license_b64 = response.content
    except:
        license_b64 = base64.b64encode(response.content).decode('utf-8')

    # Update license and start decryption process
    wvdecrypt.update_license(license_b64)
    return wvdecrypt.start_process()[1][0]

def installCDM(clientId, privateKey):
    shutil.copyfile(clientId, f"{os.getcwd()}/cdm/devices/android_generic/client_id.bin")
    shutil.copyfile(privateKey, f"{os.getcwd()}/cdm/devices/android_generic/private_key.pem")