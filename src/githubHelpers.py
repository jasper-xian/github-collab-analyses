import github
from fileAuthorScore import fileAuthorScore
from github import Github
from mongoHelpers import *

def testToken(token):
    testG = Github(token)
    try:
        name = testG.get_user().name
    except:
        return False
    return True

def repoReachableToken(repoName, tokens):
    for item in tokens:
        token = decrypt(item["token"])
        try:
            testG = Github(token)
            repo = testG.get_repo(repoName)
        except:
            continue
        return token
    return None

def getFileScore(filename, fileDict):
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

def isValidFile(filename, fileDict):
    if filename in fileDict:
        return True
    return False
