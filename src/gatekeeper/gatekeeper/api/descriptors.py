from ..models import Descriptor

# returns a list of all uploaded descriptors


def getDescriptors():
    return Descriptor.objects(location="Uploaded")


def getDescriptorsWithType(type):
    return Descriptor.objects(type=type, location="Uploaded")


def getDescriptorWithUUID(uuid):
    return Descriptor.objects(uuid=uuid, location="Uploaded")

# adds a descriptor to the database


def addDescriptor(type):
    d = Descriptor(type=type, descriptor={
                   'test': True}, location="Uploaded")
    d.save()
    return Descriptor.objects()


def addDescriptorInQuery(type, descriptor):
    print("type")


def addDescriptorWithType(descriptor):
    print(descriptor)
    # desc = Descriptor(type=type, descriptor=descriptor)
    # desc.save()
    # return Descriptor.objects()

# deletes a descriptor from the database given a UUID


def deleteDescriptorWithUUID(uuid):
    return Descriptor.objects(uuid=uuid).delete()


##ONBOARDED DESCRIPTORS##

# returns a list of all onboarded descriptors


def getOnboardedDescriptors():
    return Descriptor.objects(location="Onboarded")
    # returns a list of onboarded descriptors defined by type


def getOnboardedTypeDescriptors(type):
    return Descriptor.objects(type=type, location="Onboarded")
    # returns a specific descriptor with a matching UUID


def getOnboardedDescriptorWithUUID(uuid):
    return Descriptor.objects(uuid=uuid, location="Onboarded")
    # adds an onboarded descriptor to the database


def addOnboardedDescriptor(type):
    d = Descriptor(type=type, descriptor={
                   'test': True}, location="Onboarded")
    d.save()
    return Descriptor.objects()
    # deletes a decriptor given a UUID


def deleteOnboardedDescriptor(uuid):
    value = Descriptor.objects(uuid=uuid, location="Onboarded").delete()
    if value == 1:
        return "Deleted"
    else:
        return "Not Found"


##INSTANTIATED DESCRIPTORS##

# returns a list of all onboarded descriptors


def getInstantiatedDescriptors():
    return Descriptor.objects(location="Instantiated")
    # returns a list of Instantiated descriptors defined by type


def getInstantiatedDescriptorsWithType(type):
    return Descriptor.objects(type=type, location="Instantiated")
    # returns a specific descriptor with a matching UUID


def getInstantiatedDescriptorsWithUUID(uuid):
    return Descriptor.objects(uuid=uuid, location="Instantiated")
    # adds an Instantiated descriptor to the database


def addInstantiatedDescriptor(type):
    d = Descriptor(type=type, descriptor={
                   'test': True}, location="Instantiated")
    d.save()
    return Descriptor.objects()
    # deletes a decriptor given a UUID


def deleteInstantiatedDescriptor(uuid):
    value = Descriptor.objects(uuid=uuid, location="Instantiated").delete()
    if value == 1:
        return "Deleted"
    else:
        return "Not Found"
