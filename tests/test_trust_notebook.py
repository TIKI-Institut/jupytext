import os
import mock
import shutil
import pytest
from jupytext.contentsmanager import TextFileContentsManager
from .utils import list_notebooks


@pytest.mark.parametrize('nb_file', list_notebooks('python'))
def test_py_notebooks_are_trusted(nb_file):
    cm = TextFileContentsManager()
    root, file = os.path.split(nb_file)
    cm.root_dir = root
    nb = cm.get(file)
    for cell in nb['content'].cells:
        assert cell.metadata.get('trusted', True)


@pytest.mark.parametrize('nb_file', list_notebooks('Rmd'))
def test_rmd_notebooks_are_trusted(nb_file):
    cm = TextFileContentsManager()
    root, file = os.path.split(nb_file)
    cm.root_dir = root
    nb = cm.get(file)
    for cell in nb['content'].cells:
        assert cell.metadata.get('trusted', True)


@pytest.mark.parametrize('nb_file', list_notebooks('ipynb_py', skip='hash sign'))
def test_ipynb_notebooks_can_be_trusted(nb_file, tmpdir):
    with mock.patch('jupytext.header.INSERT_AND_CHECK_VERSION_NUMBER', False):
        cm = TextFileContentsManager()
        root, file = os.path.split(nb_file)
        tmp_ipynb = str(tmpdir.join(file))
        py_file = file.replace('.ipynb', '.py')
        tmp_py = str(tmpdir.join(py_file))
        shutil.copy(nb_file, tmp_ipynb)

        cm.default_jupytext_formats = 'ipynb,py'
        cm.root_dir = str(tmpdir)
        model = cm.get(file)
        cm.save(model, py_file)

        # Unsign and test notebook
        nb = model['content']
        for cell in nb.cells:
            if 'trusted' in cell.metadata:
                cell.metadata.pop('trusted')

        cm.notary.unsign(nb)

        model = cm.get(file)
        for cell in model['content'].cells:
            assert 'trusted' not in cell.metadata or not cell.metadata['trusted'] or not cell.outputs

        # Trust and reload
        cm.trust_notebook(py_file)

        model = cm.get(file)
        for cell in model['content'].cells:
            assert cell.metadata.get('trusted', True)

        # Remove py file, content should be the same
        os.remove(tmp_py)
        nb2 = cm.get(file)
        for cell in nb2['content'].cells:
            assert cell.metadata.get('trusted', True)

        assert model['content'] == nb2['content']

        # Just for coverage
        cm.trust_notebook(file)


@pytest.mark.parametrize('nb_file', list_notebooks('ipynb_py', skip='hash sign'))
def test_ipynb_notebooks_can_be_trusted_even_with_metadata_filter(nb_file, tmpdir):
    with mock.patch('jupytext.header.INSERT_AND_CHECK_VERSION_NUMBER', False):
        cm = TextFileContentsManager()
        root, file = os.path.split(nb_file)
        tmp_ipynb = str(tmpdir.join(file))
        py_file = file.replace('.ipynb', '.py')
        tmp_py = str(tmpdir.join(py_file))
        shutil.copy(nb_file, tmp_ipynb)

        cm.default_jupytext_formats = 'ipynb,py'
        cm.default_notebook_metadata_filter = 'all'
        cm.default_cell_metadata_filter = '-all'
        cm.root_dir = str(tmpdir)
        model = cm.get(file)
        cm.save(model, py_file)

        # Unsign notebook
        nb = model['content']
        for cell in nb.cells:
            if 'trusted' in cell.metadata:
                cell.metadata.pop('trusted')

        cm.notary.unsign(nb)

        # Trust and reload
        cm.trust_notebook(py_file)

        model = cm.get(file)
        for cell in model['content'].cells:
            assert cell.metadata.get('trusted', True)

        # Remove py file, content should be the same
        os.remove(tmp_py)
        nb2 = cm.get(file)
        for cell in nb2['content'].cells:
            assert cell.metadata.get('trusted', True)

        assert model['content'] == nb2['content']
