#ATS:lassen SELF lassenMachine 1

from ats.atsMachines.lsf_asq import lsfMachine # type: ignore[import]

class lassenMachine(lsfMachine):
    def calculateCommandList(self, test):
        if self.runningWithinBsub == True:
            return [ "jsrun", "-n", str(test.np), "-g", "1", *self.calculateBasicCommandList(test) ]
        else:
            print("ATS DISABLED ON LOGIN NODE. PLEASE RUN IN AN ALLOCATION.")
            exit(1)
