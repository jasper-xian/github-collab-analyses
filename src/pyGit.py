import github
from fileAuthorScore import fileAuthorScore
from github import Github
import requests
import json
import cryptocode
import pickle

#Will be replaced with vaulted password soon
cryptoKey = "replacablebluehyenaspwd"

class GitAnalysis:
    def __init__(self):
        self.fileDict = {}
        #self.tokens = []
        self.g = None
        #self.loggedIn = False
        self.repoName = ""
        self.currentFileName = ""
    
    def testToken(self, token):
        testG = Github(token)
        try:
            name = testG.get_user().name
        except:
            return False
        #self.loggedIn = True
        #self.tokens.append(token)
        return True

    def clearCurrentFileName(self):
        self.currentFileName = ""

    def changeCurrentFileName(self, name):
        self.currentFileName = name

    def setRepoName(self, repoName):
        self.repoName = repoName

    def setG(self, token):
        self.g = Github(token)

    def repoReachableToken(self, repoName, tokens):
        for token in tokens:
            try:
                testG = Github(token)
                repo = testG.get_repo(repoName)
            except:
                continue
            return token
        return None

    def authorsPerFileCommits(self):
        repo = self.g.get_repo(self.repoName)
        commits = repo.get_commits()
        count = 0
        for commit in commits:
            files = commit.files
            author = 0
            if commit.author is None:
                if commit.commit.author is None:
                    continue
                else:
                    author = "*" + commit.commit.author.name
            else:
                author = commit.author.login
            if commit.get_pulls().totalCount != 0:
                for file in files:
                    fileName = file.filename
                    if fileName in self.fileDict.keys():
                        if author in self.fileDict[fileName].keys():
                            self.fileDict[fileName][author].addAdditions(file.additions * 0.2)
                            self.fileDict[fileName][author].addDeletions(file.deletions * 0.2)
                            self.fileDict[fileName][author].addChanges(file.changes * 0.2)
                        else:
                            self.fileDict[fileName][author] = fileAuthorScore(file.additions * 0.2, file.deletions * 0.2, file.changes * 0.2)
                    else:
                        self.fileDict[fileName] = {}
                        self.fileDict[fileName][author] = fileAuthorScore(file.additions * 0.2, file.deletions * 0.2, file.changes * 0.2)
            else:
                for file in files:
                    fileName = file.filename
                    if fileName in self.fileDict.keys():
                        if author in self.fileDict[fileName].keys():
                            self.fileDict[fileName][author].addAdditions(file.additions)
                            self.fileDict[fileName][author].addDeletions(file.deletions)
                            self.fileDict[fileName][author].addChanges(file.changes)
                        else:
                            self.fileDict[fileName][author] = fileAuthorScore(file.additions, file.deletions, file.changes)
                    else:
                        self.fileDict[fileName] = {}
                        self.fileDict[fileName][author] = fileAuthorScore(file.additions, file.deletions, file.changes)
                    if file.status == "added" or file.status == "renamed":
                        self.fileDict[fileName][author].changeIsOriginalAuthor(True)
            #count = count + 1
            if count > 100:
                break

    def authorsPerFilePulls(self):
        repo = self.g.get_repo(self.repoName)
        pulls = repo.get_pulls("all")
        for pull in pulls:
            files = pull.get_files()
            user = 0
            if pull.user is None:
                continue
            else:
                user = pull.user.login
            for file in files:
                fileName = file.filename
                if fileName in self.fileDict.keys():
                    if user in self.fileDict[fileName].keys():
                        self.fileDict[fileName][user].addAdditions(file.additions * 0.6)
                        self.fileDict[fileName][user].addDeletions(file.deletions * 0.6)
                        self.fileDict[fileName][user].addChanges(file.changes * 0.6)
                    else:
                        self.fileDict[fileName][user] = fileAuthorScore(file.additions * 0.6, file.deletions * 0.6, file.changes * 0.6)
                else:
                    self.fileDict[fileName] = {}
                    self.fileDict[fileName][user] = fileAuthorScore(file.additions * 0.6, file.deletions * 0.6, file.changes * 0.6)
                if file.status == "added" or file.status == "renamed":
                        self.fileDict[fileName][user].changeIsOriginalAuthor(True)

    def isGitHubAuthor(self, login):
        contributors = self.g.get_repo(self.repoName).get_contributors()
        for contributor in contributors:
            if contributor.login == login:
                return True
        return False

    def printNewFileDict(self):
        for filename in self.fileDict.keys():
            for author in self.fileDict[filename].keys():
                print(filename, "-", author, "-", self.fileDict[filename][author].isOriginalAuthor, self.fileDict[filename][author].additions, self.fileDict[filename][author].deletions, self.fileDict[filename][author].changes, file=open("output4.txt", "a"))

    def getFileScore(self, filename, fileDict):
        if filename not in fileDict:
            print("File name not valid")
            return None
        authorDict = fileDict[filename]
        scores = []
        isOriginalOwner = False
        if len(authorDict) == 1:
            for author in authorDict:
                scores.append((author, 100))
            return scores
        totalChanges = 0
        totalScore = 0
        for author in authorDict.keys():
            totalChanges = totalChanges + authorDict[author].changes
        if totalChanges == 0:
            for author in authorDict.keys():
                score = 0
                if authorDict[author].isOriginalAuthor == True:
                    score = 30
                    isOriginalOwner = True
                score += 100 / len(authorDict)
                if isOriginalOwner is True:
                    score = round(score / 130 * 100, 3)
                scores.append([author, score])
                totalScore += score
        else: 
            for author in authorDict.keys():
                score = 0
                if authorDict[author].isOriginalAuthor == True:
                    score = 30
                    isOriginalOwner = True
                score += authorDict[author].changes / (totalChanges) * 100
                if isOriginalOwner is True:
                    score = round(score / 130 * 100, 3)
                scores.append([author, score])
                totalScore += score
        if totalScore > 100.01 or totalScore < 99.99:
            for item in scores:
                item[1] = item[1] / totalScore * 100
        return scores

    def isRepo(self, testRepoName):
        try:
            repo = self.g.get_repo(testRepoName)
        except:
            return False
        return True

    def isValidFile(self, filename, fileDict):
        if filename in fileDict:
            return True
        return False
    
    def saveFileDict(self):
        with open("savedFileDict.txt", "wb") as myFile:
            pickle.dump(self.fileDict, myFile)
    
    def loadFileDict(self):
        with open("savedFileDict.txt", "rb") as myFile:
            self.fileDict = pickle.load(myFile)

    def clearFileDict(self):
        self.fileDict = {}
    
    def pickledFileDict(self):
        return pickle.dumps(self.fileDict)

    def pickleFileDict(self, fileDict):
        return pickle.dumps(fileDict)

    def unpickleFileDict(self, pickledFileDict):
        return pickle.loads(pickledFileDict)

    def encrypt(self, encrpytString):
        return cryptocode.encrypt(encrpytString, cryptoKey)
    
    def decrypt(self, decrpytString):
        return cryptocode.decrypt(decrpytString, cryptoKey)