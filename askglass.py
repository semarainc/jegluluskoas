import requestx
from googletrans import Translator

class AskGlass:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
            "Host" : "glass.health",
            "Origin" : "https://glass.health",
            "Referer" : "https://glass.health/ai",


            }

        self.requests = requestx.RequestsX(header=self.headers)
        self.TARGET_URL = "https://glass.health/api/ai/suggest/"
        self.translator = Translator()

    def GetDiagDdx(self, anamnesis):
        ret_val = {"status" : 200, "clinical" : "", "clinical_id": "", "ddx": "", "ddx_id": ""}
        try:
            en_anam = self.translator.translate(anamnesis, dest='en')
            #en_anam= anamnesis

            tipe = "ddx"
            data = {
                "prompt" : en_anam,
                "suggest_type" : "",
                }

            data['suggest_type'] = tipe
            print("Waiting for Result....")
            print(self.headers)
            ddxr = self.requests.post(self.TARGET_URL, headers=self.headers, data=data)
            ddxt = ddxr.text

            print("HASILNYA ANJIR")
            print(ddxt)

            ddx = ddxr.json()["response_text"]
            ddx_id = self.translator.translate(ddx, dest='id').text

            ret_val["ddx"] = ddx.replace("\n", "<br>")
            ret_val["ddx_id"] = ddx_id.replace("\n", "<br>")

            tipe = "clinical_plan"
            data['suggest_type'] = tipe

            clinical = self.requests.post(self.TARGET_URL, headers=self.headers, data=data).json()["response_text"]

            clinical_id = self.translator.translate(clinical, dest='id').text

            ret_val["clinical"] = clinical.replace("\n", "<br>")
            ret_val["clinical_id"] = clinical_id.replace("\n", "<br>")

            return ret_val
        except Exception as e:
            print(e)
            ret_val["status"] = 500
            return ret_val
