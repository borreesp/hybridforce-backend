from infrastructure.db.repositories import LookupRepository


class LookupService:
    def __init__(self, session):
        self.repo = LookupRepository(session)

    def all(self):
        return self.repo.all()
