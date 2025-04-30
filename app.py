from flask import Flask,jsonify, request
from flask import render_template
import sqlite3
app = Flask(__name__)

import abc
from datetime import datetime
from collections import defaultdict

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Base Device Class (Template)
class Device(abc.ABC):
    def __init__(self, device_id, name, energy_usage=0):
        # Initialize device attributes
        self.__device_id = device_id
        self.__name = name
        self.__status = 'off'
        self.__energy_usage = energy_usage

    # Getter methods
    # get the id of the device
    def get_id(self):
        return self.__device_id
        # ues private attribute to prevent unauthorized data modification

    def get_name(self):
        return self.__name

    def get_status(self):
        return self.__status

    def set_status(self, status):
        self.__status = status

    def get_energy_usage(self):
        return self.__energy_usage

    def set_energy_usage(self, energy_usage):
        self.__energy_usage = energy_usage

    # Control methods
    # turn on the device
    def turn_on(self):
        self.__status = "on"

    # turn off the device
    def turn_off(self):
        self.__status = "off"

    # print device information
    def __str__(self):
        return f"Device: {self.__name}, ID: {self.__device_id}, Status: {self.__status}, Energy Usage: {self.__energy_usage}kWh"
##新增的部分
    def to_dict(self):
        return {
            "id": self.__device_id,
            "name": self.__name,
            "status": self.__status,
            "energy_usage": self.__energy_usage
        }

# Subclasses for devices
# we will define the light class, thermostat class and camera class by inheriting from the 'Device' class.
class Light(Device):
    def __init__(self, device_id, name, brightness=100):
        super().__init__(device_id, name)  # initialization
        self.brightness = brightness

 ##新增的部分
    def to_dict(self):
        data = super().to_dict()
        data["brightness"] = self.brightness
        return data


class Thermostat(Device):
    def __init__(self, device_id, name, temperature=22):
        super().__init__(device_id, name)
        self.temperature = temperature

    ##新增的部分
    def to_dict(self):
        data = super().to_dict()
        data["temperature"] = self.temperature
        return data

class Camera(Device):
    def __init__(self, device_id, name, resolution='1080p'):
        super().__init__(device_id, name)
        self.resolution = resolution

    ##新增的部分
    def to_dict(self):
        data = super().to_dict()
        data["resolution"] = self.resolution
        return data

# Device Controller
# which is used to manage all the devices
class DeviceController:
    def __init__(self):
        self.devices = {}
        # the dictionary is used for storing devices
        # and the key is the device's id
    def _load_devices(self):
        # 用于连接数据库的，名叫'devices.db'
        conn = sqlite3.connect('devices.db')
        # 创建一个游标对象，用于执行 SQL 语句
        c = conn.cursor()
        #在数据库中创建一个符合特定结构的devices表，以用于存储设备相关的信息。
        #该id列被设置为主键，TEXT为数据类型，REAL为浮点数类型
        c.execute('''CREATE TABLE IF NOT EXISTS devices 
                    (id TEXT PRIMARY KEY, name TEXT, status TEXT, energy_usage REAL, type TEXT,
                    brightness REAL, temperature REAL, resolution TEXT''')
        #从 devices 表中获取所有的行和列的数据
        c.execute("SELECT * FROM devices")
        # 获取查询结果的所有行
        rows = c.fetchall()
        for row in rows:
            #结果集中的行会以列表形式返回（列表里的每个元素代表结果集中的一行）而每一行又以元组的形式呈现，元组中的每个元素对应着查询结果中的一个字段值。
            # 解包每一行的数据
            device_id, name, status, energy_usage, device_type, brightness, temperature, resolution = row
            # 根据设备类型创建相应的设备对象
            if device_type == "Light":
                #创建一个 Light 类的实例对象，并将其赋值给变量 device
                device = Light(device_id, name, brightness)
            elif device_type == "Thermostat":
                device = Thermostat(device_id, name, temperature)
            elif device_type == "Camera":
                device = Camera(device_id, name, resolution)
            #设置设备的状态和能耗
            #set_status 是设备对象的一个方法，可以设置设备的状态。 status是从数据库中查询得到的设备当前状态信息，
            device.set_status(status)
            device.set_energy_usage(energy_usage)
            #将设备对象添加到控制器的设备字典中
            #self.devices可以存储所有的设备对象
            self.devices[device_id] = device
        # 关闭数据库连接
        conn.close()

    def _save_devices(self):
        # 连接到 SQLite 数据库 'devices.db'
        conn = sqlite3.connect('devices.db')
        # 创建一个游标对象，用于执行 SQL 语句
        c = conn.cursor()
        # 删除 'devices' 表中的所有记录,devices字典和数据库中的数据是一致的，简化逻辑
        c.execute("DELETE FROM devices")
        # 遍历控制器的设备字典中的每个设备对象
        for device in self.devices.values():
            # 获取设备的类型名称
            # type(device) 会返回 device 对象所属的类
            device_type = type(device).__name__
            # 根据设备类型执行相应的插入操作c
            if device_type == "Light":
                #? 是占位符，用于后续传入具体的值。NULL 表示该字段的值为空。其中最后参数传入的值为NULL
                c.execute("INSERT INTO devices VALUES (?,?,?,?,?,?,NULL,NULL)",
                          (device.get_id(), device.get_name(), device.get_status(), device.get_energy_usage(),
                           device_type, device.brightness))
            elif device_type == "Thermostat":
                c.execute("INSERT INTO devices VALUES (?,?,?,?,?,NULL,?,NULL)",
                          (device.get_id(), device.get_name(), device.get_status(), device.get_energy_usage(),
                           device_type, device.temperature))
            elif device_type == "Camera":
                c.execute("INSERT INTO devices VALUES (?,?,?,?,?,NULL,NULL,?)",
                          (device.get_id(), device.get_name(), device.get_status(), device.get_energy_usage(),
                           device_type, device.resolution))
        # 提交事务，将插入操作保存到数据库
        conn.commit()
        # 关闭数据库连接
        conn.close()


    # use the device's id as the key to store the device in the dictionary.
    def add_device(self, device):
        device_id = device.get_id()
        self.devices[device_id] = device
        #调用当前类（DeviceController）中的 _save_devices 方法，以更新数据
        self._save_devices()

    # use the device's id as the key to remove the device in the dictionary.
    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            self._save_devices()

    def list_devices(self):
        #返回一个由设备字典组成的列表，便于转换为 JSON 格式返回给客户端和进一步操作，如计算设备总能耗，可利用字典进行遍历
        return [device.to_dict() for device in self.devices.values()]

    def get_device(self, device_id):
        #方便设备检索
        return self.devices.get(device_id)

    def execute_command(self, device_id, command):
        if device_id in self.devices:
            device = self.devices[device_id]
            if command == "on":
                device.turn_on()
            elif command == "off":
                device.turn_off()
            else:
                print("please check your command")
                self._save_devices()
                #返回设备最新的状态
                return device.to_dict()
        return {"error": "Device not found"}


# Smart Home Hub (Singleton)
class SmartHomeHub:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartHomeHub, cls).__new__(cls)
            cls._instance.controller = DeviceController()
        return cls._instance

    # print the working information of a specific device.
    def schedule_task(self, device_id, command, time):
        print(f"scheduled task: device {device_id} will obey '{command}' command,at {time}")

    def display_status(self):
        print("status of all devices:")
        self.controller.list_devices()

    def total_energy_usage(self):
        # create a iterator which will allow us to iterate through each device one by one.
        devices_iterator = iter(self.controller.devices.values())

        def recursive_calculate(devices_iterator):
            return sum(device.get_energy_usage() for device in self.controller.devices.values())


hub = SmartHomeHub()


HOSTNAME = "127.0.0.1"

PORT = 3306

USERNAME = "root"

PASSWORD = "123456"

DATABASE = "device"

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"

db = SQLAlchemy(app)
with app.app_context():
    with db.engine.connect() as conn:
        rs = conn.execute(text("select 1"))
        print(rs.fetchone())


@app.route('/')
def index():
    return render_template('index.html')

# 下面是API endpoint
@app.route('/devices', methods=['GET']) #get表得到用户想得到数据
def get_devices():
    devices = hub.controller.list_devices()
    return jsonify(devices) #调用函数得到数据再以json格式返回

@app.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    device = hub.controller.get_device(device_id)
    if device:
        return jsonify(device.to_dict())
    return jsonify({"error": "Device not found"}), 404

@app.route('/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    device_type = data.get('type')
    device_id = data.get('id')
    name = data.get('name')
    if device_type == "Light":
        brightness = data.get('brightness', 100)
        device = Light(device_id, name, brightness)
    elif device_type == "Thermostat":
        temperature = data.get('temperature', 22)
        device = Thermostat(device_id, name, temperature)
    elif device_type == "Camera":
        resolution = data.get('resolution', '1080p')
        device = Camera(device_id, name, resolution)
    else:
        return jsonify({"error": "Invalid device type"}), 400
    hub.controller.add_device(device) #创建好的设备对象添加到设备管理系统中。
    return jsonify(device.to_dict()), 201  #状态码为 201，表示已创建成功，告知客户端设备已成功添加。

@app.route('/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    hub.controller.remove_device(device_id)
    return jsonify({"message": "Device removed successfully"})

@app.route('/devices/<device_id>/<command>', methods=['PUT'])
def execute_command(device_id, command):
    result = hub.controller.execute_command(device_id, command)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/energy_usage', methods=['GET'])
def get_total_energy_usage():
    energy_usage = hub.total_energy_usage()
    return jsonify({"total_energy_usage": energy_usage})


if __name__ == '__main__':
    app.run(debug = True)
