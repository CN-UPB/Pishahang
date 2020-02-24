from ..models import Descriptor

def getDescriptors(type):
    # d = Descriptor(type=type, descriptor={'test': True})
    # d.save()
    return Descriptor.objects(type=type)

def addDescriptor():
    pass