from sqlalchemy import insert, func
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker


def db_executor(func):
    """create and close sqlalchemy session for class methods which execute sql statement"""
    def inner(*args, **kwargs):
        self_ = args[0]
        session = self_.Session()
        try:
            func(*args, **kwargs)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            self_.Session.remove()
    return inner


def db_selector(func):
    """create and close sqlalchemy session for class methods which return query result"""
    def inner(*args, **kwargs):
        self_ = args[0]
        session = self_.Session()
        try:
            func_res = func(*args, **kwargs)
        except:
            session.rollback()
            raise
        finally:
            self_.Session.remove()
            return func_res
    return inner


class TableProcessor:

    def __init__(self, engine):
        session_factory = sessionmaker(bind=engine)
        self.Session = scoped_session(session_factory)

    @db_selector
    def get_query_result(self, query: "sqlalchemy.orm.query.Query") -> list["table_model"]:
        session = self.Session()
        result = session.execute(query).scalars().all()
        return result

    @db_executor
    def _insert_values(self, table_model: "sqlalchemy.orm.decl_api.DeclarativeMeta", data: dict):
        ins_command = insert(table_model).values(**data)
        session = self.Session()
        session.execute(ins_command)

    @db_selector
    def _get_all_data(self, table_model: "sqlalchemy.orm.decl_api.DeclarativeMeta") -> list['table_model']:
        session = self.Session()
        query = session.query(table_model)
        result = self.get_query_result(query)
        return result

    @db_selector
    def _get_filtered_data(self, table_model, filter_values: dict) -> list['table_model']:
        session = self.Session()
        query = session.query(table_model)
        for filter_column in filter_values:
            query = query.filter(getattr(table_model, filter_column) == filter_values[filter_column])
        result = self.get_query_result(query)
        return result

    @db_executor
    def _change_column_value(self, table_model, filter_values: dict, change_values: dict) -> None:
        session = self.Session()
        query = session.query(table_model)
        for filter_column in filter_values:
            query = query.filter(getattr(table_model, filter_column) == filter_values[filter_column])
        query.update(change_values)

    @db_selector
    def _get_max_value_of_column(self, table_model, column: str):

        query = func.max(getattr(table_model, column))
        result = self.get_query_result(query)[0]

        # case with empty table
        if not result:
            result = 0

        return result
