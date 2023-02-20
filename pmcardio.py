import os
import sys
import json
import time
import requestx
import traceback
from datetime import datetime

class PMCardio:
    def __init__(self, token, refresh_token):
        self.REFRESH_TOKEN = refresh_token
        self.TOKEN = token

        print("PMCardio Initialized")
        self.HOST = "https://2-4-4-edu.pmcardio.powerfulmedical.com"
        self.HOST_TOKEN = "https://d1we2i5lxero40.cloudfront.net"

        self.HEADERS = {
            "User-Agent" : "okhttp/3.12.12",
            "Authorization" : "Bearer " + self.TOKEN,
            "Connection" : "close",
            "client-version": "2.4.4",
            "client-build-number" : "160"
            }

        self.HEADERS_TOKEN = {
            "User-Agent" : "aws-sdk-js/3.22.0 os/other lang/js md/rn api/cognito_identity_provider/3.22.0",
            "Connection" : "close",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "X-Amz-User-Agent" : "aws-sdk-js/3.22.0",
            "Amz-Sdk-Invocation-Id" : "1a14322f-9ffe-427f-81f1-f1223515d6b0",
            "Amz-Sdk-Request" : "attempt=1; max=3",
            "Content-Type" : "application/x-amz-json-1.1"
            }

        self.Requests = requestx.RequestsX(header=self.HEADERS)

    def TokenSanity(func):
        def wrapper(self, *args, **kwargs):
            self.USER_CHECK = self.HOST + "/users/me"
            req = self.Requests.get(self.USER_CHECK)
            print("GUA LOGIN?")
            print(req.text)
            if "Unauthorized" in req.text:
                print("Token Expired, Renew Token...")
                self.ReqLogin = self.Login()
                self.TOKEN = self.ReqLogin["AuthenticationResult"]["AccessToken"]

                #Re-Init RequestsX
                self.HEADERS = {
                    "User-Agent" : "okhttp/3.12.12",
                    "Authorization" : "Bearer " + self.TOKEN,
                    "Connection" : "close",
                    "client-version": "2.4.4",
                    "client-build-number" : "160"
                }

                self.Requests = requestx.RequestsX(header=self.HEADERS)

            return func(self, *args, **kwargs)

        return wrapper

    def Login(self):
        self.data = json.dumps({
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "AuthParameters": {"REFRESH_TOKEN": self.REFRESH_TOKEN},
            "ClientId": "none"
            })

        self.req = self.Requests.post(self.HOST_TOKEN, headers=self.HEADERS_TOKEN, data=self.data)
        tokenize = self.req.json()
        tokenize["REFRESH_TOKEN"] = self.REFRESH_TOKEN

        print("Saving New Token in Token.txt")
        with open("token.txt", 'w') as ff:
            json.dump(tokenize, ff, indent = 6)

        return tokenize

    def Logout(self):
        print("This Is Not Implemented")
        return None

    @TokenSanity
    def GenerateReport(self, isrythm=0, page=1, rows=6, columns=2, voltage=10, speed=25):
        self.REPORT_URL = self.HOST + "/reports"

        data = {
            "number_of_rhythm_leads" : isrythm,
            "number_of_photos": page,
            "rows": rows,
            "columns": columns,
            "voltage_gain": voltage,
            "paper_speed": speed
            }

        self.req = self.Requests.post(self.REPORT_URL, json=data)
        #RESULT

        """
        {
            "report_id": "9f82f857-dc9a-442d-a307-fc768b009609",
            "report_name": "Report OHZXMB"
        }
        """

        return self.req.json()

    @TokenSanity
    def AnalyzeECG(self, img, isrythm, page, rows, columns, voltage, speed, umur, kelamin):
        try:
            REPORT_ = self.GenerateReport(isrythm, page, rows, columns, voltage, speed)
            print(REPORT_)
            REPORT_ID = REPORT_["report_id"]
            REPORT_NAME = REPORT_['report_name']
            self.ANALYZE_URL = self.HOST + "/reports/" + REPORT_ID + "/photo/0"
            self.PUT_ANALYZE_URL = self.HOST + "/reports/" + REPORT_ID
            self.data = {'photo_rotation': '0'}
            self.files = [
                ('ecg_photo',('ECG_Image.jpg', img, 'image/jpeg'))
            ]
            self.req = self.Requests.post(self.ANALYZE_URL, data=self.data, files=self.files)
            print(self.req.text)

            time.sleep(10)

            self.dataPasien = {
                    "patient_number": None,
                    "age": int(umur),
                    "gender": str(kelamin),
                    "ecg_intention": [
                        "routine_checkup"
                    ],
                    "report_name": REPORT_NAME
                }
            self.req2 = self.Requests.put(self.PUT_ANALYZE_URL, json=self.dataPasien).json()

            print(self.req2)

            self.report_url = str(self.req2['report_url'])

            diagnosis = str(self.req2.get('main_diagnosis', "Possible Normal (No Disorder)"))

            ddx = ""
            if self.req2["diagnoses"] is not None:
                ddx += str(self.req2['diagnoses']['related']) + "||--<br>  "

                for i in self.req2['diagnoses']['other']:
                    ddx += str(i['name']) + "<br> "
            else:
                ddx += str(self.req2['triage_class']['description']) + "<br>"
            ritme = self.req2['rhythm']

            if ritme is None:
                ritme = "Tidak Terdeteksi"
            else:
                ritme =  ritme['name']

            heart_rate = self.req2['view']['data']
            #
            if heart_rate is None:
                heart_rate = "Tidak Terdeteksi"
            else:
                heart_rate =  heart_rate['heart_rate']

            ket = ""

            self.req3 = self.Requests.get(self.report_url).json()
            if self.req3.get('parameters', None) is not None:
                p_wave = float(self.req3['parameters']['summary']['p_wave']['mean']) / 1000
                qrs_comp = float(self.req3['parameters']['summary']['qrs_complex']['mean']) / 1000
                st_interval = float(self.req3['parameters']['summary']['st_interval']['mean']) /1000
                pr_interval = float(self.req3['parameters']['summary']['pr_interval']['mean']) / 1000
                qt_interval = float(self.req3['parameters']['summary']['qt_interval']['mean']) / 1000
                rr_interval = float(self.req3['parameters']['summary']['rr_interval']['mean']) / 1000
                pp_interval = float(self.req3['parameters']['summary']['pp_interval']['mean']) / 1000
                axis = self.req3['parameters']['axis']

                if p_wave > 0.12:
                    ket += f"gelombang p mengalami pelebaran dengan waktu {p_wave} second yang diatas batas normal,"
                else:
                    ket += f"gelombang p dengan waktu {p_wave} second dalam batas normal,"
            else:
                p_wave = "Tidak Ada"
                qrs_comp = "Tidak Ada"
                st_interval = "Tidak Ada"
                pr_interval = "Tidak Ada"
                qt_interval = "Tidak Ada"
                rr_interval = "Tidak Ada"
                pp_interval = "Tidak Ada"
                axis = "Tidak Ada"

            waves = f"HR: {heart_rate} bpm<br>Axis: {axis}<br>P Wave: {p_wave} sekon<br>QRS Complex: {qrs_comp} sekon<br>ST Interval: {st_interval} sekon<br>PR Interval: {pr_interval} sekon<br>QT Interval: {qt_interval} sekon<br>RR Interval: {rr_interval} sekon<br>PP Interval: {pp_interval} sekon<br>"

            ket += f"pasien memiliki heart rate {heart_rate} per menit kompleks QRS memiliki waktu {qrs_comp} second, dengan Interval gelombang ST {st_interval} second, Interval gelombang PR {pr_interval} second, Interval gelombang QT adalah {qt_interval} second, Interval gelombang RR adalah {rr_interval} second, Interval Gelombang PP adalah {pp_interval} second"
            ket += f"axis yang dimiliki dalam hasil ecg menunjukkan ke arah {axis}"

            data = {"status" : 200, "diagnosis" : diagnosis, "ddx": ddx, "Wave" : waves, "keterangan" : ket, "report_url" : str(self.req2['report_pdf']) }

            """
            {
                "report_id": "c8d904ac-3167-48ad-b822-e60a0d14885a",
                "order_of_photo": 0,
                "is_submitted": true,
                "submit_count": 1,
                "digitization": null,
                "failure_key": null,
                "failure_retake": null
            }
            """
            return data
        except Exception as e:
            print(e)
            traceback.print_exc()
            data = {"status" : 500, "diagnosis" : "No Data", "ddx": "No Data", "Wave" : "ECG Error", "keterangan" : "NetError", "report_url": "" }
            return data

    @TokenSanity
    def DownloadPDF(self, url):
        with self.Requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open("ecg.pdf", 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk:
                    f.write(chunk)
