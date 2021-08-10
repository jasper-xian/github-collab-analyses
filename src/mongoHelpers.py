import github
from fileAuthorScore import fileAuthorScore
from github import Github
import cryptocode
import pickle
from flask_pymongo import PyMongo

#Will be replaced with vaulted password soon
cryptoKey = "replacablebluehyenaspwd"

def pickleFileDict(fileDict):
    return pickle.dumps(fileDict)

def unpickleFileDict(pickledFileDict):
    return pickle.loads(pickledFileDict)

def encrypt(encrpytString):
    return cryptocode.encrypt(encrpytString, cryptoKey)
    
def decrypt(decrpytString):
    return cryptocode.decrypt(decrpytString, cryptoKey)

def decryptTokenList(list):
    newList = []
    for item in list:
        newItem = decrypt(item["token"], cryptoKey)
        newList.append(newItem)
    return newList