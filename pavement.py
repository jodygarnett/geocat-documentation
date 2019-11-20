import os
from paver.easy import *
import shutil

'''
This script generates the documentation site for geocat products.

the 'all' task should be run from the command line, by running:

$ paver all

Documentation for each product is supposed to be stored in its individual repo,
and it should contain a paver task named 'builddocs', which should generate
html results in a 'build/html' folder

Documentation repos can have submodules (for instance, for a sphinx theme stored in 
its own repo). Those submodules will be updated before building the corresponding
documentation html files

The output documentation is stored in the 'docs' folder under the root of this repo.

Versions of the documentation are created using tags in the documentation repo.

For instance, for a product named 'geoserver' with tags 'v1.0' and 'v2.0', 
this script will generate the following tree structure.

|--docs
   |--geoserver
      |--v1.0
         |--index.html         
         .
         .
         .
      |--v2.0
         |--index.html         
         .
         .
         .
      |--latest
         |--index.html         
         .
         .
         .

The 'latest' folder is always added and contains the most recent version of the
documentation for a given product (taken from the current master HEAD)

The task will also deploy the data, by adding a new commit to this repository
with the updated 'docs' folder. That folder is published using GitHub pages.
'''

# The list of products, with the repository name where documentation for each 
# one is found 
products = {"bridge": "bridge-documentation",
        "geoserver": "geoserver-documentation",
        "geonetwork": "geonetwork-documentation"}

@task
@cmdopts([    
    ('githttps', 'g', 'connect to github using HTTPS instead of SSH')
])
def all(options):
    fetch(options)
    builddocs(options)
    deploy(options)

@task
@cmdopts([
    ('githttps', 'g', 'connect to github using HTTPS instead of SSH')
])
def fetch(options):
    '''clone all doc repos or update if already cloned'''
    cwd = os.getcwd()
    tmpDir = os.path.join(cwd, 'tmp')
    gitscheme = 'git@github.com:'
    if getattr(options, 'githttps', False):
        gitscheme = 'https://github.com/'
    if not os.path.exists(tmpDir):
        os.mkdir(tmpDir)
    for product, reponame in products.items():
        print (f"\nFetching {product}...")
        repoPath = os.path.join(tmpDir, product)
        if os.path.exists(repoPath):
            os.chdir(repoPath)
            sh("git pull")
            sh("git submodule update --init --remote")
        else:
            sh(f"git clone --recursive {gitscheme}geocat/{reponame}.git {repoPath}")
    os.chdir(cwd)

@task
def builddocs():
    '''create html docs from sphinx files'''
    cwd = os.getcwd()
    tmpDir = os.path.join(cwd, 'tmp')    
    for product in products:
        productFolder = os.path.join(tmpDir, product)        
        refs = getrefs(productFolder)
        for refname, ref in refs.items():
            build_product_doc(productFolder, refname, ref)

def getrefs(folder):
    cwd = os.getcwd()
    os.chdir(folder)
    refs = {"latest": "master"}
    try:
        tags = sh("git show-ref --tags", capture=True).splitlines()
        for line in tags:
            ref, tag = line.split(" ")
            refs[tag.replace("refs/tags/", "")] = ref
    except:
        pass # in case no tags exist yet    
    os.chdir(cwd)
    return refs

def build_product_doc(folder, ref, refname):
    '''creates html documentation for a given product and reference,
        and copies it to the 'docs' folder'''
    cwd = os.getcwd()
    tmpDir = os.path.join(cwd, 'tmp')
    os.chdir(folder)
    sh(f"git checkout -f {ref}")
    print (f"Building {folder} ({refname})...")
    sh("paver builddocs -c")
    os.chdir(cwd)
    src = os.path.join(tmpDir, product, 'build', 'html')
    dst = os.path.join(cwd, "docs", product, refname)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


@task
def deploy():
    sh('git add .')
    sh('git commit -am "docs update"')
    sh("git push origin master")
