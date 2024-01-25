#ATS:lassen SELF lassenMachine 1

# import os
from ats.atsMachines.lsf_asq import lsfMachine # type: ignore[import]

class lassenMachine(lsfMachine):
    # def __init__(self):
    #     super(lassenMachine,self).__init__(self)

    #     LSB_MAX_NUM_PROCESSORS = int(os.getenv("LSB_MAX_NUM_PROCESSORS",40))
    #     physical_cores_per_node = 40
    #     gpus_per_node = 4

    #     self.num_nodes = int(LSB_MAX_NUM_PROCESSORS / physical_cores_per_node)
    #     self.total_alloc_procs = self.num_nodes * physical_cores_per_node
    #     self.total_alloc_gpus = self.num_nodes * gpus_per_node

    #     self.procs_avail = self.total_alloc_procs
    #     self.gpu_avali = self.num_nodes * gpus_per_node

    def calculateCommandList(self, test):
        if self.runningWithinBsub == True:
            return [ "jsrun", "-n", str(test.np), "-a", str(test.nt), "-g", "1", *self.calculateBasicCommandList(test) ]
        else:
            print("ATS DISABLED ON LOGIN NODE. PLEASE RUN IN AN ALLOCATION.")
            exit(1)

    # def canRun(self,test):
    #     if self.total_alloc_procs < test.np * getattr(test,"nt",1) or self.total_alloc_gpus < getattr(test,"ngpu",0):
    #         return f"Test {test.name} requires {test.np * getattr(test,'nt',1)} procs ({self.total_alloc_procs} available) and {getattr(test,'ngpu',0)} gpus ({self.total_alloc_gpus} available)!"
    #     return ''

    # def canRunNow(self, test):
    #     if self.procs_avail > test.np * getattr(test,"nt") and self.gpu_avail > getattr(test,"ngpu",0):
    #         return True
    #     return False

    # def noteLaunch(self, test):
    #     self.procs_avail -= test.np * getattr(test,"nt",1)
    #     self.gpu_avail -= test.ngpu
    #     print( f"Start: {test.serialNumber}, {test.name}, nn={test.num_nodes}, np={test.np}, nt={getattr(test,'nt',1)}, ngpu={test.ngpu}" )

    # def noteEnd(self, test):
    #     self.procs_avail += test.np * getattr(test,"nt",1)
    #     self.gpu_avail += test.ngpu
    #     print( f"Stop: {test.serialNumber}, {test.name}, nn={test.num_nodes}, np={test.np}, nt={getattr(test,'nt',1)}, ngpu={test.ngpu}" )

    # def remainingCapacity(self):
    #     return self.procs_avail