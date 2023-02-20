import socket
import os
import json
import time
import sqlite3
import base64
import traceback

import askglass
import pmcardio

from sqlite3 import Error

from flask import Flask
from flask import Flask, redirect, request, jsonify, make_response, render_template, url_for, send_file, send_from_directory, current_app
from threading import Thread, Event
from queue import Queue
from dbctl import apeksdbctl
from datetime import datetime

from multiprocessing import Process, Queue

import run

app = run.main()

busyo = 0
q = None
worker = None
URL = ""

def ThreadE(q):
    global busyo, URL

    busyo =1

    data = q.get()
    try:
        img_raw = imgdata = base64.b64decode(data.get("image").split(',')[1])
        with open('ecg.jpg', 'wb') as ecg:
            ecg.write(img_raw)

        img = open('ecg.jpg', 'rb')

        with open("token.txt") as f:
            nana = f.read()

        tokener = json.loads(nana)

        Cardio = pmcardio.PMCardio(token=tokener['AuthenticationResult']['AccessToken'], refresh_token=tokener['REFRESH_TOKEN'])

        kelamin = data.get('kelamin')

        isrythm = 0
        page = 1
        rows = 0
        columns=0

        if "." in data.get('voltage'):
            voltage = float(data.get("voltage"))
        else:
            voltage = int(data.get("voltage"))

        if "." in data.get('speed'):
            speed = float(data.get("speed"))
        else:
            speed = int(data.get("speed"))

        umur = data.get("umur")
        kelamin = data.get("kelamin")

        if data.get("tipe") == '1 page, 6x2 leads':
            isrythm = 0
            rows = 6
            columns = 2
        elif data.get('tipe') == '1 page, 6x2 rhythm lead':
            isrythm = 1
            rows = 6
            columns = 2
        elif data.get('tipe') == '1 page, 3x4 lead':
            isrythm = 0
            rows = 3
            columns = 4
        elif data.get('tipe') == '1 page, 3x4 rhythm lead':
            isrythm = 1
            rows = 3
            columns = 4
        elif data.get('tipe') == '1 page, 3x4, 2 rhythm lead':
            isrythm = 2
            rows = 3
            columns = 4
            page = 2
        elif data.get('tipe') == '1 page, 3x4, 3 rhythm lead':
            isrythm = 3
            rows = 3
            columns = 4
        elif data.get('tipe') == '1 page, 12x1, leads':
            isrythm = 0
            rows = 12
            columns = 1
        elif data.get('tipe') == '1 page, 3x4, 2 rhythm lead':
            isrythm = 2
            rows = 3
            columns = 4

        resp = Cardio.AnalyzeECG(img, isrythm, page, rows, columns, voltage, speed, umur, kelamin)
        URL = resp['report_url']
    except Exception as e:
        print(e)
        traceback.print_exc()
        resp = {"status" : 500, "diagnosis" : "No Data", "ddx": "No Data", "Wave" : "ECG Error", "keterangan" : "NetError" }

    q.put_nowait(resp)
    os.remove("measure.run")

def ThreadD(q):
    global busyo

    busyo =1

    data = q.get()

    str_rm = "pasien "

    if data.get("kelamin", "") is not "":
        str_rm += f"berjenis kelamin {data.get('kelamin')} "

    if data.get("usia", "") is not "":
        str_rm += f"berusia {data.get('usia')} "

    if data.get("td", "") is not "":
        str_rm += f"memiliki tekanan darah {data.get('td')} mmHg "

    if data.get("bb", "") is not "":
        str_rm += f"pasien memiliki berat badan {data.get('bb')} Kg "

    if data.get("suhu", "") is not "":
        str_rm += f"suhu tubuh {data.get('suhu')} derajat celcius "

    if data.get("keluhan", "") is not "":
        str_rm += f"pasien mengeluhkan {data.get('keluhan')} "

    if data.get("onset", "") is not "":
        str_rm += f"keluhan ini sudah terjadi sejak {data.get('onset')}. "

    if data.get("kualitas") is not None:
        str_rm += f"keluhan ini {data.get('kualitas')}, "

    if data.get("kuantitas", "") is not "":
        str_rm += f"kuantitas {data.get('kuantitas')}, "

    if data.get("memperberat", "") is not "":
        str_rm += f"keluhan ini memberat bila {data.get('mempeberat')}, "

    if data.get("memperingan", "") is not "":
        str_rm += f"keluha ini mereda bila {data.get('memperingan')}, "

    if data.get("sakitdulu", "") is not "":
        str_rm += f"pasien memiliki riwayat penyakit dahulu berupa {data.get('sakitdulu')}, "

    if data.get("sakitkeluarga", "") is not "":
        str_rm += f"keluarga pasien memiliki riwayat penyakit, {data.get('sakitkeluarga')}. "

    if data.get("keterangan", "") is not "":
        str_rm += f"{data.get('keterangan')} "

    #str_rm = f"""
    #pasien berjenis kelamin {data.get("kelamin", "laki-laki")} berusia {data.get("usia", 10)} memiliki tekanan darah {data.get("td")} mmHg, pasien juga #memiliki berat badan {data.get("bb")} kg, suhu {data.get("suhu")} derajat celsius, mengeluhkan adanya {data.get("keterangan")}
    #"""

    viggnete = askglass.AskGlass()
    resp = viggnete.GetDiagDdx(str_rm)

    #db_ = apeksdbctl.create_connection('apeks.db')
    #apeksdbctl.AddData(db_, [str(nama), str(jk), str(usia/12), str(waktu), str(Berat), str(Tinggi), str(zimt['Status'])])

    q.put_nowait(resp)
    os.remove("measure.run")

@app.route('/', methods=["GET"])
def welcome():
    return render_template('welcome.html')

@app.route('/askglass', methods=["GET"])
def index():
    global q, worker, busyo
    #return render_template('index.html')
    if os.path.exists("measure.run"):
        print("[DEBUG] Busy State Terminate...")
        os.remove("measure.run")
        worker.terminate()
        busyo = 0

    return render_template('index.html')

@app.route('/pmcardio', methods=["GET"])
def PMCardio():
    global q, worker, busyo
    #return render_template('index.html')
    if os.path.exists("measure.run"):
        print("[DEBUG] Busy State Terminate...")
        os.remove("measure.run")
        worker.terminate()
        busyo = 0

    return render_template('cardio.html')

@app.route('/purge', methods=["POST"])
def Purge():
    db_ = apeksdbctl.create_connection("apeks.db")
    apeksdbctl.PurgeData(db_)
    return "ok"

@app.route('/admin', methods=["GET", "POST"])
def Admin():
    db_ = apeksdbctl.create_connection('apeks.db')
    datas = apeksdbctl.LoadDatas(db_)
    return render_template("admin.html", data=datas)

@app.route('/clear', methods=["GET", "POST"])
def bersih():
    global busyo

    if os.path.exists("measure.run"):
        print("[DEBUG] Busy State Terminate...")
        os.remove("measure.run")
        worker.terminate()
        busyo = 0

    busyo = 0
    return "ok"

@app.route('/measure', methods=["GET", "POST"])
def measure():
    global q, worker, busyo
    
    if os.path.exists("measure.run") and busyo == 1:
        print("[DEBUG] Busy State Terminate...")
        os.remove("measure.run")
        worker.terminate()

    busyo = 1
    q = Queue(maxsize=0)
    data = request.get_json(force=True)
    
    with open("measure.run", 'w') as f:
        f.write("1")

    worker = Process(target=ThreadD, args=(q,))
    worker.daemon = True
    worker.start()
    
    q.put(data)
    
    while os.path.exists("measure.run"):
        time.sleep(2)
    #worker.join()

    resp = q.get()
    busyo = 0
    return make_response(jsonify(resp), 200)

@app.route('/measure2', methods=["GET", "POST"])
def measure2():
    global q, worker, busyo

    if os.path.exists("measure.run") and busyo == 1:
        print("[DEBUG] Busy State Terminate...")
        os.remove("measure.run")
        worker.terminate()

    busyo = 1
    q = Queue(maxsize=0)
    data = request.get_json(force=True)

    with open("measure.run", 'w') as f:
        f.write("1")

    worker = Process(target=ThreadE, args=(q,))
    worker.daemon = True
    worker.start()

    q.put(data)

    while os.path.exists("measure.run"):
        time.sleep(2)
    #worker.join()

    resp = q.get()
    busyo = 0
    return make_response(jsonify(resp), 200)

@app.route('/download', methods=['GET', 'POST'])
def download():
    global URL
    print("DownloadPDF")
    with open("token.txt") as f:
        nana = f.read()

    tokener = json.loads(nana)

    Cardio = pmcardio.PMCardio(token=tokener['AuthenticationResult']['AccessToken'], refresh_token=tokener['REFRESH_TOKEN'])
    Cardio.DownloadPDF(URL)
    print("PDF DOWNLOADED")
    uploads = os.path.join(current_app.root_path, "ecg.pdf")
    return send_file(uploads, as_attachment=True, download_name='ECG Report.pdf')

if __name__ == '__main__':
    apeksdbctl.DbInit()
    app.run(host='0.0.0.0', port=5050, debug=True)
