from typing import Any, Type

from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, session: Session, model: Type[Any]):
        self.session = session
        self.model = model

    def get(self, obj_id: Any):
        return self.session.get(self.model, obj_id)

    def list(self):
        return self.session.query(self.model).all()

    def create(self, **kwargs):
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, instance):
        self.session.delete(instance)
        self.session.commit()
        return instance
