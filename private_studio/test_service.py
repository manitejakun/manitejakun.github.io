import base64
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from uuid import uuid4

os.environ.setdefault("SESSION_SECRET","test-fixture")
from private_studio.app import app, ORIGIN

class PublishingTest(unittest.TestCase):
    def test_owner_publish_edit_retry(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ,STUDIO_DATABASE=str(Path(folder)/"drafts"),PUBLISH_KEY="fixture"):
            client=app.test_client()
            key=str(uuid4())
            headers={"Origin":ORIGIN}
            draft="/draft/"+key
            publish="/publish/"+key
            for route in (draft,"/cover/"+key,"/preview/"+key,"/published"):
                self.assertEqual(client.get(route).status_code,401)
            self.assertEqual(client.post(publish).status_code,401)
            with client.session_transaction() as session: session["owner"]="manitejakun"
            post=dict(title="A long title "*12,slug="sample",publication_date="2026-11-21",body="First")
            self.assertEqual(client.put(draft,json=post).status_code,403)
            self.assertEqual(client.put(draft,json=post,headers=headers).status_code,204)
            self.assertIn(b"First",client.get("/preview/"+key).data)
            files={}
            def github(url,data=None,token=None,method=None):
                if "/contents/" in url:
                    if not files: raise HTTPError(url,404,"",{},None)
                    return {"sha":files["sha"]}
                if "/git/ref/" in url: return {"object":{"sha":"head"}}
                if "/git/commits/" in url: return {"tree":{"sha":"tree"}}
                if url.endswith("/git/trees"):
                    raw=data["tree"][-1]["content"].encode()
                    files.update(body=json.loads(raw),sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest())
                return {"sha":"fixture"}
            with patch("private_studio.app.remote",side_effect=github):
                self.assertEqual(client.post(publish,headers=headers).status_code,200)
                self.assertEqual(client.post(publish,headers=headers).status_code,200)
                post=client.get(draft).json
                post["body"]="Second"
                client.put(draft,json=post,headers=headers)
                self.assertEqual(client.post(publish,headers=headers).status_code,200)
                self.assertEqual(files["body"]["body"],"Second")
