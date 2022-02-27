from flask import Flask
from flask import request, jsonify
from flask import render_template
from effects import Ledstrip
import effects
from multiprocessing import Process

app = Flask(__name__)
app.config['DEBUG'] = False

ledstrip = Ledstrip()

POWER = False
process = None
USAGE_TIME = 0
EFFECT = {'id': -1, 'settings': -1}


def conv_p_status(value): return 'ON' if value else 'OFF'


@app.route('/', methods=['GET'])
def index():
    global POWER
    return render_template('index.html', power=conv_p_status(POWER), ws=ledstrip.wall_settings,
                           usage_time=USAGE_TIME, effect=str(EFFECT))


@app.route('/api/v1/status', methods=['GET'])
def status():
    global POWER, EFFECT
    wall_settings = ledstrip.wall_settings
    color_id_name = {str(v): k for k, v in ledstrip.colors_list.items()}
    for k in wall_settings.keys():
        wall_settings[k][0] = color_id_name.get(str(wall_settings[k][0]), "RANDOM")
    status = {'power_supply_status': conv_p_status(POWER),
              'wall_settings': wall_settings,
              'effect': EFFECT
              }
    return jsonify(status)


@app.route('/api/v1/configuration', methods=['GET'])
def configuration():
    return jsonify(ledstrip.default_effects_settings)


@app.route('/api/v1/powering', methods=['GET', 'POST'])
def powering():
    global POWER
    if request.method == 'POST':
        data = request.get_json().get('power_supply_status')
        if data == 'ON':
            if not POWER:
                POWER = True
                ledstrip.power_switch('ON')
                ledstrip.set_off()
            return jsonify({'power_supply_status': conv_p_status(POWER)})
        elif data == 'OFF':
            if POWER:
                POWER = False
                ledstrip.power_switch('OFF')
            return jsonify({'power_supply_status': conv_p_status(POWER)})
        else:
            return str([type(data), str(data)])
    else:
        return jsonify({'power_supply_status': POWER})


@app.route('/api/v1/controller', methods=['POST'])
def controller():
    data = request.get_json()
    if 'power_supply_status' in data:
        if data.get('power_supply_status') == 'OFF':
            ledstrip.controller_shutdown()
            return jsonify({'power_supply_status': 'OFF'})


@app.route('/api/v1/general', methods=['POST'])
def general():
    """
    Example post:
    {
    'wall':0
    #'color':'RED'
    #'brightness':1.0
    }
    """
    global process
    global OFF
    data = request.get_json()
    if 'wall' in data:
        wall = str(data['wall'])
    else:
        print('Blad')
        return 'error'
        pass
    if process is not None:
        process.terminate()
        process = None
        ledstrip.set_white()
    if 'color' in data:
        color = data['color']
        if color == 'RANDOM':
            if wall == '0':
                color = ledstrip.random_color(ledstrip.wall_settings["1"][0])
            else:
                color = ledstrip.random_color(ledstrip.wall_settings[wall][0])
        else:
            color = ledstrip.colors_list.get(color, [0,0,0])
        if wall == '0':
            for k in ledstrip.wall_settings.keys():
                ledstrip.wall_settings[k][0] = color
        else:
            ledstrip.wall_settings[wall][0] = color
    if 'brightness' in data:
        brightness = float(data['brightness'])
        if wall == '0':
            for k in ledstrip.wall_settings.keys():
                ledstrip.wall_settings[k][1] = brightness
        else:
            ledstrip.wall_settings[wall][1] = brightness
    for k, v in ledstrip.wall_settings.items():
        ledstrip.set_color_wall(color=v[0], wall=ledstrip.walls_list[k], brightness=v[1])
    return jsonify(data)


@app.route('/api/v1/effects', methods=['POST'])
def effect():
    if request.method == 'POST':
        global process
        global EFFECT
        data = request.get_json()
        if 'id' in data and 'settings' in data:
            effect_id = int(data['id'])
            settings = data['settings']
            EFFECT = data
        elif 'id' in data and int(data['id']) == -1:
            if process is not None:
                process.terminate()
                process = None
            for k, v in ledstrip.wall_settings.items():
                ledstrip.set_color_wall(color=v[0], wall=ledstrip.walls_list[k], brightness=v[1])
            return data
        else:
            return 'error'
        if process is not None:
            process.terminate()
        if effect_id == 1:
            process = Process(target=ledstrip.rainbow_cycle,
                              kwargs={'speed': float(settings['speed']), 'direction': settings['direction'],
                                      'brightness': float(settings['brightness'])})
            process.start()
        elif effect_id == 2:
            process = Process(target=ledstrip.train,
                              kwargs={'background_col': ledstrip.colors_list[settings['background_color']],
                                      'train_color': ledstrip.colors_list[settings['train_color']],
                                      'train_speed': float(settings['train_speed']),
                                      'train_size': int(settings['train_size']),
                                      'background_brightness': float(settings['background_brightness']),
                                      'train_brightness': float(settings['train_brightness'])})
            process.start()
        elif effect_id == 3:
            process = Process(target=ledstrip.akuku, kwargs={'color_1': ledstrip.colors_list[settings['color_1']],
                                                             'color_2': ledstrip.colors_list[settings['color_2']],
                                                             'dimmer_speed': float(settings['speed']),
                                                             'max_level': float(settings['max_level']),
                                                             'min_level': float(settings['min_level'])})
            process.start()
        return jsonify(data)
    return 'brak'

# if __name__ == '__main__':
# app.run(host="0.0.0.0", port=5000)
