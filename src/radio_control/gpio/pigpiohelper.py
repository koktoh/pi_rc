import pigpio

__instance: pigpio.pi = None


def get_instance() -> pigpio.pi:
    """
    Get singlton pigpio.pi instance.
    """
    global __instance

    if __instance is None:
        __instance = pigpio.pi()

    return __instance
