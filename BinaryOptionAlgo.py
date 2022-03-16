from iqoptionapi.stable_api import IQ_Option
import time, logging, configparser
from datetime import datetime, date, timedelta
from multiprocessing import Process
import os
import numpy as np

logging.disable(level=logging.DEBUG)


def get_balance(iqoapi):
    return iqoapi.get_balance()


def get_payout(iqoapi, active):
    iqoapi.subscribe_strike_list(active, 1)
    while True:
        d = iqoapi.get_digital_current_profit(active, 1)
        if d:
            d = round(int(d) / 100, 2)
            break
        time.sleep(1)
    iqoapi.unsubscribe_strike_list(active, 1)

    return d


def configuracao():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')

    return {'sorosgale': arquivo.get('GERAL', 'sorosgale'),
            'levels': arquivo.get('GERAL', 'levels'),
            'active': arquivo.get('GERAL', 'active'),
            'login': arquivo.get('GERAL', 'login'),
            'password': arquivo.get('GERAL', 'password')}


def entradas(iqoapi, par, entrada, direcao, operacao):
    status, id = iqoapi.buy_digital_spot(par, entrada, direcao, 1) if operacao == 1 else iqoapi.buy(
        entrada, par, direcao, 1)

    if status:
        while True:
            status, valor = iqoapi.check_win_digital_v2(id) if operacao == 1 else iqoapi.check_win_v3(id)
            if status:
                if valor > 0:
                    return status, round(valor, 2)
                else:
                    return status, round(valor, 2)
                break
    else:
        return False, 0


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


def get_initial_amount(iqoapi, active, amount_by_payout):
    balance = get_balance(iqoapi)
    payout = str(get_payout(iqoapi, active))
    initial_percent = float(amount_by_payout[payout]) / 100
    return round(initial_percent * balance, 2)




def run_auto_bo(active, email, pwd):
    # Connect to IQOption
    iqoapi = IQ_Option(email, pwd)
    iqoapi.connect()
    # Account type REAL, PRACTICE
    acc_type = 'PRACTICE'
    iqoapi.change_balance(acc_type)  # PRACTICE / REAL
    operacao = 1

    while True:
        if not iqoapi.check_connect():
            print('Connection error')

            iqoapi.connect()
        else:
            print('\n\nConnection success!')
            break

        time.sleep(1)

    amount_by_payout = {'0.74': '0.99', '0.75': '0.97', '0.76': '0.96', '0.77': '0.94', '0.78': '0.93', '0.79': '0.91',
                        '0.80': '0.90', '0.81': '0.88', '0.82': '0.87', '0.83': '0.85', '0.84': '0.84', '0.85': '0.83',
                        '0.86': '0.82', '0.87': '0.80', '0.88': '0.79', '0.89': '0.78', '0.90': '0.77', '0.91': '0.76',
                        '0.92': '0.75', '0.93': '0.74', '0.94': '0.73', '0.95': '0.72', '0.96': '0.71', '0.97': '0.70',
                        '0.98': '0.69', '0.99': '0.68', '100': '0.67'}
    direction = None
    lucro_total = 0
    while True:
        print('Iniciando processamento para ', active)
        initial_amount = get_initial_amount(iqoapi, active, amount_by_payout)
        print('Initial amount ', initial_amount)
        direction = mhi_strategy(iqoapi, active)
        print("deu direction ", direction)
        lucre_opera = 0

        minutos = float(((datetime.now()).strftime('%M.%S'))[1:])
        entrar = True if (4.58 <= minutos <= 5) or minutos >= 9.58 else False

        if entrar:
            while True:
                #verifica velas
                status, valor = entradas(iqoapi, active, initial_amount, direction, 1)
                lucro_total += valor
                if status and valor < 0:
                    perda = abs(valor)

                    for i in range(2):
                        if lucre_opera >= perda:
                            break
                        if direction:

                            status, valor_soros = entradas(iqoapi, active, (perda / 2) + lucre_opera, direction, 1)

                        if status:
                            if valor_soros > 0:
                                lucre_opera += round(valor_soros, 2)
                            else:
                                lucre_opera = 0
                                perda += round(abs(valor_soros), 2) / 2

                        print('Resultado operação: ', end='')
                        print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/', round(lucre_opera, 2),
                              ('/ ' + str(i) + ' GALE' if i > 0 else ''))


# Carrega as configuracoes
config = configuracao()

if __name__ == '__main__':
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_DYNAMIC'] = 'FALSE'

    expiration = 5
    actives = {expiration: ('EURUSD',)}
    email = config['login']
    pwd = config['password']

    for expiration_time, active_list in actives.items():
        for active in active_list:
            Process(target=run_auto_bo, args=(active, email, pwd)).start()
