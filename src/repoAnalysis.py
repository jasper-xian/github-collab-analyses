import github
from fileAuthorScore import fileAuthorScore
from github import Github
import requests
import json
import cryptocode
import pickle

class GitAnalysis:
    def __init__(self):
        self.fileDict = {}
        self.g = None
        self.repoName = ""

    def clearCurrentFileName(self):
        self.currentFileName = ""

    def changeCurrentFileName(self, name):
        self.currentFileName = name

    def setRepoName(self, repoName):
        self.repoName = repoName

    def setG(self, token):
        self.g = Github(token)

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

    def clearFileDict(self):
        self.fileDict = {}
    
    def pickledFileDict(self):
        return pickle.dumps(self.fileDict)