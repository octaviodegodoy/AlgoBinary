from iqoptionapi.stable_api import IQ_Option
import time, json, logging, configparser
from datetime import datetime, date, timedelta
from dateutil import tz
from multiprocessing import Process
import os

logging.disable(level=logging.DEBUG)


def money_amount():
    # calculate based on balance
    return 20


def configuracao():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')

    return {'sorosgale': arquivo.get('GERAL', 'sorosgale'),
            'levels': arquivo.get('GERAL', 'levels'),
            'active': arquivo.get('GERAL', 'active'),
            'login': arquivo.get('GERAL', 'login'),
            'password': arquivo.get('GERAL', 'password')}


def run_auto_bo(email, pwd, active):
    # Connect to IQOption
    iqoapi = IQ_Option(email, pwd)
    iqoapi.connect()
    print('Iniciando processamento para ', active)

# Carrega as configuracoes
config = configuracao()

if __name__ == '__main__':
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_DYNAMIC'] = 'FALSE'

    expiration = 5
    actives = {expiration: (
        'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP')}

    email = config['login']
    pwd = config['password']

    # Account type REAL, PRACTICE
    acc_type = 'PRACTICE'

    money = float(money_amount())

    for expiration_time, active_list in actives.items():
        for active in active_list:
            Process(target=run_auto_bo, args=(email, pwd, active)).start()
