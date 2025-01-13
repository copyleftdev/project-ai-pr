#------------------------------------------------------------------------------
#  symbCtrlModbus.py
#
#  A dummy module to emulate a Modbus-based controller for demo purposes.
#  Replace with your real symbCtrlModbus implementation for production.
#
#  Symbrosia
#  Copyright 2024, all rights reserved
#
#------------------------------------------------------------------------------
import random

class SymbCtrl:
    def __init__(self):
        self._error = False
        self._connected = False

    def start(self, address, port):
        """
        Pretend to open a Modbus connection to the given address/port.
        Return True if "connected," False otherwise.
        """
        # Here we just fake a successful connection:
        self._connected = True
        return self._connected

    def service(self):
        """
        Called after a connection is opened. 
        Could be used to poll the device or do other housekeeping.
        """
        # Set self._error if something goes wrong.
        # For now, we pretend there is no error:
        self._error = False

    def error(self):
        """
        Return True if the controller has encountered a communications error.
        """
        return self._error

    def value(self, reg_name):
        """
        Return some dummy data based on the register name.
        The real code would read from a device here.
        """
        # We'll just return something random or typical:
        if "temp" in reg_name.lower():
            return 23.45
        elif "bool" in reg_name.lower():
            # Return True/False randomly
            return random.choice([True, False])
        else:
            # Some integer
            return random.randint(0, 100)

    def convert(self, reg_name, ref_value_str):
        """
        Convert the string from reference file to the same type you'd get from self.value().
        We use self.type() to guess the type from the reg_name, then parse.
        """
        t = self.type(reg_name)
        try:
            if t == "float":
                return float(ref_value_str)
            elif t == "int" or t == "uint":
                return int(ref_value_str)
            elif t == "bool":
                # Interpret typical boolean strings (on/off, 1/0, true/false).
                lv = ref_value_str.strip().lower()
                return lv in ["1", "true", "on"]
            else:
                # Default to string
                return ref_value_str
        except:
            # If something goes wrong, fallback
            return ref_value_str

    def description(self, reg_name):
        """
        Return a short description of the register.
        In real usage, you'd look up register info in a table.
        """
        return f"Description for {reg_name}"

    def type(self, reg_name):
        """
        Return a guess at the register type.
        In real usage, you'd have a config or table that determines the type.
        """
        # We'll do something naive:
        reg_name_lower = reg_name.lower()
        if "temp" in reg_name_lower:
            return "float"
        if "switch" in reg_name_lower or "bool" in reg_name_lower:
            return "bool"
        if "str" in reg_name_lower:
            return "str"
        # By default, let's assume int/uint
        return "int"
