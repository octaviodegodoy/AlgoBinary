from iqoptionapi.stable_api import IQ_Option
import time, json, logging, configparser
from datetime import datetime, date, timedelta
from dateutil import tz
from multiprocessing import Process
import os
import numpy as np

logging.disable(level=logging.DEBUG)


def money_amount():
    # calculate based on balance
    return 20


def banca(iqoapi):
    return iqoapi.get_balance()


def configuracao():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')

    return {'sorosgale': arquivo.get('GERAL', 'sorosgale'),
            'levels': arquivo.get('GERAL', 'levels'),
            'active': arquivo.get('GERAL', 'active'),
            'login': arquivo.get('GERAL', 'login'),
            'password': arquivo.get('GERAL', 'password')}


def mhi_strategy(iqoapi, active):
    # Define the number of digits of price and indicators
    max_dict = 6
    size = 5 * 60
    direction = None
    # Get total of digits used by iq
    iqoapi.start_candles_stream(active, size, max_dict)
    velas = iqoapi.get_realtime_candles(active, size)
    inputs = {
        'open': np.array([]),
        'high': np.array([]),
        'low': np.array([]),
        'close': np.array([]),
        'volume': np.array([]),
        'at': np.array([])
    }

    for timestamp in velas:
        inputs['open'] = np.append(inputs['open'], velas[timestamp]['open'])
        inputs['close'] = np.append(inputs['close'], velas[timestamp]['close'])
        inputs['volume'] = np.append(inputs['volume'], velas[timestamp]['volume'])

    velas[0] = 'g' if inputs['open'][0] < inputs['close'][0] else 'r' if inputs['open'][0] > inputs['close'][0] else 'd'
    velas[1] = 'g' if inputs['open'][1] < inputs['close'][1] else 'r' if inputs['open'][1] > inputs['close'][1] else 'd'
    velas[2] = 'g' if inputs['open'][2] < inputs['close'][2] else 'r' if inputs['open'][2] > inputs['close'][2] else 'd'
    velas[3] = 'g' if inputs['open'][3] < inputs['close'][3] else 'r' if inputs['open'][3] > inputs['close'][3] else 'd'
    velas[4] = 'g' if inputs['open'][4] < inputs['close'][4] else 'r' if inputs['open'][4] > inputs['close'][4] else 'd'
    velas[5] = 'g' if inputs['open'][5] < inputs['close'][5] else 'r' if inputs['open'][5] > inputs['close'][5] else 'd'
    cores = velas[0] + ' ' + velas[1] + ' ' + velas[2] + ' ' + velas[3] + ' ' + velas[4] + ' ' + velas[5]
    print('Cores total ', cores)

    color_candles = 3
    if (cores.count('g') + cores.count('r')) == 6:
        if cores.count('r') < color_candles:
            direction = 'call'
        elif cores.count('g') < color_candles:
            direction = 'put'

    return direction


def run_auto_bo(email, pwd, active, money):
    # Connect to IQOption
    iqoapi = IQ_Option(email, pwd)
    iqoapi.connect()

    while True:
        if iqoapi.check_connect() == False:
            print('Connection error')

            iqoapi.connect()
        else:
            print('\n\nConnection success!')
            break

        time.sleep(1)

    print('Iniciando processamento para ', active)
    balance = banca(iqoapi)
    print('Total balance ', balance)
    direction = mhi_strategy(iqoapi, active)
    print("deu direction ", direction)
    lucro = 0
    operacao = 1
    print('Verificando se ha direction ')
    direction = 'call'
    win_count = 0
    if direction:
        print('Começa a brincadeira ', direction)

        while True:
            minutos = float(((datetime.now()).strftime('%M.%S'))[1:])
            # entrar = True if (4.58 <= minutos <= 5) or minutos >= 9.58 else False
            entrar = True

            if entrar:
                while win_count < 3:
                    if direction:
                        status, id = iqoapi.buy_digital_spot(active, money, direction,
                                                             1) if operacao == 1 else iqoapi.buy(
                            money, active, direction, 1)

                    if status:
                        while True:
                            try:
                                status, valor = iqoapi.check_win_digital_v2(
                                    id) if operacao == 1 else iqoapi.check_win_v3(id)
                            except:
                                status = True
                                valor = 0

                            if status:
                                lucro += round(valor, 2)
                                if valor > 0:
                                    win_count += 1
                                    money += valor
                                elif valor <= 0:
                                    win_count = 0
                                    money = money / 2
                                break

                    #       print('Resultado operação: ', end='')
                    #   print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/', round(lucro, 2),
                    #         ('/ ' + str(i) + ' GALE' if i > 0 else ''))


# Carrega as configuracoes
config = configuracao()

if __name__ == '__main__':
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_DYNAMIC'] = 'FALSE'

    expiration = 5
    actives = {expiration: ('EURUSD', 'EURGBP')}

    email = config['login']
    pwd = config['password']
    operacao = 1

    # Account type REAL, PRACTICE
    acc_type = 'PRACTICE'

    money = float(money_amount())

    for expiration_time, active_list in actives.items():
        for active in active_list:
            Process(target=run_auto_bo, args=(email, pwd, active, money)).start()
