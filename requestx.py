import requests
import time

class RequestsX:
    def __init__(self, header={}, cookie={}):
        self.headers = header
        self.cookies = cookie
        self.ERROR_CODE = [400, 404, 403, 503, 500]

    def get(self, url=None, headers={}, retry=7, **kwargs):
        headers = {**self.headers, **headers}

        trial = 0
        while trial <= retry:
            try:
                req = requests.get(url, headers=headers, timeout=30, **kwargs)
                #print(req.text)
                if req.status_code not in self.ERROR_CODE:
                    #print(req.status_code)
                    #print(req.text)
                    return req
            except Exception as e:
                print("Error Occured When Doing Get Request (Trial): ", e)

            trial += 1
            time.sleep(5)

        return req

    def post(self, url=None, headers={}, retry=7, **kwargs):
        headers = {**self.headers, **headers}

        trial = 0

        while trial <= retry:
            try:
                req = requests.post(url, headers=headers, timeout=30, **kwargs)
                #print(req.text)
                if req.status_code not in self.ERROR_CODE:
                    #print(req.status_code)
                    #print(req.text)
                    return req
            except Exception as e:
                print("Error Occured When Doing Post Request (Trial): ", e)

            trial += 1
            time.sleep(5)

        return req

    def put(self, url=None, headers={}, retry=7, **kwargs):
        headers = {**self.headers, **headers}

        trial = 0

        while trial <= retry:
            try:
                req = requests.put(url, headers=headers, timeout=30, **kwargs)
                #print(req.text)
                if req.status_code not in self.ERROR_CODE:
                    #print(req.status_code)
                    #print(req.text)
                    return req
            except Exception as e:
                print("Error Occured When Doing Post Request (Trial): ", e)

            trial += 1
            time.sleep(5)

        return req
