import requests
import time
import hashlib
import logging

logger = logging.getLogger('palideenz-api')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('recent.log', encoding='utf-8')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
fh.setFormatter(formatter)
logger.addHandler(fh)
#logger.info('Loaded smite-python {}, github.com/jaydenkieran/smite-python'.format(version))

class PaladinsSession():
    
    def __init__(self, devid, devkey, lang=1):
        self.dev_Id = devid
        self.key = devkey
        self.api_url = 'http://api.paladins.com/paladinsapi.svc'
        self.lang = lang
        self.sessionid = None

    def _form_url(self, methodname, parameters=None):
        signature = self._create_signature(methodname)
        timestamp = self._get_timestamp()
        methodname += "json"
        url = [self.api_url,methodname,self.dev_Id,signature,self.sessionid,timestamp]
        if parameters:
            #print(parameters)
            for param in parameters:
                url.append(str(param))
                

        url = '/'.join(url)
        return url

    def _create_signature(self, command):
        s = self.dev_Id + command + self.key + time.strftime("%Y%m%d%H%M%S", time.gmtime())
        m = hashlib.md5(bytes(s.encode()))
        m.digest()
        return str(m.hexdigest())

    def _create_session(self):
        sig = self._create_signature('createsession')
        ctime = self._get_timestamp()
        url = '/'.join([self.api_url,'createsessionjson',self.dev_Id,sig,ctime])
        return(requests.get(url).json())

    @staticmethod
    def _get_timestamp():
        return time.strftime("%Y%m%d%H%M%S", time.gmtime())
    
    def _make_request(self, methodname, parameters=None):
        try:
            if not self.sessionid:
                self.sessionid = self._create_session()['session_id']
            
            url = self._form_url(methodname,parameters)
            logger.info('Built request URL for {}: {}'.format(methodname, url))
            return(requests.get(url).json())
        except:
            logging.exception("error when making request")


