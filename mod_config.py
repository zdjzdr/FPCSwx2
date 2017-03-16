# coding:utf-8
# designer:Zhoulang
import configparser
import os


# 获取配置文件
def get_config(section, key):
    config = configparser.ConfigParser()
    path = os.path.split(os.path.realpath(__file__))[0]+'\\wxcfg.conf'
    if config.read(path, encoding='utf-8'):
        return config.get(section, key)
    else:
        print("配置文件不存在,请重新运行服务器,打开http:127.0.0.1:3456/cfg 重新设置")
        s = {
            'host': '127.0.0.1',
            'database': 'ESApp1',
            'user': 'sa',
            'pwd': '',
            'port': 1433,
            'customstr': '【FPCS系统提醒】',
            'Secret': '',
            'TOKEN': 'eswx',
            'EncodingAESKey': '',
            'CorpId': '',
            'agent_id': 0,
            'tm': 60,
            'msg_limit': 1
        }
        config['wx'] = s
        with open(path, 'w', encoding='utf-8') as f:
            config.write(f)


# 写入配置文件
def set_config(section, dic=None):
    config = configparser.ConfigParser()
    path = os.path.split(os.path.realpath(__file__))[0] + '\\wxcfg.conf'
    config[section] = dic
    # config.set(section, key, value)
    with open(path, 'w', encoding='utf-8') as f:
        config.write(f)
