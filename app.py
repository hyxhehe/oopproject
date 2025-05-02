from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import abc
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# MySQL 数据库配置
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "123456"
DATABASE = "device"
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Base Device Class (Template)
class Device(abc.ABC):
    def __init__(self, device_id, name, energy_usage=0):
        self.__device_id = device_id
        self.__name = name
        self.__status = 'off'
        self.__energy_usage = energy_usage

    def get_id(self):
        return self.__device_id

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

    def turn_on(self):
        self.__status = "on"

    def turn_off(self):
        self.__status = "off"

    def __str__(self):
        return f"Device: {self.__name}, ID: {self.__device_id}, Status: {self.__status}, Energy Usage: {self.__energy_usage}kWh"

    def to_dict(self):
        return {
            "id": self.__device_id,
            "name": self.__name,
            "status": self.__status,
            "energy_usage": self.__energy_usage
        }


# Subclasses for devices
class Light(Device):
    def __init__(self, device_id, name, brightness=100):
        super().__init__(device_id, name)
        self.brightness = brightness

    def to_dict(self):
        data = super().to_dict()
        data["brightness"] = self.brightness
        return data


class Thermostat(Device):
    def __init__(self, device_id, name, temperature=22):
        super().__init__(device_id, name)
        self.temperature = temperature

    def to_dict(self):
        data = super().to_dict()
        data["temperature"] = self.temperature
        return data


class Camera(Device):
    def __init__(self, device_id, name, resolution='1080p'):
        super().__init__(device_id, name)
        self.resolution = resolution

    def to_dict(self):
        data = super().to_dict()
        data["resolution"] = self.resolution
        return data


# Device model for SQLAlchemy
class DeviceModel(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    status = db.Column(db.String(255))
    energy_usage = db.Column(db.Float)
    type = db.Column(db.String(255))
    brightness = db.Column(db.Float)
    temperature = db.Column(db.Float)
    resolution = db.Column(db.String(255))


# Device Controller
class DeviceController:
    def __init__(self):
        self.devices = {}
        self._load_devices()

    def _load_devices(self):
        try:
            devices = DeviceModel.query.all()
            for device in devices:
                device_id = device.id
                name = device.name
                status = device.status
                energy_usage = device.energy_usage
                device_type = device.type
                brightness = device.brightness
                temperature = device.temperature
                resolution = device.resolution

                if device_type == "Light":
                    device_obj = Light(device_id, name, brightness)
                elif device_type == "Thermostat":
                    device_obj = Thermostat(device_id, name, temperature)
                elif device_type == "Camera":
                    device_obj = Camera(device_id, name, resolution)

                device_obj.set_status(status)
                device_obj.set_energy_usage(energy_usage)
                self.devices[device_id] = device_obj
            logging.debug("Devices loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading devices: {e}")

    def _save_devices(self):
        try:
            DeviceModel.query.delete()
            for device in self.devices.values():
                device_type = type(device).__name__
                new_device = DeviceModel(
                    id=device.get_id(),
                    name=device.get_name(),
                    status=device.get_status(),
                    energy_usage=device.get_energy_usage(),
                    type=device_type
                )
                if device_type == "Light":
                    new_device.brightness = device.brightness
                elif device_type == "Thermostat":
                    new_device.temperature = device.temperature
                elif device_type == "Camera":
                    new_device.resolution = device.resolution

                db.session.add(new_device)
            db.session.commit()
            logging.debug("Devices saved successfully.")
        except Exception as e:
            logging.error(f"Error saving devices: {e}")
            db.session.rollback()

    def add_device(self, device):
        device_id = device.get_id()
        self.devices[device_id] = device
        self._save_devices()

    def remove_device(self, device_id):
        if device_id in self.devices:
            del self.devices[device_id]
            self._save_devices()

    def list_devices(self):
        return [device.to_dict() for device in self.devices.values()]

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def execute_command(self, device_id, command):
        if device_id in self.devices:
            device = self.devices[device_id]
            if command == "on":
                device.turn_on()
            elif command == "off":
                device.turn_off()
            else:
                logging.warning("Invalid command received.")
            self._save_devices()
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

    def schedule_task(self, device_id, command, time):
        logging.info(f"scheduled task: device {device_id} will obey '{command}' command,at {time}")

    def display_status(self):
        logging.info("status of all devices:")
        return self.controller.list_devices()

    def total_energy_usage(self):
        return sum(device.get_energy_usage() for device in self.controller.devices.values())


hub = SmartHomeHub()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_device', methods=['GET'])
def add_device_page():
    return render_template('add_advice.html')

@app.route('/remove_device', methods=['GET'])
def remove_device_input():
    return render_template('remove_device.html')

@app.route('/confirm_remove_device', methods=['GET'])
def confirm_remove_device():
    # 这里编写处理确认删除设备的逻辑，例如获取设备信息展示给用户确认等
    return "Confirm remove device page"  # 这里先简单返回，后续根据实际逻辑修改

@app.route('/device_control', methods=['GET'])
def device_control_page():
    return render_template('device_status.html')
@app.route('/devices', methods=['GET'])
def get_devicelist():
    try:
        devices = hub.controller.list_devices()
        return render_template('devicelist.html', devices=devices)
    except Exception as e:
        logging.error(f"Error getting devices: {e}")
        return jsonify({"error": "An error occurred while getting devices"}), 500


@app.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    try:
        device = hub.controller.get_device(device_id)
        if device:
            return jsonify(device.to_dict())
        return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        logging.error(f"Error getting device: {e}")
        return jsonify({"error": "An error occurred while getting the device"}), 500


@app.route('/devices', methods=['POST'])
def add_device():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        device_type = data.get('type')
        device_id = data.get('id')
        name = data.get('name')
        if not device_type or not device_id or not name:
            return jsonify({"error": "Missing required fields (type, id, name)"}), 400
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
        hub.controller.add_device(device)
        return jsonify(device.to_dict()), 201
    except Exception as e:
        logging.error(f"Error adding device: {e}")
        return jsonify({"error": "An error occurred while adding the device"}), 500


@app.route('/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    try:
        hub.controller.remove_device(device_id)
        return jsonify({"message": "Device removed successfully"})
    except Exception as e:
        logging.error(f"Error removing device: {e}")
        return jsonify({"error": "An error occurred while removing the device"}), 500


@app.route('/devices/<device_id>/<command>', methods=['GET', 'PUT'])
def execute_command(device_id, command):
    try:
        result = hub.controller.execute_command(device_id, command)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return jsonify({"error": "An error occurred while executing the command"}), 500


@app.route('/energy_usage', methods=['GET'])
def get_total_energy_usage():
    try:
        devices = hub.controller.list_devices()
        if devices:
            device = devices[0]
            result = {
                "id": device["id"],
                "name": device["name"],
                "energy_usage": device["energy_usage"]
            }
            return jsonify(result), 200
        else:
            # 无设备时返回符合结构的空数据
            result = {
                "id": "",
                "name": "",
                "energy_usage": 0,
            }
            return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error getting energy usage: {e}")
        return jsonify({"error": "An error occurred while getting energy usage"}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
