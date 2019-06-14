from os_aio_pod.bean import Bean
from os_aio_pod.utils import load_class


def test_load_class():

    assert Bean == load_class("os_aio_pod.bean.Bean", Bean, True)
    assert load_class("os_aio_pod.bean.Bean", Bean) is None
