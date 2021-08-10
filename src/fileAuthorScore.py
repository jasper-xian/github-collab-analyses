class fileAuthorScore:
    def __init__(self):
        self.additions = 0
        self.deletions = 0
        self.changes = 0
        self.isOriginalAuthor = False
        self.comments = 0

    def __init__(self, additions, deletions, changes):
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.isOriginalAuthor = False
        self.comments = 0

    """ def __init__(self, isOriginalAuthor, additions, deletions, changes):
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.isOriginalAuthor = isOriginalAuthor
        self.comments = 0

    def __init__(self, isOriginalAuthor, additions, deletions, changes, comments):
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.isOriginalAuthor = isOriginalAuthor
        self.comments = comments """
    
    def addAdditions(self, num):
        self.additions += num

    def addDeletions(self, num):
        self.deletions += num

    def addChanges(self, num):
        self.changes += num

    def changeIsOriginalAuthor(self, flag):
        self.isOriginalAuthor = flag