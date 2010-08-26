#!/usr/bin/python

import os
import sys
import shutil
import subprocess

WORKSPACE = os.environ['WORKSPACE']
PROJECT = os.environ["PROJECT"]  
PROJECT_ROOT = os.environ["PROJECT_ROOT"]

DJANGO_PROJECT_ROOT = os.path.join(PROJECT_ROOT, PROJECT)
VIRTUAL_ENV = os.path.realpath(
    os.path.join(WORKSPACE, "%s-virtualenv" % PROJECT))
VIRTUAL_ENV_PYTHON = os.path.join(VIRTUAL_ENV, "bin", "python")
DJANGO_SETTINGS_MODULE = "%s.settings_hudson" % PROJECT


def new_requirements():
    t1 = os.stat(os.path.join(PROJECT_ROOT, "requirements.pip")).st_mtime
    t2 = os.stat(VIRTUAL_ENV).st_mtime
    return t1 > t2


def setup_virtual_env():
    if not os.path.exists(VIRTUAL_ENV) or new_requirements():
        print "Initializing virtualenv at %s" % VIRTUAL_ENV
        try:
            subprocess.check_call(
                ['virtualenv', '--quiet', '--no-site-packages', VIRTUAL_ENV])

            subprocess.check_call([
                os.path.join(VIRTUAL_ENV, 'bin', 'easy_install'),
                '--quiet', 'pip'])

            subprocess.check_call([
                os.path.join(VIRTUAL_ENV, 'bin', 'pip'),
                '-E', VIRTUAL_ENV,
                'install',
                '--quiet',
                '-r', os.path.join(PROJECT_ROOT, "requirements.pip")])

            # Add the containing directory to the virtualenv so imports work:
            venv_pth = file(
                os.path.join(VIRTUAL_ENV, "lib", "python2.6",
                             "site-packages", "%s.pth" % PROJECT), "w")
            print >> venv_pth, PROJECT_ROOT
            venv_pth.close()

            postactivate = file(
                os.path.join(VIRTUAL_ENV, "bin", "postactivate"), "w")
            cmd = "export DJANGO_SETTINGS_MODULE=%s" % DJANGO_SETTINGS_MODULE
            print >> postactivate, cmd
            cmd = "export PROJECT_ROOT=%s" % DJANGO_PROJECT_ROOT
            print >> postactivate, cmd
            postactivate.close()

        except Exception, e:
            print >> sys.stderr, "ABORTING: Unable to setup virtualenv: %s" % e
            shutil.rmtree(VIRTUAL_ENV, ignore_errors=True)
            sys.exit(2)


def run_tests():
    os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE
    os.chdir(DJANGO_PROJECT_ROOT)

    try:
        subprocess.check_call(
            [os.path.join(VIRTUAL_ENV, "bin", "django-admin.py"),
             "test", "--noinput"])
    except Exception, e:
        print >> sys.stderr, "Tests failed: %s" % e
        sys.exit(2)

if __name__ == '__main__':
    setup_virtual_env()
    run_tests()
    sys.exit(0)
