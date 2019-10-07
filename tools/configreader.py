from configparser import ConfigParser
import os


def reader(config_path):
    config = ConfigParser()
    config.read(config_path,encoding='utf8')
    return config


config_path = os.path.abspath(__file__+'/../../'+'config/config.ini')
config = reader(config_path)
