"""Neo4j driver wrapper with connection pooling and context manager support."""

import logging
from contextlib import contextmanager
from neo4j import GraphDatabase, Driver, Session

log = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self._uri = uri
        self._database = database
        self._driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
        log.info(f"Neo4j client connected to {uri}")

    @contextmanager
    def session(self) -> Session:
        with self._driver.session(database=self._database) as s:
            yield s

    def run_query(self, cypher: str, **params) -> list[dict]:
        with self.session() as s:
            result = s.run(cypher, **params)
            return [dict(r) for r in result]

    def close(self):
        self._driver.close()

    def verify_connectivity(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except Exception as e:
            log.error(f"Neo4j connectivity check failed: {e}")
            return False
