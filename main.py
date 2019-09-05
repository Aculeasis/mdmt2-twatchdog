import subprocess
import threading
import time

import logger
from utils import pretty_time

NAME = 'twatchdog'
API = 9999
TERMINAL_VER_MIN = (0, 12, 16)
TW_CONFIG = '{}_config'.format(NAME)


class Main(threading.Thread):
    TWATCHDOG = NAME
    NET_CHANNEL = 'net'
    WAIT_INTERVAL = 60

    def __init__(self, cfg, log, owner):
        super().__init__(name=NAME)
        self.cfg, self.log, self.own = cfg, log, owner
        self._interval, self._actions, self._custom_cmd = self._load_cfg()
        self._send_notify = self.own.registration(self.TWATCHDOG)
        self.disable = True
        self.work = False
        self._wait = threading.Event()
        self._check_wait = threading.Event()
        if not self._actions:
            self.log('Empty actions')
            return
        try:
            # noinspection PyProtectedMember
            self._terminal_diagnostic_msg = self.own._terminal.diagnostic_msg
            if not callable(self._terminal_diagnostic_msg):
                raise RuntimeError('diagnostic_msg must be callable')
        except Exception as e:
            self.log('Internal error: {}'.format(e), logger.ERROR)
            return
        self.disable = False

    def start(self):
        self.work = True
        self._registration()
        msg = 'interval: {} sec; '.format(self._interval) if self._interval else ''
        msg += 'actions: {}'.format(', '.join(self._actions))
        msg += '; custom_cmd: \'{}\''.format(self._custom_cmd) if self._custom_cmd else ''
        self.log(msg)
        super().start()

    def join(self, timeout=None):
        self.work = False
        self._unregistration()
        self._check_wait.set()
        self._wait.set()
        super().join(timeout)

    def run(self):
        while self.work:
            self._wait.clear()
            self._wait.wait(self._interval)
            if self.work and self._terminal_stuck() and self.work:
                self._actions_event()

    def _twatchdog_call(self, *_, **__):
        self._wait.set()

    def _terminal_stuck(self) -> bool:
        self._check_wait.clear()
        self.own.terminal_call('callme', self._check_wait.set, save_time=False)
        self._check_wait.wait(self.WAIT_INTERVAL)
        return not self._check_wait.is_set()

    def _actions_event(self):
        # log, notify, custom, {stop, reset}
        msg = 'Thread of terminal stuck: {}'.format(self._terminal_diagnostic_msg())
        if 'log' in self._actions:
            self.log(msg, logger.ERROR)
        if 'notify' in self._actions and self._send_notify:
            self._send_notify(msg)
        if self._custom_cmd:
            try:
                w_time = time.time()
                code = subprocess.call(self._custom_cmd, shell=True)
                w_time = time.time() - w_time
                self.log('Call \'{}\'. Code: {}, time: {}'.format(self._custom_cmd, code, pretty_time(w_time)))
            except OSError as e:
                self.log('Call \'{}\' failed: {}'.format(self._custom_cmd, e), logger.ERROR)
        if 'stop' in self._actions:
            self.own.die_in(5)
        elif 'reset' in self._actions:
            self.own.die_in(5, True)

    def _registration(self):
        self.own.subscribe(self.TWATCHDOG, self._twatchdog_call, self.NET_CHANNEL)
        if 'notify' in self._actions:
            self.own.add_notifications([self.TWATCHDOG], True)

    def _unregistration(self):
        self.own.unsubscribe(self.TWATCHDOG, self._twatchdog_call, self.NET_CHANNEL)
        if 'notify' in self._actions:
            self.own.remove_notifications([self.TWATCHDOG])

    def _load_cfg(self) -> tuple:
        default = {'interval': 30, 'actions': ['log', 'notify'], 'custom_cmd': ''}
        config = self.cfg.load_dict(TW_CONFIG)
        corrupted = False
        if isinstance(config, dict):
            for key in default.keys():
                if key not in config or not isinstance(config[key], type(default[key])):
                    corrupted = True
                    break
        elif config is not None:
            corrupted = True
        if corrupted:
            self.log('Configuration \'{}\' corrupted, set default: {}'.format(TW_CONFIG, default), logger.WARN)
        if corrupted or config is None:
            config = default
            self.cfg.save_dict(TW_CONFIG, config, True)
        custom_cmd = ''
        actions = [key for key in ('log', 'notify') if key in config['actions']]
        if config['custom_cmd'] and 'custom' in config['actions']:
            custom_cmd = config['custom_cmd']
            actions.append('custom')
        for key in ('stop', 'reset'):
            if key in config['actions']:
                actions.append(key)
                break
        interval = config['interval'] * 60 if config['interval'] > 0 else None
        return interval, tuple(actions), custom_cmd
