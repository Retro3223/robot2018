from unittest.mock import MagicMock, patch
from data_logger import DataLogger

import pytest

from robot import Rockslide
from commands.profiled_forward import ProfiledForward

import hal
import hal_impl
from hal_impl.sim_hooks import SimHooks as BaseSimHooks


class SimHooks(BaseSimHooks):
    def __init__(self):
        super().__init__()
        self.time = 0.0

    def getTime(self):
        return self.time


@pytest.fixture(scope='function')
def sim_hooks():
    with patch('hal_impl.functions.hooks', new=SimHooks()) as hooks:
        hal_impl.functions.reset_hal()
        yield hooks


def test_ProfiledForward1(Notifier):
    robot = Rockslide()
    robot.robotInit()

    command = ProfiledForward(10)
    command.initialize()
    command.execute()
    command.isFinished()
    command.end()


log_trajectory = True


def test_ProfiledForward2(Notifier, sim_hooks):
    global log_trajectory
    robot = Rockslide()
    robot.robotInit()
    DT = robot.getPeriod()

    robot.drivetrain.getLeftEncoder = getLeftEncoder = MagicMock()
    robot.drivetrain.getRightEncoder = getRightEncoder = MagicMock()
    getLeftEncoder.return_value = 0
    getRightEncoder.return_value = 0
    command = ProfiledForward(10)
    command.initialize()

    t = 0
    pos_ft = 0
    import pdb

    if log_trajectory:
        logger = DataLogger("test_profiled_forward2.csv")
        logger.log_while_disabled = True
        logger.do_print = True
        logger.add('t', lambda: t)
        logger.add('pos', lambda: pos_ft)
        logger.add('target_pos', lambda: command.dist_ft)
        logger.add('v', lambda: command.profiler_l.current_target_v)
        logger.add('max_v', lambda: command.max_velocity)
        logger.add('a', lambda: command.profiler_l.current_a)
        logger.add('max_a', lambda: command.max_acceleration)
        logger.add('voltage', lambda: command.drivetrain.getVoltage())
        logger.add('vpl', lambda: command.drivetrain.motor_lb.get())
        logger.add('adist', lambda: command.profiler_l.adist)
        logger.add('err', lambda: command.profiler_l.err)
    pdb.set_trace()
    while t < 10:
        logger.log()
        getLeftEncoder.return_value = pos_ft * command.drivetrain.ratio
        getRightEncoder.return_value = -pos_ft * command.drivetrain.ratio

        command.execute()

        v = command.profiler_l.current_target_v
        pos_ft += v * DT
        t += DT
        sim_hooks.time = t

        if command.isFinished():
            break

    command.end()
    if log_trajectory:
        logger.log()
        logger.close()
