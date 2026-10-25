#!/usr/bin/env python3
"""Offline smoke checks: no real credentials, model, database or HTTP services."""
import ast
import importlib.util
import json
from pathlib import Path
import time
import tomllib
import unittest

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


class ReleaseChecks(unittest.TestCase):
    def test_sources_and_lock(self):
        for path in [*ROOT.glob("*.py"), *(ROOT / "backend").rglob("*.py")]:
            ast.parse(path.read_text(), filename=str(path))
        for path in (ROOT / "backend/data").glob("*.json"):
            json.loads(path.read_text())
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
        lock = tomllib.loads((ROOT / "uv.lock").read_text())
        locked = next(p for p in lock["package"] if p["name"] == project["name"])
        self.assertEqual(project["version"], locked["version"])

    def test_service_auth_contract(self):
        # Load only auth: importing the complete application would read local .env.
        spec = importlib.util.spec_from_file_location(
            "release_security", ROOT / "backend/app/security/security.py")
        security = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(security)
        from fastapi import Depends

        app = FastAPI()
        secret = "a" * 64  # synthetic, solely in-memory test fixture
        app.state.service_auth_secret = secret

        @app.post("/chat", dependencies=[Depends(security.require_service_auth)])
        def chat():
            return {"ok": True}

        now = int(time.time())
        claims = dict(iss="aica-shopware", aud="aica-backend", sub="shopware-proxy",
                      token_use="service", iat=now, exp=now + 60)
        with TestClient(app) as client:
            self.assertEqual(client.post("/chat").status_code, 401)

            def request(payload, signing_secret=secret):
                token = jwt.encode(payload, signing_secret, algorithm="HS256")
                return client.post("/chat", headers={"Authorization": "Bearer " + token})

            self.assertEqual(request(claims).status_code, 200)
            self.assertEqual(request(claims, "b" * 64).status_code, 401)
            for update in [dict(aud="wrong"), dict(sub="browser"),
                           dict(token_use="context"), dict(iat=now-120, exp=now-60),
                           dict(exp=now+61), dict(iat=str(now))]:
                self.assertEqual(request(claims | update).status_code, 401)
            for name in claims:
                self.assertEqual(request({k: v for k, v in claims.items() if k != name}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
