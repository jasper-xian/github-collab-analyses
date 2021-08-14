from io import BytesIO, StringIO
from flask import Flask, render_template, url_for, request, session, redirect, Blueprint
from functools import wraps
from flask.helpers import send_file
from flask_pymongo import PyMongo
import bcrypt
import matplotlib.pyplot as plt
from repoAnalysis import GitAnalysis
from mongoHelpers import *
from githubHelpers import *
from graphs import *
from celery import Celery

app = Flask(__name__)
myGitAnalysis = GitAnalysis()

app.config["MONGO_DBNAME"] = "mydb"
app.config["MONGO_URI"] = "mongodb+srv://read-write:github-collab-analysis@cluster0.2g2n0.mongodb.net/mydb?retryWrites=true&w=majority"
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

mongo = PyMongo(app)
celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
#celery.conf.update(app.config)

#Will be replaced with vaulted password soon
cryptoKey = "replacablebluehyenaspwd"

#Decorators
def loginRequired(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'username' in session:
      return f(*args, **kwargs)
    else:
      return redirect('/')
  return wrap

#Redirects logged in users to home
def loggedInRedirect(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'username' not in session:
      return f(*args, **kwargs)
    else:
      return redirect(url_for('home', username=session['username']))
  return wrap

@app.route('/')
#@loggedInRedirect
def index():
  if 'username' in session:
    return redirect(url_for('home', username=session['username']))
  return render_template('index.html')

@app.route('/login', methods=['GET'])
#@loggedInRedirect
def login():
  if 'username' in session:
    return redirect(url_for('home', username=session['username']))
  return render_template('login.html')

@app.route('/logout')
@loginRequired
def logout():
  session.clear()
  return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
#@loggedInRedirect
def loginPOST():
  users = mongo.db.users
  login_user = users.find_one({"username" : request.form['username']})
  if login_user:
      if bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password']):
          session['username'] = request.form['username']
          return redirect(url_for('home', username=session['username']))
      else:
        return render_template('failedLogin.html')
  else:
      return render_template('failedLogin.html')

@app.route('/register', methods=['GET'])
#@loggedInRedirect
def register():
  if 'username' in session:
    return redirect(url_for('home', username=session['username']))
  return render_template('register.html')

@app.route('/register', methods=['POST'])
#@loggedInRedirect
def registerPOST():
    users = mongo.db.users
    existing_user = users.find_one({"username" : request.form['username']})
    if existing_user is None or "/" in request.form['username']:
        hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        token = request.form['token']
        flag = testToken(token=token)
        if flag is False:
            return render_template('failedRegisterToken.html')
        #hashtokens = [bcrypt.hashpw(request.form['token'].encode('utf-8'), bcrypt.gensalt())] 
        hashtokens = [{"name": request.form['tokenName'], "token": encrypt(token)}]
        users.insert_one({"username" : request.form['username'], "password" : hashpass, "tokens": hashtokens, "fileDicts": []})
        session['username'] = request.form['username']
        return redirect(url_for('home', username=session['username']))
    return render_template('failedRegisterUser.html')

@app.route('/<username>')
@loginRequired
def home(username):
  return render_template('home.html', username=username)

@celery.task
def addRepo(repoName, token):
  users = mongo.db.users
  myGitAnalysis.setG(token=token)
  myGitAnalysis.clearFileDict()
  myGitAnalysis.setRepoName(repoName)
  myGitAnalysis.authorsPerFileCommits()
  myGitAnalysis.authorsPerFilePulls()
  data = {"repoName": repoName, "pickledFileDict": myGitAnalysis.pickledFileDict()}
  users.update_one({"username": session['username']}, {"$push": {"fileDicts": data}})

@app.route('/<username>/repositories')
@loginRequired
def changeRepos(username):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  userFileDicts = currUser["fileDicts"]
  repoNames = []
  for item in userFileDicts:
    repoNames.append(item["repoName"])
  return render_template('changeRepos.html', username=username, repoNames=repoNames)

@app.route('/<username>/repositories', methods=['POST'])
@loginRequired
def changeReposPOST(username):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  userTokens = currUser["tokens"]
  userFileDicts = currUser["fileDicts"]
  repoNames = []
  for item in userFileDicts:
    repoNames.append(item["repoName"])
  if 'add' in request.form:
    repoName = request.form['reponame']
    token = repoReachableToken(repoName=repoName, tokens=userTokens)
    if token is None or repoName in repoNames:
      return render_template('failedChangeRepo.html', username=username, repoNames=repoNames)
    else:
      addRepo.apply_async(args=[repoName, token])
      return render_template('addingRepo.html', username=username, repoNames=repoNames)
  elif 'update' in request.form:
    repoName = request.form['updateRepo']
    token = repoReachableToken(repoName=repoName, tokens=userTokens)
    myGitAnalysis.setG(token=token)
    myGitAnalysis.clearFileDict()
    myGitAnalysis.setRepoName(repoName=repoName)
    myGitAnalysis.authorsPerFileCommits()
    myGitAnalysis.authorsPerFilePulls()
    data = {"repoName": repoName, "pickledFileDict": myGitAnalysis.pickledFileDict()}
    users.update_one({"username": session['username']}, {"$pull": {"fileDicts": {"repoName": repoName}}})
    users.update_one({"username": session['username']}, {"$push": {"fileDicts": data}})
    return redirect(url_for('home', username=username))
  else:
    repoName = request.form['removeRepo']
    users.update_one({"username": session['username']}, {"$pull": {"fileDicts": {"repoName": repoName}}})
    return redirect(url_for('home', username=username))


@app.route('/<username>/tokens')
@loginRequired
def changeTokens(username):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  tokenNames = []
  for item in currUser["tokens"]:
    tokenNames.append(item["name"])
  return render_template('changeTokens.html', username=username, tokenNames=tokenNames)

@app.route('/<username>/tokens', methods=['POST'])
@loginRequired
def changeTokensPOST(username):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  tokenNames = []
  for item in currUser["tokens"]:
    tokenNames.append(item["name"])
  if 'add' in request.form:
    tokenName = request.form['tokenName']
    token = request.form['tokenValue']
    flag = testToken(token=token)
    if flag is False or tokenName in tokenNames:
      return render_template('failedChangeTokens.html', username=username, tokenNames=tokenNames)
    data = {"name": tokenName, "token": encrypt(token)}
    users.update_one({"username": session['username']}, {"$push": {"tokens": data}})
    return redirect(url_for('home', username=username))
  else:
    tokenName = request.form['removeToken']
    users.update_one({"username": session['username']}, {"$pull": {"tokens": {"name": tokenName}}})
    return redirect(url_for('home', username=username))

@app.route('/<username>/search')
@loginRequired
def selectRepo(username):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  userFileDicts = currUser["fileDicts"]
  repoNames = []
  for item in userFileDicts:
    repoNames.append(item["repoName"])
  return render_template('selectRepo.html', username=username, repoNames=repoNames)

@app.route('/<username>/search', methods=['POST'])
@loginRequired
def selectRepoPOST(username):
  repoName = request.form['repoList']
  tempList = repoName.split("/")
  return redirect(url_for('fileSearch', username=username, login=tempList[0], repoOnly=tempList[1]))

@app.route('/<username>/search/<login>/<repoOnly>')
@loginRequired
def fileSearch(username, login, repoOnly):
  repoName = login + "/" + repoOnly
  return render_template('fileSearch.html', username=username, repoName=repoName)

@app.route('/<username>/search/<login>/<repoOnly>', methods=['POST'])
@loginRequired
def fileSearchPOST(username, login, repoOnly):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  userFileDicts = currUser["fileDicts"]
  repoName = login + "/" + repoOnly
  fileDict = pickledFileDict = 0
  for item in userFileDicts:
    if item["repoName"] == repoName:
      pickledFileDict = item["pickledFileDict"]
      fileDict = unpickleFileDict(pickledFileDict=pickledFileDict)
  if fileDict == 0:
    return "Bad Repository Name"
  filename = request.form['filename']
  #isValidFile = isValidFile(filename=filename, fileDict=fileDict)
  flag = isValidFile(filename=filename, fileDict=fileDict)
  if filename == "":
    return redirect(url_for('fullFileList', username=username, login=login, repoOnly=repoOnly))
  elif not flag:
    return render_template('failedFileSearch.html', username=username, repoName=repoName)
  else:
    session['currentFileName'] = filename
    dashedFileName = filename.replace("/", "-")
    return redirect(url_for('fileScore', username=username, login=login, repoOnly=repoOnly, dashedFileName=dashedFileName))

@app.route('/<username>/search/<login>/<repoOnly>/all-files')
@loginRequired
def fullFileList(username, login, repoOnly):
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  userFileDicts = currUser["fileDicts"]
  repoName = login + "/" + repoOnly
  fileDict = pickledFileDict = 0
  for item in userFileDicts:
    if item["repoName"] == repoName:
      pickledFileDict = item["pickledFileDict"]
      fileDict = unpickleFileDict(pickledFileDict=pickledFileDict)
  if fileDict == 0:
    return "Bad Repository Name"
  
  finalScoreList = []
  for filename in fileDict:
    scores = getFileScore(filename=filename, fileDict=fileDict)
    result = filename + " --> "
    for item in scores:
      result = result + "[" + item[0] + ": " + str(item[1]) + "] "
    finalScoreList.append(result)
  return render_template('fullRepoScores.html', username=username, finalScoreList=finalScoreList, login=login, repoOnly=repoOnly)

@app.route('/<username>/search/<login>/<repoOnly>/<dashedFileName>')
@loginRequired
def fileScore(username, login, repoOnly, dashedFileName):
  filename = session['currentFileName']
  #session.pop('currentFileName', None)
  # result = filename + " --> "
  # for item in scores:
  #   result = result + "[" + item[0] + ": " + str(item[1]) + "] "
  return render_template('singleFileScore.html', filename=filename, username=username, login=login, repoOnly=repoOnly)

@app.route('/<username>/search/<login>/<repoOnly>/display-figure')
def singleFileScoreChart(username, login, repoOnly):
  filename = session['currentFileName']
  session.pop('currentFileName', None)
  users = mongo.db.users
  currUser = users.find_one({"username": session['username']})
  userFileDicts = currUser["fileDicts"]
  repoName = login + "/" + repoOnly
  fileDict = pickledFileDict = 0
  for item in userFileDicts:
    if item["repoName"] == repoName:
      pickledFileDict = item["pickledFileDict"]
      fileDict = unpickleFileDict(pickledFileDict=pickledFileDict)
  if fileDict == 0:
    return "Bad Repository Name"
  
  scores = getFileScore(filename=filename, fileDict=fileDict)
  img = generateDonutPieChart(scores=scores)
  return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)