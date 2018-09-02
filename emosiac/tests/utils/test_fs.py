import os
import shutil

from emosiac.utils.fs import ensure_directory


def test_ensure_directory_multiple_levels():
  directory = '/tmp/multiple/dir/levels'
  assert not os.path.isdir('/tmp/multiple/')
  ensure_directory(directory)
  assert os.path.isdir(directory)
  shutil.rmtree('/tmp/multiple/')

