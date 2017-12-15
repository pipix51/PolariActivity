
import os
import sys
import shutil
import tempfile
import subprocess
from glob import glob
from ConfigParser import ConfigParser
from os.path import join, dirname, abspath, lexists, islink, isdir, exists
from os.path import basename
from gettext import gettext as _


# COMPONENTS = ['Edit', 'Jam', 'Mini', 'SynthLab']

# FULL_COMPONENT_NAMES = [
        # TRANS: Full activity name that will be used in Sugar Shell
        # _('TamTamEdit'),
        # TRANS: Full activity name that will be used in Sugar Shell
        # _('TamTamJam'),
        # TRANS: Full activity name that will be used in Sugar Shell
        # _('TamTamMini'),
        # TRANS: Full activity name that will be used in Sugar Shell
        # _('TamTamSynthLab')]


def link_activities(dst_root, cp_cmd):
    for component in COMPONENTS:
        activity_dir = join(dst_root, 'TamTam%s.activity' % component)

        if lexists(activity_dir):
            if islink(activity_dir):
                os.unlink(activity_dir)
            else:
                shutil.rmtree(activity_dir)
        os.makedirs(join(activity_dir, 'activity'))

        for i in [component, 'incremental', 'twisted', 'zope', 'po',
                'TamTam%s.py' % component,
                join('activity', 'TamTam%s.svg' % component),]:
            if exists(join(src_root, i)):
                cp_cmd(join(src_root, i), join(activity_dir, i))

        info = ConfigParser()
        info.read(join(src_root, 'activity', 'activity.info'))
        info.set('DEFAULT', 'component_id', component.lower())
        info.set('DEFAULT', 'component_name', 'TamTam%s' % component)
        for key, value in info.items('Activity'):
            # Replace % expansions since ASLO doesn't understand them
            info.set('Activity', key, value)
        info_file = file(join(activity_dir, 'activity', 'activity.info'), 'w')
        info.write(info_file)
        info_file.close()
        info.read(join(src_root, 'activity', 'activity.info'))

        setup_file = file(join(activity_dir, 'setup.py'), 'w')
        setup_file.write('#!/usr/bin/env python\n')
        setup_file.write('from sugar.activity import bundlebuilder\n')
        setup_file.write('bundlebuilder.start()\n')
        setup_file.close()
        os.chmod(setup_file.name, 0755)


def walk_activities(*commands):
    dst_root = tempfile.mkdtemp(dir=join(src_root, '..'))
    link_activities(dst_root, link_tree)
    if not exists(join(src_root, 'dist')):
        os.makedirs(join(src_root, 'dist'))

    for component in COMPONENTS:
        for cmd in commands:
            print '-- %s %s activity' % (' '.join(cmd), component)

            activity_dir = join(dst_root, 'TamTam%s.activity' % component)
            subprocess.check_call(['python', 'setup.py'] + cmd,
                    cwd=activity_dir)

            for i in glob(join(activity_dir, 'dist', '*.xo')) + \
                    glob(join(activity_dir, 'dist', '*.tar.*')):
                os.rename(i, join(src_root, 'dist', basename(i)))

    shutil.rmtree(dst_root)


def link_tree(src, dst):
    if abspath(src) == abspath(dst):
        return

    do_copy = []

    def link(src, dst):
        if not exists(dirname(dst)):
            os.makedirs(dirname(dst))
        if do_copy:
            shutil.copy(src, dst)
        else:
            try:
                os.link(src, dst)
            except OSError:
                do_copy.append(True)
                shutil.copy(src, dst)

    if isdir(src):
        for root, __, files in os.walk(src):
            dst_root = join(dst, root[len(src):].lstrip(os.sep))
            if not exists(dst_root):
                os.makedirs(dst_root)
            for i in files:
                link(join(root, i), join(dst_root, i))
    else:
        link(src, dst)


if len(sys.argv) == 1:
    print """\
Available commands:
dev [PATH]           Create symlinked activity directories in PATH
                     (default is "..") to run TamTam activities in development
                     environment from ~/Activities directory
dist_xo              Create xo bundles for all TamTam activities
dist_source          Create a tar source bundles for all TamTam activities
genpot               Generate the gettext pot file
install              Install activities in the system; it is mpstly for
                     packagers to use in package spec files; export DESTDIR
                     environment variable to set destination directory
"""
    exit(0)

src_root = abspath(dirname(__file__))

if sys.argv[1] == 'dev':
    if len(sys.argv) > 2:
        dst_root = sys.argv[2]
    else:
        dst_root = join(src_root, '..')
    link_activities(dst_root, os.symlink)
elif sys.argv[1] in ['dist_source', 'genpot']:
    from sugar.activity import bundlebuilder
    bundlebuilder.start()
elif sys.argv[1] == 'dist_xo':
    walk_activities(['build'], ['dist_xo'])
elif sys.argv[1] == 'install':
    destdir = os.environ.get('DESTDIR', '')
    walk_activities(['build'], ['install', '--prefix=%s/usr' % destdir])
else:
    print 'Unknown command %s' % sys.argv[1]
    exit(1)
