#ATS:lassen SELF lassenMachine 1

from ats.atsMachines.lsf_asq import lsfMachine # type: ignore[import]

class lassenMachine(lsfMachine):
    def calculateCommandList(self, test):
        return [ "jsrun", "-n", str(test.np), "--pack", "-g", "1", *self.calculateBasicCommandList(test) ]
