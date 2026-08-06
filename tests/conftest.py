import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.test_server import start_server


@pytest.fixture(scope="session")
def server_url():
    url, srv = start_server()
    yield url
    srv.shutdown()


@pytest.fixture(scope="session")
def wordlist_path(tmp_path_factory):
    wl = tmp_path_factory.mktemp("data") / "wordlist.txt"
    wl.write_text("# test wordlist\nadmin/\nblog\ndoes-not-exist\n.env\nphpinfo.php\nsettings\nabout\ncontact\n", encoding='utf-8')
    return str(wl)
