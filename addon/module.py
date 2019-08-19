module_pip = False
module_opencv = False

def checkModules():

    try:
        import pip
        module_pip = True
    except ImportError:
        module_pip = False

    try:
        import cv2
        module_opencv = True
    except ImportError:
        module_opencv = False

    if all([module_pip, module_opencv]):
        return True
    else:
        return False